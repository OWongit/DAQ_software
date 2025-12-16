"""
Sensor classes for converting analog voltage readings to physical values.
"""

import config


class Load_Cell:
    """
    Load cell sensor that reads differential voltage from two analog inputs.

    Args:
        sig_plus_idx (int): Voltage list index for positive signal
        sig_minus_idx (int): Voltage list index for negative signal
        excitation_voltage (float): Excitation voltage (default: 5.0)
        sensitivity (float): Sensitivity in mV/V (default: 0.020)
    """

    def __init__(self, ADC, sig_plus_idx, sig_minus_idx, max_load, excitation_voltage=5.0, sensitivity=0.0020):
        self.ADC = ADC
        self.sig_plus_idx = sig_plus_idx
        self.sig_minus_idx = sig_minus_idx
        self.excitation_voltage = excitation_voltage
        self.sensitivity = sensitivity
        self.max_load = max_load

    def read(self):
        sig_plus = self.ADC.read_voltage_single(self.sig_plus_idx)
        sig_minus = self.ADC.read_voltage_single(self.sig_minus_idx)

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
        current_mv_per_v = v_diff / self.excitation_voltage

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

    def __init__(self, ADC, sig_idx, excitation_voltage=5.0, V_max=4.5, V_min=0.5, V_span=4.0, P_min=0.0, P_max=100.0):
        self.ADC = ADC
        self.sig_idx = sig_idx
        self.excitation_voltage = excitation_voltage
        self.V_max = V_max
        self.V_min = V_min
        self.V_span = V_span
        self.P_min = P_min
        self.P_max = P_max

    def read(self):
        sig_voltage = self.ADC.read_voltage_single(self.sig_idx)

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
        V_lead1_idx (int): Voltage list index for lead 1
        V_lead2_idx (int): Voltage list index for lead 2
    """

    def __init__(self, ADC, V_lead1_idx, V_lead2_idx):
        self.ADC = ADC
        self.V_lead1_idx = V_lead1_idx
        self.V_lead2_idx = V_lead2_idx
        # self.adc = adc
        # self.adc.enable_rtd_mode()
        # TODO: configure IDAC and reference for RTD using ADC driver'
        # TODO: CANNOT USE MULTIPLE ADC REFERENCES. IF USING AN RTD, EVERY OTHER INPUT CHANNEL WILL USE THE SAME RTD REFERENCE.
        # TODO: PERHAPS CAN TIME MULTIPLEX THE RTD REFERENCE/MAIN REFERENCE SO WE CAN READ RTDs AT THE SAME TIME AS OTHER SENSORS?

    def read(self):
        V_lead1 = self.ADC.read_voltage_single(self.V_lead1_idx)
        V_lead2 = self.ADC.read_voltage_single(self.V_lead2_idx)

        # Placeholder calculation - to be implemented later
        return self._calculate_temperature(V_lead1, V_lead2)

    def _calculate_temperature(self, V_lead1, V_lead2):
        """
        Calculate temperature from lead voltages.
        Placeholder implementation - to be completed later.

        Args:
            V_lead1 (float): Voltage at lead 1
            V_lead2 (float): Voltage at lead 2

        Returns:
            float: Calculated temperature
        """
        # TODO: Implement temperature calculation
        return 0.0


def initialize_sensors(adc1, adc2):
    sensor_labels = []
    load_cells = []
    for name, cfg in config.LOAD_CELLS.items():
        if cfg["enabled"]:
            print(f"Initializing Load Cell {name} with sig_plus_idx {cfg['sig_plus_idx']} and sig_minus_idx {cfg['sig_minus_idx']}")
            if cfg["ADC"] == 1:
                selected_adc = adc1
            elif cfg["ADC"] == 2:
                selected_adc = adc2
            else:
                raise ValueError(f"Invalid ADC configuration: {cfg['ADC']}")

            sensor = Load_Cell(
                ADC=selected_adc,
                sig_plus_idx=cfg["sig_plus_idx"],
                sig_minus_idx=cfg["sig_minus_idx"],
                max_load=cfg["max_load"],
                excitation_voltage=cfg["excitation_voltage"],
                sensitivity=cfg["sensitivity"],
            )
            load_cells.append((name, sensor))
            sensor_labels.append(name)

    pressure_transducers = []
    for name, cfg in config.PRESSURE_TRANSDUCERS.items():
        if cfg["enabled"]:
            print(f"Initializing Pressure Transducer {name} with sig_idx {cfg['sig_idx']}")
            if cfg["ADC"] == 1:
                selected_adc = adc1
            elif cfg["ADC"] == 2:
                selected_adc = adc2
            else:
                raise ValueError(f"Invalid ADC configuration: {cfg['ADC']}")

            sensor = Pressure_Transducer(
                ADC=selected_adc,
                sig_idx=cfg["sig_idx"],
                excitation_voltage=cfg["excitation_voltage"],
                V_max=cfg["V_max"],
                V_min=cfg["V_min"],
                V_span=cfg["V_span"],
                P_min=cfg["P_min"],
                P_max=cfg["P_max"],
            )
            pressure_transducers.append((name, sensor))
            sensor_labels.append(name)

    rtds = []
    for name, cfg in config.RTDS.items():
        if cfg["enabled"]:
            print(f"Initializing RTD {name} with V_lead1_idx {cfg['V_lead1_idx']} and V_lead2_idx {cfg['V_lead2_idx']}")
            if cfg["ADC"] == 1:
                selected_adc = adc1
            elif cfg["ADC"] == 2:
                selected_adc = adc2
            else:
                raise ValueError(f"Invalid ADC configuration: {cfg['ADC']}")

            sensor = RTD(
                ADC=selected_adc,
                V_lead1_idx=cfg["V_lead1_idx"],
                V_lead2_idx=cfg["V_lead2_idx"],
                #   adc=adc
            )
            rtds.append((name, sensor))
            sensor_labels.append(name)

    return sensor_labels, load_cells, pressure_transducers, rtds


def read_sensors(load_cells, pressure_transducers, rtds):
    sensor_values = []
    for _, sensor in load_cells:
        force = sensor.read()
        sensor_values.append(force)
    for _, sensor in pressure_transducers:
        pressure = sensor.read()
        sensor_values.append(pressure)
    for _, sensor in rtds:
        temperature = sensor.read()
        sensor_values.append(temperature)
    return sensor_values
