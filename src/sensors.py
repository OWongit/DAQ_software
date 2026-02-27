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

    def __init__(self, ADC, sig_plus_idx, sig_minus_idx, max_load, excitation_voltage=5.0, sensitivity=0.0020, offset=0.0):
        self.ADC = ADC
        self.sig_plus_idx = sig_plus_idx
        self.sig_minus_idx = sig_minus_idx
        self.excitation_voltage = excitation_voltage
        self.sensitivity = sensitivity
        self.max_load = max_load
        self.offset = float(offset)

    def read(self):
        sig_plus = self.ADC.read_voltage_single(self.sig_plus_idx, settle_discard=config.ADC_SETTLE_DISCARD)
        sig_minus = self.ADC.read_voltage_single(self.sig_minus_idx, settle_discard=config.ADC_SETTLE_DISCARD)

        # Placeholder calculation - to be implemented later
        return sig_plus, sig_minus, self._calculate_force(sig_plus, sig_minus)

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

        return (ratio * self.max_load) - self.offset


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

    def __init__(self, ADC, sig_idx, excitation_voltage=5.0, V_max=4.5, V_min=0.5, V_span=4.0, P_min=0.0, P_max=100.0, offset=0.0):
        self.ADC = ADC
        self.sig_idx = sig_idx
        self.excitation_voltage = excitation_voltage
        self.V_max = V_max
        self.V_min = V_min
        self.V_span = V_span
        self.P_min = P_min
        self.P_max = P_max
        self.offset = float(offset)

    def read(self):
        sig_voltage = self.ADC.read_voltage_single(self.sig_idx, settle_discard=config.ADC_SETTLE_DISCARD)

        # Placeholder calculation - to be implemented later
        return sig_voltage, self._calculate_pressure(sig_voltage)

    def _calculate_pressure(self, sig_voltage):
        """
        Calculate pressure from voltage reading.
        Placeholder implementation - to be completed later.

        Args:
            sig_voltage (float): Signal voltage

        Returns:
            float: Calculated pressure
        """

        # Clamp to valid sensor range
        sig_voltage = max(self.V_min, min(sig_voltage, self.V_max))

        if self.V_span == 0:
            return 0.0

        pressure_range = self.P_max - self.P_min

        # Linear mapping
        pressure = (sig_voltage - self.V_min) * (pressure_range / self.V_span) + self.P_min

        return pressure - self.offset


class RTD:
    """
    RTD (Resistance Temperature Detector) sensor that reads voltage from two analog inputs.

    Args:
        V_lead1_idx (int): Voltage list index for lead 1
        V_lead2_idx (int): Voltage list index for lead 2
    """

    def __init__(self, ADC, V_lead1_idx, V_lead2_idx, offset=0.0):
        self.ADC = ADC
        self.V_lead1_idx = V_lead1_idx
        self.V_lead2_idx = V_lead2_idx
        self.offset = float(offset)
        # TODO: configure IDAC and reference for RTD using ADC driver'
        # TODO: CANNOT USE MULTIPLE ADC REFERENCES. IF USING AN RTD, EVERY OTHER INPUT CHANNEL WILL USE THE SAME RTD REFERENCE.
        # TODO: PERHAPS CAN TIME MULTIPLEX THE RTD REFERENCE/MAIN REFERENCE SO WE CAN READ RTDs AT THE SAME TIME AS OTHER SENSORS?

    def read(self):
        # self.ADC.enable_rtd_mode() DO NOT USE UNLESS CONNECTED TO AN RTD SENSOR
        V_lead1 = self.ADC.read_voltage_single(self.V_lead1_idx, settle_discard=config.ADC_SETTLE_DISCARD)
        V_lead2 = self.ADC.read_voltage_single(self.V_lead2_idx, settle_discard=config.ADC_SETTLE_DISCARD)
        # self.ADC.disable_rtd_mode() DO NOT USE UNLESS CONNECTED TO AN RTD SENSOR
        # Placeholder calculation - to be implemented later
        return V_lead1, V_lead2, self._calculate_temperature(V_lead1, V_lead2)

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
        return 0.0 - self.offset


def _adc_for_cfg(cfg, adc1, adc2):
    """Return the ADC instance (adc1 or adc2) for the given config's ADC index."""
    if cfg["ADC"] == 1:
        return adc1
    if cfg["ADC"] == 2:
        return adc2
    raise ValueError(f"Invalid ADC configuration: {cfg['ADC']}")


def initialize_sensors(adc1, adc2):
    sensor_labels = []
    load_cells = []
    for name, cfg in config.LOAD_CELLS.items():
        if cfg["enabled"]:
            print(f"Initializing Load Cell {name} with sig_plus_idx {cfg['SIG+']} and sig_minus_idx {cfg['SIG-']}")
            selected_adc = _adc_for_cfg(cfg, adc1, adc2)
            sensor = Load_Cell(
                ADC=selected_adc,
                sig_plus_idx=cfg["SIG+"],
                sig_minus_idx=cfg["SIG-"],
                max_load=cfg["max_load"],
                excitation_voltage=cfg["excitation_voltage"],
                sensitivity=cfg["sensitivity"],
                offset=float(cfg.get("offset", 0)),
            )
            load_cells.append((name, sensor))
            sensor_labels.append(name)

    pressure_transducers = []
    for name, cfg in config.PRESSURE_TRANSDUCERS.items():
        if cfg["enabled"]:
            print(f"Initializing Pressure Transducer {name} with sig_idx {cfg['SIG']}")
            selected_adc = _adc_for_cfg(cfg, adc1, adc2)
            sensor = Pressure_Transducer(
                ADC=selected_adc,
                sig_idx=cfg["SIG"],
                excitation_voltage=cfg["excitation_voltage"],
                V_max=cfg["V_max"],
                V_min=cfg["V_min"],
                V_span=cfg["V_span"],
                P_min=cfg["P_min"],
                P_max=cfg["P_max"],
                offset=float(cfg.get("offset", 0)),
            )
            pressure_transducers.append((name, sensor))
            sensor_labels.append(name)

    rtds = []
    for name, cfg in config.RTDS.items():
        if cfg["enabled"]:
            print(f"Initializing RTD {name} with V_lead1_idx {cfg['L1']} and V_lead2_idx {cfg['L2']}")
            selected_adc = _adc_for_cfg(cfg, adc1, adc2)
            sensor = RTD(
                ADC=selected_adc,
                V_lead1_idx=cfg["L1"],
                V_lead2_idx=cfg["L2"],
                offset=float(cfg.get("offset", 0)),
            )
            rtds.append((name, sensor))
            sensor_labels.append(name)

    return sensor_labels, load_cells, pressure_transducers, rtds


def read_sensors(load_cells, pressure_transducers, rtds):
    sensor_values = []
    voltages = []
    for _, sensor in load_cells:
        v_sig_plus, v_sig_minus, force = sensor.read()
        voltages.append(v_sig_plus)
        voltages.append(v_sig_minus)
        sensor_values.append(force)
    for _, sensor in pressure_transducers:
        v_p_sig, pressure = sensor.read()
        voltages.append(v_p_sig)
        sensor_values.append(pressure)
    for _, sensor in rtds:
        v_lead1, v_lead2, temperature = sensor.read()
        voltages.append(v_lead1)
        voltages.append(v_lead2)
        sensor_values.append(temperature)
    return voltages, sensor_values
