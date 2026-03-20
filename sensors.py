"""
Sensor classes for converting analog voltage readings to physical values.
"""

import math
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
        v_diff = abs(sig_plus - sig_minus)

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

        # Linear mapping
        pressure = (sig_voltage - self.V_min) * ((self.P_max - self.P_min) / self.V_span) + self.P_min

        return pressure - self.offset


class RTD:
    """
    3-wire RTD sensor using software-ratiometric measurement with IDAC excitation.

    Enables RTD mode (switches ADC to internal 2.5 V reference, turns on
    IDACs), reads both the RTD voltage (L1-L2) and the Rref voltage
    (REFP-REFN) differentially, then takes their ratio so that both IDAC
    current and internal reference voltage cancel.  Finally restores the
    ADC to its normal state so other sensors are unaffected.

    Temperature is computed via the Callendar-Van Dusen equation (IEC 60751).
    """

    # Callendar-Van Dusen coefficients (IEC 60751)
    _CVD_A = 3.9083e-3
    _CVD_B = -5.775e-7
    _CVD_C = -4.183e-12  # only used for T < 0 °C

    def __init__(self, ADC, V_lead1_idx, V_lead2_idx,
                 refp_ain=7, refn_ain=6,
                 r0=1000.0, rref=5600.0,
                 idac_current_ua=50, idac1_ain=5, idac2_ain=3,
                 unit="°C", offset=0.0):
        self.ADC = ADC
        self.V_lead1_idx = V_lead1_idx
        self.V_lead2_idx = V_lead2_idx
        self.refp_ain = refp_ain
        self.refn_ain = refn_ain
        self.r0 = float(r0)
        self.rref = float(rref)
        self.idac_current_ua = idac_current_ua
        self.idac1_ain = idac1_ain
        self.idac2_ain = idac2_ain
        self.unit = unit
        self.offset = float(offset)

    _VREF_INTERNAL = 2.5
    _FS = (1 << 23) - 1  # 8 388 607

    def read(self):
        """
        Enable RTD excitation, read L1 and L2 single-ended voltages plus
        the differential code across the RTD, disable RTD excitation, then
        compute resistance and temperature.

        Resistance is computed as R = V_RTD / I_IDAC.  The IDAC current only
        flows through the RTD (not through Rref), so a software-ratiometric
        approach using Rref would give the wrong answer for this circuit
        topology where the Rbias chain contributes extra current through Rref.

        Returns:
            (v_lead1, v_lead2, resistance, temperature)
        """
        self.ADC.enable_rtd_mode(
            current_ua=self.idac_current_ua,
            idac1_ain=self.idac1_ain,
            idac2_ain=self.idac2_ain,
        )
        try:
            v_lead1 = self.ADC.read_voltage_single(
                self.V_lead1_idx, vref=2.5, settle_discard=config.ADC_SETTLE_DISCARD,
            )
            v_lead2 = self.ADC.read_voltage_single(
                self.V_lead2_idx, vref=2.5, settle_discard=config.ADC_SETTLE_DISCARD,
            )
            code_rtd = self.ADC.read_raw_diff(
                self.V_lead1_idx,
                self.V_lead2_idx,
                settle_discard=config.ADC_SETTLE_DISCARD,
            )
        finally:
            self.ADC.disable_rtd_mode()

        resistance = self._code_to_resistance(code_rtd)
        temp_c = self._resistance_to_temperature(resistance)
        temperature = self._convert_unit(temp_c) - self.offset
        return v_lead1, v_lead2, resistance, temperature

    def _code_to_resistance(self, code_rtd):
        """R = V_RTD / I_IDAC, where V_RTD is derived from the raw ADC code."""
        v_rtd = (code_rtd / self._FS) * self._VREF_INTERNAL
        i_idac = self.idac_current_ua * 1e-6
        if i_idac == 0:
            return 0.0
        return v_rtd / i_idac

    def _resistance_to_temperature(self, resistance):
        """Invert the Callendar-Van Dusen equation to get temperature in °C."""
        r_ratio = resistance / self.r0

        # Quadratic inverse for T >= 0 °C:
        #   R/R0 = 1 + A*T + B*T^2  =>  B*T^2 + A*T + (1 - R/R0) = 0
        discriminant = self._CVD_A ** 2 - 4 * self._CVD_B * (1 - r_ratio)
        if discriminant < 0:
            return 0.0
        temp_c = (-self._CVD_A + math.sqrt(discriminant)) / (2 * self._CVD_B)

        if temp_c < 0:
            temp_c = self._newton_cvd_negative(resistance, temp_c)

        return temp_c

    def _newton_cvd_negative(self, resistance, initial_guess, iterations=10):
        """Newton-Raphson refinement for T < 0 °C (full CVD with C term)."""
        A, B, C, R0 = self._CVD_A, self._CVD_B, self._CVD_C, self.r0
        t = initial_guess
        for _ in range(iterations):
            r_calc = R0 * (1 + A * t + B * t**2 + C * (t - 100) * t**3)
            dr_dt = R0 * (A + 2 * B * t + C * (4 * t**3 - 300 * t**2))
            if abs(dr_dt) < 1e-15:
                break
            t -= (r_calc - resistance) / dr_dt
        return t

    def _convert_unit(self, temp_c):
        """Convert from °C to the configured display unit."""
        if self.unit == "°F":
            return temp_c * 9.0 / 5.0 + 32.0
        if self.unit == "K":
            return temp_c + 273.15
        return temp_c


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
            print(f"Initializing RTD {name} on ADC{cfg['ADC']} "
                  f"L1=AIN{cfg['L1']} L2=AIN{cfg['L2']} "
                  f"IDAC={cfg.get('idac_current_ua', 50)}µA "
                  f"R0={cfg.get('r0', 1000)}Ω Rref={cfg.get('rref', 5600)}Ω")
            selected_adc = _adc_for_cfg(cfg, adc1, adc2)
            sensor = RTD(
                ADC=selected_adc,
                V_lead1_idx=cfg["L1"],
                V_lead2_idx=cfg["L2"],
                refp_ain=cfg.get("refp_ain", 7),
                refn_ain=cfg.get("refn_ain", 6),
                r0=cfg.get("r0", 1000.0),
                rref=cfg.get("rref", 5600.0),
                idac_current_ua=cfg.get("idac_current_ua", 50),
                idac1_ain=cfg.get("idac1_ain", 5),
                idac2_ain=cfg.get("idac2_ain", 3),
                unit=cfg.get("unit", "°C"),
                offset=float(cfg.get("offset", 0)),
            )
            rtds.append((name, sensor))
            sensor_labels.append(name)

    return sensor_labels, load_cells, pressure_transducers, rtds


def read_sensors(load_cells, pressure_transducers, rtds):
    sensor_values = []
    csv_columns = []
    for _, sensor in load_cells:
        v_sig_plus, v_sig_minus, force = sensor.read()
        csv_columns.extend([v_sig_plus, v_sig_minus, force])
        sensor_values.append(force)
    for _, sensor in pressure_transducers:
        v_p_sig, pressure = sensor.read()
        csv_columns.extend([v_p_sig, pressure])
        sensor_values.append(pressure)
    for _, sensor in rtds:
        v_lead1, v_lead2, resistance, temperature = sensor.read()
        csv_columns.extend([v_lead1, v_lead2, temperature])
        sensor_values.append(temperature)
    return csv_columns, sensor_values
