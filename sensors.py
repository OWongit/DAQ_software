"""
Sensor classes for converting analog voltage readings to physical values.
"""
import config
from ADC import ADS124S08

class Load_Cell:
    """
    Load cell sensor that reads differential voltage from two analog inputs.
    
    Args:
        sig_plus_idx (int): Voltage list index for positive signal
        sig_minus_idx (int): Voltage list index for negative signal
        excitation_voltage (float): Excitation voltage (default: 5.0)
        sensitivity (float): Sensitivity in mV/V (default: 0.020)
    """
    
    def __init__(self, sig_plus_idx, sig_minus_idx, max_load, excitation_voltage=5.0, sensitivity=0.0020):
        self.sig_plus_idx = sig_plus_idx
        self.sig_minus_idx = sig_minus_idx
        self.excitation_voltage = excitation_voltage
        self.sensitivity = sensitivity
        self.max_load = max_load
    
    def read(self, voltages):
        """
        Read and convert voltage values to force.
        
        Args:
            voltages (list): List of voltage readings from ADC
            
        Returns:
            float: Calculated force value
        """
        if len(voltages) <= max(self.sig_plus_idx, self.sig_minus_idx):
            return 0.0
        
        sig_plus = voltages[self.sig_plus_idx]
        sig_minus = voltages[self.sig_minus_idx]
        
        # Placeholder calculation - to be implemented later
        return self._calculate_force(sig_plus, sig_minus)
    
    def _calculate_force(self, sig_plus, sig_minus):
        """
        Calculate force from differential voltage.
        Placeholder implementation - to be completed later.
        
        Args:
            sig_plus (float): Positive signal voltage
            sig_minus (float): Negative signal voltage
            
        Returns:
            float: Calculated force
        """

        """
        Calculate normalized force ratio.
        """
        # 1. Calculate differential voltage (e.g. 0.008 V)
        v_diff = sig_plus - sig_minus
        
        # 2. Avoid division by zero errors
        if self.excitation_voltage == 0 or self.sensitivity == 0:
            return 0.0
            
        # 3. Calculate current mV/V reading
        # Example: 0.008V / 5.0V = 0.0016 V/V = 1.6 mV/V
        current_mv_per_v = (v_diff / self.excitation_voltage)
        
        # 4. Calculate ratio of Full Scale
        # Example: 1.6 mV/V / 2.0 mV/V (sensitivity) = 0.8 (80% load)
        ratio = current_mv_per_v / self.sensitivity
        
        return ratio * self.max_load


class Pressure_Transducer:
    """
    Pressure transducer sensor that reads voltage from a single analog input.
    
    Args:
        sig_idx (int): Voltage list index for signal input
        excitation_voltage (float): Excitation voltage (default: 5.0)
        V_max (float): Maximum voltage (default: 4.5)
        V_min (float): Minimum voltage (default: 0.5)
        V_span (float): Voltage span (default: 4.0)
        P_min (float): Minimum pressure (default: 0.0)
        P_max (float): Maximum pressure (default: 100.0)
    """
    
    def __init__(self, sig_idx, excitation_voltage=5.0, V_max=4.5, V_min=0.5, 
                 V_span=4.0, P_min=0.0, P_max=100.0):
        self.sig_idx = sig_idx
        self.excitation_voltage = excitation_voltage
        self.V_max = V_max
        self.V_min = V_min
        self.V_span = V_span
        self.P_min = P_min
        self.P_max = P_max
    
    def read(self, voltages):
        """
        Read and convert voltage value to pressure.
        
        Args:
            voltages (list): List of voltage readings from ADC
            
        Returns:
            float: Calculated pressure value
        """
        if len(voltages) <= self.sig_idx:
            return 0.0
        
        sig_voltage = voltages[self.sig_idx]
        
        # Placeholder calculation - to be implemented later
        return self._calculate_pressure(sig_voltage)
    
    def _calculate_pressure(self, sig_voltage):
        """
        Calculate pressure from voltage reading.
        Placeholder implementation - to be completed later.
        
        Args:
            sig_voltage (float): Signal voltage
            
        Returns:
            float: Calculated pressure
        """
        if self.V_span == 0:
            return 0.0
            
        pressure_range = self.P_max - self.P_min
        
        # Linear mapping
        pressure = (sig_voltage - self.V_min) * (pressure_range / self.V_span) + self.P_min
        
        return pressure


class RTD:
    """
    RTD (Resistance Temperature Detector) sensor that reads voltage from two analog inputs.
    
    Args:
        V_leg1_idx (int): Voltage list index for leg 1
        V_leg2_idx (int): Voltage list index for leg 2
    """
    
    def __init__(self, V_leg1_idx, V_leg2_idx):
        self.V_leg1_idx = V_leg1_idx
        self.V_leg2_idx = V_leg2_idx
        #TODO: configure IDAC and reference for RTD using ADC driver
    
    def read(self, voltages):
        """
        Read and convert voltage values to temperature.
        
        Args:
            voltages (list): List of voltage readings from ADC
            
        Returns:
            float: Calculated temperature value
        """
        if len(voltages) <= max(self.V_leg1_idx, self.V_leg2_idx):
            return 0.0
        
        V_leg1 = voltages[self.V_leg1_idx]
        V_leg2 = voltages[self.V_leg2_idx]
        
        # Placeholder calculation - to be implemented later
        return self._calculate_temperature(V_leg1, V_leg2)
    
    def _calculate_temperature(self, V_leg1, V_leg2):
        """
        Calculate temperature from leg voltages.
        Placeholder implementation - to be completed later.
        
        Args:
            V_leg1 (float): Voltage at leg 1
            V_leg2 (float): Voltage at leg 2
            
        Returns:
            float: Calculated temperature
        """
        # TODO: Implement temperature calculation
        return 0.0

def initialize_sensors():
    sensor_labels = []
    load_cells = []
    for name, cfg in config.LOAD_CELLS.items():
        if cfg['enabled']:
            print(f"Initializing Load Cell {name} with sig_plus_idx {cfg['sig_plus_idx']} and sig_minus_idx {cfg['sig_minus_idx']}")
            sensor = Load_Cell(
                sig_plus_idx=cfg['sig_plus_idx'],
                sig_minus_idx=cfg['sig_minus_idx'],
                max_load=cfg['max_load'],
                excitation_voltage=cfg['excitation_voltage'],
                sensitivity=cfg['sensitivity']
            )
            load_cells.append((name, sensor))
            sensor_labels.append(f"{name} Force")

    pressure_transducers = []
    for name, cfg in config.PRESSURE_TRANSDUCERS.items():
        if cfg['enabled']:
            print(f"Initializing Pressure Transducer {name} with sig_idx {cfg['sig_idx']}")
            sensor = Pressure_Transducer(
                sig_idx=cfg['sig_idx'],
                excitation_voltage=cfg['excitation_voltage'],
                V_max=cfg['V_max'],
                V_min=cfg['V_min'],
                V_span=cfg['V_span'],
                P_min=cfg['P_min'],
                P_max=cfg['P_max']
            )
            pressure_transducers.append((name, sensor))
            sensor_labels.append(f"{name} Pressure")

    rtds = []
    for name, cfg in config.RTDS.items():
        if cfg['enabled']:
            print(f"Initializing RTD {name} with V_leg1_idx {cfg['V_leg1_idx']} and V_leg2_idx {cfg['V_leg2_idx']}")

            sensor = RTD(
                V_leg1_idx=cfg['V_leg1_idx'],
                V_leg2_idx=cfg['V_leg2_idx']
            )
            rtds.append((name, sensor))
            sensor_labels.append(f"{name} Temp")

    return sensor_labels, load_cells, pressure_transducers, rtds

def read_sensors(voltages, load_cells, pressure_transducers, rtds):
    sensor_values = []
    for name, sensor in load_cells:
        force = sensor.read(voltages)
        sensor_values.append(force)
    for name, sensor in pressure_transducers:
        pressure = sensor.read(voltages)
        sensor_values.append(pressure)
    for name, sensor in rtds:
        temperature = sensor.read(voltages)
        sensor_values.append(temperature)
    return sensor_values