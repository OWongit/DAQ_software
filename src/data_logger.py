import csv
import os
import datetime
from . import config


class DataLogger:
    """
    A simple CSV logger class.
    Creates a new, timestamped CSV file in a specified directory
    and handles writing headers and data rows.
    """

    def get_daq_header(self):
        """
        Parses config.py and returns a list of column headers
        for all enabled sensors.
        """
        header = []

        # 1. Load Cells
        for name, params in getattr(config, "LOAD_CELLS", {}).items():
            if params.get("enabled"):
                header.extend([f"{name}_SIG+", f"{name}_SIG-"])

        # 2. Pressure Transducers
        for name, params in getattr(config, "PRESSURE_TRANSDUCERS", {}).items():
            if params.get("enabled"):
                header.append(f"{name}_SIG")

        # 3. RTDs
        for name, params in getattr(config, "RTDS", {}).items():
            if params.get("enabled"):
                header.extend([f"{name}_L1", f"{name}_L2"])

        return header

    def __init__(self, base_dir="data"):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.filename = os.path.join(self.base_dir, f"DATA-{timestamp}.csv")

        print(f"DataLogger: Opening file {self.filename}")

        self.file_handle = open(self.filename, "w", newline="", encoding="utf-8")
        self.writer = csv.writer(self.file_handle)

        self.HEADER = ["Timestamp"] + self.get_daq_header()

        try:
            self.writer.writerow(self.HEADER)
            self.file_handle.flush()
        except Exception as e:
            print(f"DataLogger: Error writing header: {e}")

    def log_row(self, row_data):
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
        return os.path.basename(self.filename)
