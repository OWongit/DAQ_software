import csv
import os
import datetime
import config


class DataLogger:
    """
    A simple CSV logger class.
    Creates a new, timestamped CSV file in a specified directory
    and handles writing headers and data rows.
    """

    def get_daq_header(self):
        """
        Parses config.py and returns a list of column headers
        for all enabled sensors, including computed values with units.
        """
        header = []

        for name, params in getattr(config, "LOAD_CELLS", {}).items():
            if params.get("enabled"):
                unit = params.get("unit", "N")
                header.extend([f"{name}_SIG+", f"{name}_SIG-", f"{name}_Force({unit})"])

        for name, params in getattr(config, "PRESSURE_TRANSDUCERS", {}).items():
            if params.get("enabled"):
                unit = params.get("unit", "psi")
                header.extend([f"{name}_SIG", f"{name}_Pressure({unit})"])

        for name, params in getattr(config, "RTDS", {}).items():
            if params.get("enabled"):
                header.extend([f"{name}_L1", f"{name}_L2", f"{name}_Temp(C)"])

        return header

    def __init__(self, base_dir="data"):
        self.base_dir = os.path.abspath(base_dir)
        self.file_handle = None
        self.writer = None
        self.filename = None
        self.enabled = False

        sensor_header = self.get_daq_header()
        if not sensor_header:
            print("DataLogger: No sensors enabled — CSV logging disabled")
            return

        os.makedirs(self.base_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.filename = os.path.join(self.base_dir, f"DATA-{timestamp}.csv")

        print(f"DataLogger: Opening file {self.filename}")

        self.file_handle = open(self.filename, "w", newline="", encoding="utf-8")
        self.writer = csv.writer(self.file_handle)
        self.enabled = True

        self.HEADER = ["Timestamp"] + sensor_header

        try:
            self.writer.writerow(self.HEADER)
            self.file_handle.flush()
        except Exception as e:
            print(f"DataLogger: Error writing header: {e}")

    def log_row(self, row_data):
        if not self.enabled:
            return
        try:
            self.writer.writerow(row_data)
        except Exception as e:
            print(f"DataLogger: Error logging row: {e}")

    def close(self):
        try:
            if self.file_handle:
                print(f"DataLogger: Closing file {self.filename}")
                self.file_handle.close()
        except Exception as e:
            print(f"DataLogger: Error closing file: {e}")

    def get_filename(self):
        if self.filename is None:
            return None
        return os.path.basename(self.filename)
