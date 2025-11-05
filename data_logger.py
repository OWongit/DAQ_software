import csv
import os
import datetime

class DataLogger:
    """
    A simple CSV logger class.
    
    Creates a new, timestamped CSV file in a specified directory
    and handles writing headers and data rows.
    """
    
    def __init__(self, base_dir="data"):
        """
        Initializes the logger.
        - Creates the base_dir if it doesn't exist.
        - Creates a unique, timestamped filename.
        - Opens the file and creates a csv.writer object.
        """
        # Create the full directory path (e.g., /home/pi/my_project/data)
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Generate a unique, timestamped filename
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.filename = os.path.join(self.base_dir, f"DATA-{timestamp}.csv")
        
        print(f"DataLogger: Opening file {self.filename}")
        
        # Open the file in 'write' mode ('w')
        self.file_handle = open(self.filename, 'w', newline='', encoding='utf-8')
        self.writer = csv.writer(self.file_handle)
    
    def write_header(self, headers):
        """Writes a list of strings as the header row."""
        try:
            self.writer.writerow(headers)
            self.file_handle.flush() # Ensure it's written immediately
        except Exception as e:
            print(f"DataLogger: Error writing header: {e}")
            
    def log_row(self, row_data):
        """Writes a list of data as a new row."""
        try:
            self.writer.writerow(row_data)
        except Exception as e:
            print(f"DataLogger: Error logging row: {e}")

    def close(self):
        """Closes the file handle cleanly."""
        try:
            if self.file_handle:
                print(f"DataLogger: Closing file {self.filename}")
                self.file_handle.close()
        except Exception as e:
            print(f"DataLogger: Error closing file: {e}")