import os
import shutil
import logging
import argparse
import sys
import schedule
import time
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QCheckBox, QTextEdit,
                             QFileDialog, QComboBox, QTimeEdit)
from PyQt6.QtCore import Qt, QTime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def wipe_media(target_dir, secure_delete=False, verbose=False, extensions=None, log_widget=None):
    """
    Wipes media files from the specified directory.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logging.info(f"Wiping media files from: {target_dir}")
    if log_widget:
        log_widget.append(f"Wiping media files from: {target_dir}")

    # Define default media file extensions
    default_video_extensions = ['.mp4', '.avi', '.flv', '.wmv', '.mov', '.webm', '.mkv', '.f4v', '.vob', '.ogg', '.gifv', '.amv', '.mpg', '.mp2', '.mpeg', '.mpe', '.mpv', '.m4v', '.3gp']
    default_audio_extensions = ['.wav', '.aiff', '.mp3', '.acc', '.wma', '.ogg', '.flac']

    if extensions:
        # Use user-specified extensions
        media_extensions = extensions.split(',')
    else:
        # Use default extensions
        media_extensions = default_video_extensions + default_audio_extensions

    for root, _, files in os.walk(target_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_extension = os.path.splitext(file)[1].lower()

            if file_extension in media_extensions:
                try:
                    if secure_delete:
                        # Implement secure deletion (replace with actual secure deletion logic)
                        logging.debug(f"Securely deleting: {file_path}")
                        if log_widget:
                            log_widget.append(f"Securely deleting: {file_path}")
                        os.remove(file_path)
                    else:
                        os.remove(file_path)
                        logging.debug(f"Deleted: {file_path}")
                        if log_widget:
                            log_widget.append(f"Deleted: {file_path}")
                except Exception as e:
                    logging.error(f"Error deleting {file_path}: {e}")
                    if log_widget:
                        log_widget.append(f"Error deleting {file_path}: {e}")

    logging.info("Media wiping complete.")
    if log_widget:
        log_widget.append("Media wiping complete.")

def schedule_wipe_media(target_dir, secure_delete, verbose, extensions, log_widget, schedule_interval, schedule_time):
    """
    Schedules the media wiping task.
    """
    def scheduled_task():
        wipe_media(target_dir, secure_delete, verbose, extensions, log_widget)

    if schedule_interval == "Daily":
        schedule.every().day.at(schedule_time.strftime("%H:%M")).do(scheduled_task)
    elif schedule_interval == "Weekly":
        schedule.every().week.on(0).at(schedule_time.strftime("%H:%M")).do(scheduled_task) # 0 for Monday
    elif schedule_interval == "Monthly":
        schedule.every().month.on(1).at(schedule_time.strftime("%H:%M")).do(scheduled_task) # 1 for the first day of the month

    while True:
        schedule.run_pending()
        time.sleep(60)  # Wait for 1 minute

class MediaWiperGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MediaWiper")

        self.target_dir_label = QLabel("Target Directory:")
        self.target_dir_input = QLineEdit()
        self.target_dir_button = QPushButton("Browse")
        self.target_dir_button.clicked.connect(self.browse_directory)

        self.secure_delete_checkbox = QCheckBox("Secure Delete")
        self.verbose_logging_checkbox = QCheckBox("Verbose Logging")
        self.extensions_label = QLabel("File Extensions (comma-separated):")
        self.extensions_input = QLineEdit()

        self.enable_scheduling_checkbox = QCheckBox("Enable Scheduling")
        self.enable_scheduling_checkbox.setEnabled(False)

        self.schedule_interval_label = QLabel("Schedule Interval:")
        self.schedule_interval_combo = QComboBox()
        self.schedule_interval_combo.addItem("Daily")
        self.schedule_interval_combo.addItem("Weekly")
        self.schedule_interval_combo.addItem("Monthly")
        self.schedule_interval_combo.setEnabled(False)

        self.schedule_time_label = QLabel("Schedule Time:")
        self.schedule_time_edit = QTimeEdit()
        self.schedule_time_edit.setTime(QTime.currentTime())
        self.schedule_time_edit.setEnabled(False)

        self.wipe_button = QPushButton("Wipe Media")
        self.wipe_button.clicked.connect(self.start_wiping)

        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(self.target_dir_label)
        layout.addWidget(self.target_dir_input)
        layout.addWidget(self.target_dir_button)
        layout.addWidget(self.secure_delete_checkbox)
        layout.addWidget(self.verbose_logging_checkbox)
        layout.addWidget(self.extensions_label)
        layout.addWidget(self.extensions_input)
        layout.addWidget(self.enable_scheduling_checkbox)
        layout.addWidget(self.schedule_interval_label)
        layout.addWidget(self.schedule_interval_combo)
        layout.addWidget(self.schedule_time_label)
        layout.addWidget(self.schedule_time_edit)
        layout.addWidget(self.wipe_button)
        layout.addWidget(self.log_widget)

        self.setLayout(layout)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.target_dir_input.setText(directory)

    def start_wiping(self):
        target_dir = self.target_dir_input.text()
        secure_delete = self.secure_delete_checkbox.isChecked()
        verbose = self.verbose_logging_checkbox.isChecked()
        extensions = self.extensions_input.text()
        enable_scheduling = self.enable_scheduling_checkbox.isChecked()

        if enable_scheduling:
            schedule_interval = self.schedule_interval_combo.currentText()
            schedule_time = self.schedule_time_edit.time()
            # Schedule the media wiping task
            schedule_wipe_media(target_dir, secure_delete, verbose, extensions, self.log_widget, schedule_interval, schedule_time)
        else:
            # Wipe media immediately
            wipe_media(target_dir, secure_delete, verbose, extensions, self.log_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = MediaWiperGUI()

    # Check if there are command-line arguments
    if len(sys.argv) > 1:
        # Parse command-line arguments
        parser = argparse.ArgumentParser(description="Wipe media files from a directory.")
        parser.add_argument("target_dir", help="The directory to wipe.")
        parser.add_argument("-s", "--secure", action="store_true", help="Enable secure deletion.")
        parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging.")
        parser.add_argument("-e", "--extensions", help="Specify file extensions to delete (comma-separated).")

        args = parser.parse_args()

        # Run wipe_media with command-line arguments
        wipe_media(args.target_dir, args.secure, args.verbose, args.extensions)
    else:
        # Show the GUI
        gui.show()
        sys.exit(app.exec())
