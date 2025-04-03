import os
import shutil
import logging
import argparse
import sys
import subprocess
import json
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QCheckBox, QTextEdit,
                             QFileDialog, QComboBox, QTimeEdit, QMessageBox, QDateEdit)
from PyQt6.QtCore import Qt, QTime, QDate

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for secure deletion
CHUNK_SIZE = 1024 * 1024  # 1MB chunks for overwriting

def _overwrite_file(file_path, passes, method, log_widget=None):
    """Helper function to overwrite a file securely."""
    try:
        file_size = os.path.getsize(file_path)
        logging.debug(f"Overwriting {file_path} ({file_size} bytes) using method '{method}' ({passes} passes)...")
        if log_widget:
            log_widget.append(f"Overwriting {file_path} ({file_size} bytes) using method '{method}' ({passes} passes)...")

        with open(file_path, 'wb') as f:
            for p in range(passes):
                logging.debug(f"Pass {p+1}/{passes} for {file_path}")
                f.seek(0) # Go to the beginning for each pass
                bytes_written = 0
                while bytes_written < file_size:
                    chunk = b''
                    # Determine data pattern for the pass
                    if method == 'random':
                        chunk = os.urandom(min(CHUNK_SIZE, file_size - bytes_written))
                    elif method == 'dod':
                        if p == 0: # Pass 1: Zeros
                            chunk = bytes(min(CHUNK_SIZE, file_size - bytes_written))
                        elif p == 1: # Pass 2: Ones
                            chunk = b'\xFF' * min(CHUNK_SIZE, file_size - bytes_written)
                        else: # Pass 3: Random
                            chunk = os.urandom(min(CHUNK_SIZE, file_size - bytes_written))
                    elif method == 'random_35pass':
                        # 35 passes using random data
                        chunk = os.urandom(min(CHUNK_SIZE, file_size - bytes_written))
                    else: # Default to random if method unknown (should not happen)
                         chunk = os.urandom(min(CHUNK_SIZE, file_size - bytes_written))

                    f.write(chunk)
                    bytes_written += len(chunk)
                f.flush()
                os.fsync(f.fileno()) # Ensure data is written to disk
        logging.debug(f"Finished overwriting {file_path}")
        if log_widget:
            log_widget.append(f"Finished overwriting {file_path}")
        return True
    except Exception as e:
        logging.error(f"Error overwriting {file_path}: {e}")
        if log_widget:
            log_widget.append(f"Error overwriting {file_path}: {e}")
        return False


def wipe_media(target_dir, secure_method='none', verbose=False, extensions=None, log_widget=None):
    """
    Wipes media files from the specified directory using the chosen method.
    secure_method: 'none', 'random', 'dod', 'random_35pass'
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logging.info(f"Starting media wiping from: {target_dir}")
    if log_widget:
        log_widget.append(f"Starting media wiping from: {target_dir}")

    # Define default media file extensions
    default_video_extensions = ['.mp4', '.avi', '.flv', '.wmv', '.mov', '.webm', '.mkv', '.f4v', '.vob', '.ogg', '.gifv', '.amv', '.mpg', '.mp2', '.mpeg', '.mpe', '.mpv', '.m4v', '.3gp']
    default_audio_extensions = ['.wav', '.aiff', '.mp3', '.acc', '.wma', '.ogg', '.flac']

    if extensions:
        # Use user-specified extensions
        media_extensions = [ext if ext.startswith('.') else '.' + ext for ext in extensions.split(',')]
    else:
        # Use default extensions
        media_extensions = default_video_extensions + default_audio_extensions

    try:
        for root, _, files in os.walk(target_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_extension = os.path.splitext(file)[1].lower()

                if file_extension in media_extensions:
                    try:
                        if secure_method == 'none':
                            os.remove(file_path)
                            logging.debug(f"Deleted (standard): {file_path}")
                            if log_widget:
                                log_widget.append(f"Deleted (standard): {file_path}")
                        else:
                            logging.info(f"Securely deleting ({secure_method}): {file_path}")
                            if log_widget:
                                log_widget.append(f"Securely deleting ({secure_method}): {file_path}")

                            overwrite_successful = False
                            if secure_method == 'random':
                                overwrite_successful = _overwrite_file(file_path, passes=1, method='random', log_widget=log_widget)
                            elif secure_method == 'dod':
                                overwrite_successful = _overwrite_file(file_path, passes=3, method='dod', log_widget=log_widget)
                            elif secure_method == 'random_35pass':
                                # Using 35 random passes
                                overwrite_successful = _overwrite_file(file_path, passes=35, method='random_35pass', log_widget=log_widget)

                            if overwrite_successful:
                                os.remove(file_path)
                                logging.debug(f"Deleted (secure, {secure_method}): {file_path}")
                                if log_widget:
                                    log_widget.append(f"Deleted (secure, {secure_method}): {file_path}")
                            else:
                                logging.error(f"Skipping deletion of {file_path} due to overwrite error.")
                                if log_widget:
                                    log_widget.append(f"Skipping deletion of {file_path} due to overwrite error.")

                    except Exception as e:
                        logging.error(f"Error processing {file_path}: {e}")
                        if log_widget:
                            log_widget.append(f"Error processing {file_path}: {e}")
    except Exception as e:
        logging.error(f"Error during media wiping: {e}")
        if log_widget:
            log_widget.append(f"Error during media wiping: {e}")

    logging.info("Media wiping complete.")
    if log_widget:
        log_widget.append("Media wiping complete.")

class MediaWiperGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MediaWiper")

        self.target_dir_label = QLabel("Target Directory:")
        self.target_dir_input = QLineEdit()
        self.target_dir_input.setToolTip("Enter the directory to wipe media files from.")
        self.target_dir_button = QPushButton("Browse")
        self.target_dir_button.setToolTip("Browse to select the target directory.")
        self.target_dir_button.clicked.connect(self.browse_directory)

        self.secure_method_label = QLabel("Secure Deletion Method:")
        self.secure_method_combo = QComboBox()
        self.secure_method_combo.addItem("Standard Delete (Not Secure)", "none")
        self.secure_method_combo.addItem("Secure: Single Pass (Random)", "random")
        self.secure_method_combo.addItem("Secure: DoD 5220.22-M (3 Pass)", "dod")
        self.secure_method_combo.addItem("Secure: 35 Pass (Random)", "random_35pass") # Renamed
        self.secure_method_combo.setToolTip("Select the method for deleting files.\nStandard is fastest but not secure.\nSecure methods overwrite data before deletion.")

        self.verbose_logging_checkbox = QCheckBox("Verbose Logging")
        self.verbose_logging_checkbox.setToolTip("Enable verbose logging to see more detailed information in the log.")
        self.extensions_label = QLabel("File Extensions (comma-separated):")
        self.extensions_input = QLineEdit()
        self.extensions_input.setToolTip("Enter the file extensions to delete, separated by commas (e.g., mp4,avi,mov).")

        self.enable_scheduling_checkbox = QCheckBox("Enable Scheduling")
        self.enable_scheduling_checkbox.setToolTip("Enable or disable scheduled media wiping.")
        self.enable_scheduling_checkbox.stateChanged.connect(self.toggle_scheduling)

        self.schedule_interval_label = QLabel("Schedule Interval:")
        self.schedule_interval_combo = QComboBox()
        self.schedule_interval_combo.addItem("Daily")
        self.schedule_interval_combo.addItem("Weekly")
        self.schedule_interval_combo.addItem("Monthly")
        self.schedule_interval_combo.setToolTip("Select the schedule interval.")
        self.schedule_interval_combo.setEnabled(False)

        self.schedule_date_label = QLabel("Schedule Date:")
        self.schedule_date_edit = QDateEdit()
        self.schedule_date_edit.setDate(QDate.currentDate())
        self.schedule_date_edit.setToolTip("Select the date to schedule the media wiping.")
        self.schedule_date_edit.setEnabled(False)

        self.schedule_time_label = QLabel("Schedule Time:")
        self.schedule_time_edit = QTimeEdit()
        self.schedule_time_edit.setTime(QTime.currentTime())
        self.schedule_time_edit.setToolTip("Select the time to schedule the media wiping.")
        self.schedule_time_edit.setEnabled(False)

        self.wipe_button = QPushButton("Wipe Media")
        self.wipe_button.setToolTip("Start wiping media files from the selected directory.")
        self.wipe_button.clicked.connect(self.start_wiping)

        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(self.target_dir_label)
        layout.addWidget(self.target_dir_input)
        layout.addWidget(self.target_dir_button)
        layout.addWidget(self.secure_method_label)
        layout.addWidget(self.secure_method_combo)
        layout.addWidget(self.verbose_logging_checkbox)
        layout.addWidget(self.extensions_label)
        layout.addWidget(self.extensions_input)
        layout.addWidget(self.enable_scheduling_checkbox)
        layout.addWidget(self.schedule_interval_label)
        layout.addWidget(self.schedule_interval_combo)
        layout.addWidget(self.schedule_date_label)
        layout.addWidget(self.schedule_date_edit)
        layout.addWidget(self.schedule_time_label)
        layout.addWidget(self.schedule_time_edit)
        self.next_schedule_label = QLabel("Next Schedule: N/A")
        layout.addWidget(self.next_schedule_label)
        layout.addWidget(self.wipe_button)
        layout.addWidget(self.log_widget)

        self.setLayout(layout)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.target_dir_input.setText(directory)

    def toggle_scheduling(self, state):
        self.schedule_interval_combo.setEnabled(state == Qt.CheckState.Checked.value)
        self.schedule_date_edit.setEnabled(state == Qt.CheckState.Checked.value)
        self.schedule_time_edit.setEnabled(state == Qt.CheckState.Checked.value)

    def start_wiping(self):
        target_dir = self.target_dir_input.text()
        # Get the method value ('none', 'random', 'dod', 'gutmann') from the combo box data
        secure_method = self.secure_method_combo.currentData()
        verbose = self.verbose_logging_checkbox.isChecked()
        extensions = self.extensions_input.text()
        enable_scheduling = self.enable_scheduling_checkbox.isChecked()

        if not target_dir:
            QMessageBox.critical(self, "Error", "Please select a target directory.")
            return

        if enable_scheduling:
            schedule_interval = self.schedule_interval_combo.currentText()
            schedule_date = self.schedule_date_edit.date()
            schedule_time = self.schedule_time_edit.time()

            # Create schedule info
            schedule_info = {
                "interval": schedule_interval.lower(),
                "date": schedule_date.toString("yyyy-MM-dd"),
                "time": schedule_time.toString("HH:mm")
            }
            schedule_info_json = json.dumps(schedule_info)

            # Calculate next schedule time
            next_schedule = "N/A"
            if schedule_interval == "Daily":
                next_schedule = schedule_date.addDays(1).toString("yyyy-MM-dd") + " " + schedule_time.toString("HH:mm")
            elif schedule_interval == "Weekly":
                next_schedule = schedule_date.addDays(7).toString("yyyy-MM-dd") + " " + schedule_time.toString("HH:mm")
            elif schedule_interval == "Monthly":
                next_schedule = schedule_date.addMonths(1).toString("yyyy-MM-dd") + " " + schedule_time.toString("HH:mm")

            self.next_schedule_label.setText(f"Next Schedule: {next_schedule}")

            # Start the scheduler.py script as a separate process
            try:
                scheduler_path = os.path.join(os.getcwd(), "scheduler.py")

                # Create a dictionary of wipe arguments
                # Pass the secure_method string instead of the old boolean
                wipe_args = {
                    "target_dir": target_dir,
                    "secure_method": secure_method,
                    "verbose": verbose,
                    "extensions": extensions
                }
                wipe_args_json = json.dumps(wipe_args)

                subprocess.Popen(
                    ["python", scheduler_path, "--schedule_info", schedule_info_json, "--wipe_args", wipe_args_json],
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
                self.log_widget.append("Scheduled media wiping task.")
                QMessageBox.information(self, "Success", "Media wiping scheduled successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to start scheduler: {e}")
        else:
            # Wipe media immediately
            # Pass the secure_method string
            wipe_media(target_dir, secure_method, verbose, extensions, self.log_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = MediaWiperGUI()

    # Check if there are command-line arguments
    if len(sys.argv) > 1:
        # Parse command-line arguments
        parser = argparse.ArgumentParser(description="Wipe media files from a directory.")
        parser.add_argument("target_dir", help="The directory to wipe.")
        parser.add_argument(
            "--secure-method",
            choices=['none', 'random', 'dod', 'random_35pass'], # Updated choice
            default='none',
            help="Specify the secure deletion method ('none', 'random', 'dod', 'random_35pass'). 'none' is standard delete (default)." # Updated help
        )
        parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging.")
        parser.add_argument("-e", "--extensions", help="Specify file extensions to delete (comma-separated).")

        args = parser.parse_args()

        # Run wipe_media with command-line arguments, passing the secure_method
        wipe_media(args.target_dir, secure_method=args.secure_method, verbose=args.verbose, extensions=args.extensions)
    else:
        # Show the GUI
        gui.show()
        sys.exit(app.exec())
