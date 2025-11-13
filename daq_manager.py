import time
import threading
import copy
from data_logger import DataLogger

try:
    from ADC import ADS124S08

    print("--- Main: Running on REAL hardware ---")
except (ImportError, ModuleNotFoundError):
    print("--- Main: (Mock Mode) Hardware not found, importing ADC_testable ---")
    from sims.ADC_testable import ADS124S08

# Note: We don't import Enabled_Inputs here,
# the config is passed in from web_server.py

class DAQManager:
    """
    Manages all DAQ hardware and logging operations.
    This class is designed to be thread-safe.
    """
    
    def __init__(self, data_dir, initial_adc1_config, initial_adc2_config):
        self.data_dir = data_dir
        
        # --- Hardware Config ---
        self.GPIOCHIP = "/dev/gpiochip0"
        self.VREF = 2.5
        self.GAIN = 1
        
        # --- State Variables ---
        self._is_logging = False
        self._logging_thread = None
        self._status_message = "Idle"
        self.logger = None
        self._lock = threading.Lock() # To protect shared state
        
        # --- Channel Configuration ---
        # We hold config in memory, copied from the initial file
        self._adc1_config = copy.deepcopy(initial_adc1_config)
        self._adc2_config = copy.deepcopy(initial_adc2_config)
        
        # --- Hardware Initialization ---
        try:
            self.adc1 = ADS124S08(spi_bus=0, spi_dev=0, gpiochip=self.GPIOCHIP, reset_pin=17, drdy_pin=25, start_pin=27, max_speed_hz=1_000_000)
            self.adc2 = ADS124S08(spi_bus=0, spi_dev=1, gpiochip=self.GPIOCHIP, reset_pin=22, drdy_pin=24, start_pin=26, max_speed_hz=1_000_000)

            self.adc1.hardware_reset()
            self.adc2.hardware_reset()
            self.adc1.configure_basic(use_internal_ref=True, gain=self.GAIN)
            self.adc2.configure_basic(use_internal_ref=True, gain=self.GAIN)
            
            self._status_message = "Idle. ADCs initialized."
        except Exception as e:
            self._status_message = f"CRITICAL: Failed to initialize ADCs: {e}. Server may not function."
            print(self._status_message)
            # In a real app, you might not want to continue,
            # but here we allow the server to run to report the error.
            self.adc1 = None
            self.adc2 = None

    # --- Public Control Methods ---
    
    def start_logging(self):
        """Starts a new logging session in a separate thread."""
        with self._lock:
            if self._is_logging:
                raise RuntimeError("Logging is already in progress.")
            
            if not self.adc1 or not self.adc2:
                raise RuntimeError("ADCs are not initialized. Cannot start logging.")
            
            # Create a new logger for this session
            self.logger = DataLogger(base_dir=self.data_dir)
            
            # --- Dynamically create headers from *current* config ---
            headers = ["timestamp_unix"]
            
            # Get all enabled channel labels for ADC1
            adc1_headers = [f"ADC1_{label}" for label, (_, enabled) in self._adc1_config.items() if enabled]
            # Get all enabled channel labels for ADC2
            adc2_headers = [f"ADC2_{label}" for label, (_, enabled) in self._adc2_config.items() if enabled]
            
            self.logger.write_header(headers + adc1_headers + adc2_headers)
            
            self._is_logging = True
            self._status_message = f"Logging to {self.logger.get_filename()}"
            
            # Start the hardware
            self.adc1.start()
            self.adc2.start()
            
            # Start the logging loop in a new thread
            self._logging_thread = threading.Thread(target=self._logging_loop)
            self._logging_thread.start()
            
            return self.logger.get_filename()

    def _logging_loop(self):
        """The private method that runs in a thread, collecting data."""
        
        # Copy config to be used *for this session*
        # This prevents config from changing mid-run
        local_adc1_config = copy.deepcopy(self._adc1_config)
        local_adc2_config = copy.deepcopy(self._adc2_config)
        
        while self._is_logging: # Loop continues as long as this flag is True
            try:
                csv_timestamp = time.time()
                
                voltages1 = []
                voltages2 = []
                
                for label, (ch_idx, enabled) in local_adc1_config.items():
                    if not enabled:
                        continue
                    try:
                        _, volts1 = self.adc1.read_voltage_single(ch_idx, vref=self.VREF, gain=self.GAIN, settle_discard=True)
                        voltages1.append(volts1)
                    except Exception as e:
                        print(f"Error reading ADC1 {label}: {e}")
                        voltages1.append(None) # Log a gap

                for label, (ch_idx, enabled) in local_adc2_config.items():
                    if not enabled:
                        continue
                    try:
                        _, volts2 = self.adc2.read_voltage_single(ch_idx, vref=self.VREF, gain=self.GAIN, settle_discard=True)
                        voltages2.append(volts2)
                    except Exception as e:
                        print(f"Error reading ADC2 {label}: {e}")
                        voltages2.append(None) # Log a gap
                
                # Log the data
                row_data = [csv_timestamp] + voltages1 + voltages2
                self.logger.log_row(row_data)
                
                time.sleep(0.2) # Same as your original loop

            except Exception as e:
                print(f"Error in logging loop: {e}")
                # Decide if error is fatal
                # For now, just continue
        
        # --- Cleanup after loop finishes ---
        print("Logging loop stopping...")
        try:
            self.adc1.stop()
            self.adc2.stop()
        except Exception as e:
            print(f"Error stopping ADCs: {e}")
            
        if self.logger:
            self.logger.close()
        print(f"File {self.logger.get_filename()} closed.")

    def stop_logging(self):
        """Stops the logging thread and closes the file."""
        filename = None
        with self._lock:
            if not self._is_logging:
                raise RuntimeError("Logging is not in progress.")
            
            if self.logger:
                filename = self.logger.get_filename()
            
            self._is_logging = False # Signal the thread to stop
            self._status_message = "Idle"
        
        if self._logging_thread:
            self._logging_thread.join() # Wait for the thread to finish
            self._logging_thread = None
            
        return filename

    # --- Public Status & Config Methods ---

    def is_logging(self):
        """Thread-safe check if logging is active."""
        with self._lock:
            return self._is_logging

    def get_status_message(self):
        """Thread-safe method to get status."""
        with self._lock:
            return self._status_message

    def get_current_filename(self):
        """Thread-safe method to get current filename."""
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
        """Sets the *in-memory* channel config. Only call when not logging."""
        with self._lock:
            if self._is_logging:
                raise RuntimeError("Cannot change config while logging.")
            self._adc1_config = copy.deepcopy(adc1_config)
            self._adc2_config = copy.deepcopy(adc2_config)
            self._status_message = "Idle. Channel config updated."