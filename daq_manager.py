import time
import threading
import copy
from data_logger import DataLogger

try:
    from ADC import ADS124S08
    print("--- DAQManager: Running on REAL hardware ---")
except (ImportError, ModuleNotFoundError):
    print("--- DAQManager: (Mock Mode) Hardware not found ---")
    from sims.ADC_testable import ADS124S08


class DAQManager:
    """
    Manages all DAQ hardware, monitoring, and logging operations.
    This class is designed to be thread-safe.
    """
    
    def __init__(self, data_dir, initial_adc1_config, initial_adc2_config):
        self.data_dir = data_dir
        
        # --- Hardware Config ---
        self.GPIOCHIP = "/dev/gpiochip0"
        self.VREF = 2.5
        self.GAIN = 1
        self.MONITOR_INTERVAL = 0.2 # Read hardware every 200ms
        
        # --- State Variables ---
        self._is_logging = False
        self._is_monitoring = False
        self._monitor_thread = None
        self._status_message = "Idle"
        self.logger = None
        self._lock = threading.Lock() # To protect shared state
        
        # --- Channel Configuration ---
        self._adc1_config = copy.deepcopy(initial_adc1_config)
        self._adc2_config = copy.deepcopy(initial_adc2_config)
        # We must build the list of *enabled* channels for the loop
        self.enabled_channels = self._build_enabled_channel_list()
        
        # --- FIX: Initialize _latest_data to prevent crashes on startup ---
        self._latest_data = {
            "timestamp": time.time(),
            "voltages": {}
        }
        
        # --- Hardware Initialization ---
        try:
            self.adc1 = ADS124S08(spi_bus=0, spi_dev=0, gpiochip=self.GPIOCHIP, reset_pin=17, drdy_pin=25, start_pin=27, max_speed_hz=1_000_000)
            self.adc2 = ADS124S08(spi_bus=0, spi_dev=1, gpiochip=self.GPIOCHIP, reset_pin=22, drdy_pin=24, start_pin=26, max_speed_hz=1_000_000)

            self.adc1.hardware_reset()
            self.adc2.hardware_reset()
            self.adc1.configure_basic(use_internal_ref=True, gain=self.GAIN)
            self.adc2.configure_basic(use_internal_ref=True, gain=self.GAIN)
            
            self._status_message = "Idle. ADCs initialized."
            
            # --- Auto-start monitoring ---
            self.start_monitoring()
            
        except Exception as e:
            self._status_message = f"CRITICAL: Failed to initialize ADCs: {e}. Server may not function."
            print(self._status_message)
            self.adc1 = None
            self.adc2 = None

    def _build_enabled_channel_list(self):
        """Helper to create the list of channels to read in the monitor loop."""
        channels = []
        for label, (ch_idx, enabled) in self._adc1_config.items():
            if enabled:
                channels.append(('adc1', f"ADC1_{label}", ch_idx))
        for label, (ch_idx, enabled) in self._adc2_config.items():
            if enabled:
                channels.append(('adc2', f"ADC2_{label}", ch_idx))
        return channels

    # --- Public Control Methods ---
    
    def start_monitoring(self):
        """Starts the continuous hardware monitoring loop in a thread."""
        with self._lock:
            if self._is_monitoring:
                return # Already running
            
            if not self.adc1 or not self.adc2:
                print("Cannot start monitoring, ADCs not initialized.")
                return

            print("DAQManager: Starting hardware monitoring loop...")
            self._is_monitoring = True
            
            # Start the hardware
            self.adc1.start()
            self.adc2.start()
            
            # Start the monitoring loop in a new thread
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()

    def _monitor_loop(self):
        """The private method that runs in a thread, continuously reading data."""
        
        # Use the pre-built list of enabled channels
        local_channel_list = self.enabled_channels
        
        if not local_channel_list:
            print("MONITOR LOOP: No channels enabled. Stopping.")
            self._is_monitoring = False
            return
            
        while self._is_monitoring:
            try:
                csv_timestamp = time.time()
                current_readings = {} # Holds {'ADC1_AIN10': 1.23, ...}
                
                # --- Read all enabled channels ---
                for adc_id, full_label, ch_idx in local_channel_list:
                    try:
                        adc = self.adc1 if adc_id == 'adc1' else self.adc2
                        _, volts = adc.read_voltage_single(ch_idx, vref=self.VREF, gain=self.GAIN, settle_discard=True)
                        current_readings[full_label] = volts
                    except Exception as e:
                        print(f"Error reading {full_label}: {e}")
                        current_readings[full_label] = None # Log a gap
                
                # --- If logging, write to CSV ---
                if self._is_logging:
                    # Construct row in the *exact* order of enabled_channels
                    # This matches the header
                    row_data = [csv_timestamp] + [current_readings[label] for _, label, _ in local_channel_list]
                    if self.logger:
                        self.logger.log_row(row_data)
                
                # --- FIX: Update shared data for the API in the correct format ---
                with self._lock:
                    self._latest_data = {
                        "timestamp": csv_timestamp,
                        "voltages": current_readings
                    }
                
                time.sleep(self.MONITOR_INTERVAL)

            except Exception as e:
                print(f"Error in monitor loop: {e}")
                time.sleep(1) # Don't spam errors
        
        # --- Cleanup after loop finishes ---
        print("DAQManager: Monitoring loop stopping...")
        try:
            if self.adc1: self.adc1.stop()
            if self.adc2: self.adc2.stop()
        except Exception as e:
            print(f"Error stopping ADCs: {e}")
            
        # If logging was active, close the file
        if self._is_logging:
            self.stop_logging()

    def start_logging(self):
        """Starts a new logging session."""
        with self._lock:
            if self._is_logging:
                raise RuntimeError("Logging is already in progress.")
            
            if not self._is_monitoring:
                raise RuntimeError("Monitoring is not active. Cannot start logging.")
            
            # Create a new logger for this session
            self.logger = DataLogger(base_dir=self.data_dir)
            
            # --- Dynamically create headers from *current* config ---
            headers = ["timestamp_unix"] + [label for _, label, _ in self.enabled_channels]
            self.logger.write_header(headers)
            
            self._is_logging = True
            self._status_message = f"Logging to {self.logger.get_filename()}"
            
            return self.logger.get_filename()

    def stop_logging(self):
        """Stops the logging and closes the file."""
        filename = None
        with self._lock:
            if not self._is_logging:
                return # Not logging, nothing to do
            
            if self.logger:
                filename = self.logger.get_filename()
                self.logger.close()
                self.logger = None
            
            self._is_logging = False
            self._status_message = "Idle. Monitoring."
            
        print(f"File {filename} closed.")
        return filename

    # --- Public Status & Config Methods ---

    def get_latest_data(self):
        """Thread-safe method to get the latest data block."""
        with self._lock:
            return self._latest_data

    def is_logging(self):
        """Thread-safe check if logging is active."""
        with self._lock:
            return self._is_logging

    def get_status_message(self):
        """Thread-safe method to get status."""
        with self._lock:
            return self._status_message

    def get_current_filename(self):
        """Thread-safe method to get current logging filename."""
        with self._lock:
            if self.logger and self._is_logging:
                return self.logger.get_filename()
            return None

    def get_channel_config(self):
        """Returns the current *in-memory* channel config."""
        with self._lock:
            return {
                'adc1': self._adc1_config,
                'adc2': self._adc2_config
            }

    def set_channel_config(self, adc1_config, adc2_config):
        """
        Sets the *in-memory* channel config. 
        This is a complex operation and should only be done
        when monitoring is stopped.
        """
        with self._lock:
            if self._is_monitoring:
                raise RuntimeError("Cannot change config while monitoring.")
            self._adc1_config = copy.deepcopy(adc1_config)
            self._adc2_config = copy.deepcopy(adc2_config)
            # Re-build the channel list for the next monitor run
            self.enabled_channels = self._build_enabled_channel_list()
            self._status_message = "Idle. Channel config updated."