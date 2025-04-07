import os
import shutil
import logging
import argparse
import sys
import subprocess
import json
import threading
import time # Added for potential sleep/yield in worker
from PyQt6 import QtGui, QtCore # Added QtGui, QtCore
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QCheckBox, QTextEdit,
                             QFileDialog, QComboBox, QTimeEdit, QMessageBox, QDateEdit,
                             QDialog, QProgressBar) # Added QDialog, QProgressBar
from PyQt6.QtCore import Qt, QTime, QDate, QThread, QObject, pyqtSignal # Added QThread, QObject, pyqtSignal

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define standard file categories and extensions
FILE_CATEGORIES = {
    "Video": ['.mp4', '.avi', '.flv', '.wmv', '.mov', '.webm', '.mkv', '.f4v', '.vob', '.ogg', '.gifv', '.amv', '.mpg', '.mp2', '.mpeg', '.mpe', '.mpv', '.m4v', '.3gp'],
    "Audio": ['.wav', '.aiff', '.mp3', '.aac', '.wma', '.ogg', '.flac'],
    "Images": ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'],
    "Documents": ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt']
}

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


# --- Worker Thread for Wiping ---
class WipeWorker(QObject):
    progress_updated = pyqtSignal(int, str) # value (0-100), message
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, target_dir, secure_method, verbose, extensions,
                 include_video, include_audio, include_images, include_documents, log_widget):
        super().__init__()
        self.target_dir = target_dir
        self.secure_method = secure_method
        self.verbose = verbose
        self.extensions = extensions
        self.include_video = include_video
        self.include_audio = include_audio
        self.include_images = include_images
        self.include_documents = include_documents
        self.log_widget = log_widget
        self._is_cancelled = False # Flag for cancellation

    def cancel(self):
        """Sets the cancellation flag."""
        logging.info("Cancellation requested for wipe worker.")
        self._is_cancelled = True

    def run(self):
        """Performs the wiping operation, emitting signals for progress."""
        try:
            if self.verbose:
                logging.getLogger().setLevel(logging.DEBUG)

            logging.info(f"Worker starting media wiping from: {self.target_dir}")
            if self.log_widget:
                # Use invokeMethod for thread-safe GUI updates from worker if needed
                # QtCore.QMetaObject.invokeMethod(self.log_widget, "append", Qt.ConnectionType.QueuedConnection, QtCore.Q_ARG(str, f"Starting media wiping from: {self.target_dir}"))
                # For simplicity now, we assume log_widget append is safe enough or handled elsewhere
                 self.log_widget.append(f"Starting media wiping from: {self.target_dir}")
            self.progress_updated.emit(0, f"Scanning {self.target_dir}...")

            # Build the list of extensions to wipe
            extensions_to_wipe = set()
            if self.include_video: extensions_to_wipe.update(FILE_CATEGORIES["Video"])
            if self.include_audio: extensions_to_wipe.update(FILE_CATEGORIES["Audio"])
            if self.include_images: extensions_to_wipe.update(FILE_CATEGORIES["Images"])
            if self.include_documents: extensions_to_wipe.update(FILE_CATEGORIES["Documents"])

            if self.extensions:
                custom_extensions = [ext.strip() for ext in self.extensions.split(',')]
                for ext in custom_extensions:
                    if ext: extensions_to_wipe.add(ext if ext.startswith('.') else '.' + ext)

            media_extensions = list(extensions_to_wipe)

            if not media_extensions:
                logging.warning("No file extensions specified for wiping.")
                if self.log_widget: self.log_widget.append("No file extensions specified.")
                self.error_occurred.emit("No file extensions specified for wiping.")
                # self.finished.emit() # Error signal implies finish
                return # Exit run method

            logging.info(f"Targeting extensions: {', '.join(media_extensions)}")
            if self.log_widget: self.log_widget.append(f"Targeting extensions: {', '.join(media_extensions)}")

            # --- First Pass: Scan for files to count total ---
            files_to_wipe = []
            self.progress_updated.emit(0, "Scanning for files...")
            # REMOVED: QApplication.processEvents() # Allow UI to update during scan - Unsafe from worker thread
            try:
                for root, _, files in os.walk(self.target_dir):
                    if self._is_cancelled:
                        logging.info("Wiping cancelled during scan.")
                        self.progress_updated.emit(0, "Scan cancelled.")
                        self.finished.emit()
                        return
                    for file in files:
                        file_extension = os.path.splitext(file)[1].lower()
                        if file_extension in media_extensions:
                            files_to_wipe.append(os.path.join(root, file))
                    # Yield control briefly during walk if needed - Not strictly necessary with QThread
                    # time.sleep(0.001)
            except Exception as e:
                # Ensure cancellation check before emitting error if possible
                if self._is_cancelled:
                    logging.info("Wiping cancelled during scan error handling.")
                    self.finished.emit()
                    return
                logging.error(f"Error scanning directory {self.target_dir}: {e}")
                self.error_occurred.emit(f"Error scanning directory: {e}")
                # self.finished.emit()
                return

            total_files = len(files_to_wipe)
            logging.info(f"Found {total_files} files to wipe.")
            if self.log_widget: self.log_widget.append(f"Found {total_files} files to wipe.")
            if total_files == 0:
                self.progress_updated.emit(100, "No matching files found to wipe.")
                self.finished.emit()
                return

            # --- Second Pass: Wipe files ---
            processed_files = 0
            for file_path in files_to_wipe:
                if self._is_cancelled:
                    logging.info("Wiping cancelled.")
                    # Update progress to reflect cancellation point
                    progress_percent = int((processed_files / total_files) * 100) if total_files > 0 else 0
                    self.progress_updated.emit(progress_percent, "Wiping cancelled.")
                    self.finished.emit()
                    return

                processed_files += 1
                progress_percent = int((processed_files / total_files) * 100)
                # Limit message length for display
                display_filename = os.path.basename(file_path)
                if len(display_filename) > 50: display_filename = display_filename[:23] + "..." + display_filename[-24:]
                status_message = f"Wiping ({processed_files}/{total_files}): {display_filename}"
                self.progress_updated.emit(progress_percent, status_message)
                logging.debug(status_message)

                try:
                    if self.secure_method == 'none':
                        os.remove(file_path)
                        logging.debug(f"Deleted (standard): {file_path}")
                        # Don't flood log widget from worker, main log is enough
                        # if self.log_widget: self.log_widget.append(f"Deleted (standard): {file_path}")
                    else:
                        logging.info(f"Securely deleting ({self.secure_method}): {file_path}")
                        # if self.log_widget: self.log_widget.append(f"Securely deleting ({self.secure_method}): {file_path}")

                        overwrite_successful = False
                        # Pass None for log_widget to _overwrite_file to avoid potential thread issues
                        if self.secure_method == 'random':
                            overwrite_successful = _overwrite_file(file_path, passes=1, method='random', log_widget=None)
                        elif self.secure_method == 'dod':
                            overwrite_successful = _overwrite_file(file_path, passes=3, method='dod', log_widget=None)
                        elif self.secure_method == 'random_35pass':
                            overwrite_successful = _overwrite_file(file_path, passes=35, method='random_35pass', log_widget=None)

                        if overwrite_successful:
                            os.remove(file_path)
                            logging.debug(f"Deleted (secure, {self.secure_method}): {file_path}")
                            # if self.log_widget: self.log_widget.append(f"Deleted (secure, {self.secure_method}): {file_path}")
                        else:
                            logging.error(f"Skipping deletion of {file_path} due to overwrite error.")
                            if self.log_widget: self.log_widget.append(f"Skipping deletion of {file_path} due to overwrite error.")
                            # Optionally emit an error signal here or just log it

                except Exception as e:
                    logging.error(f"Error processing {file_path}: {e}")
                    if self.log_widget: self.log_widget.append(f"Error processing {file_path}: {e}")
                    # Optionally emit an error signal here for specific file errors
                    # self.error_occurred.emit(f"Error processing {os.path.basename(file_path)}: {e}")
                    # Decide whether to continue or stop on single file error

                # Yield control briefly to keep GUI responsive - Unsafe from worker thread
                # time.sleep(0.001) # Be careful with sleeps, can slow down significantly
                # REMOVED: QApplication.processEvents()


            # Ensure cancellation check before final signals
            if self._is_cancelled:
                 logging.info("Wiping cancelled before final completion signal.")
                 self.finished.emit()
                 return

            logging.info("Media wiping complete.")
            if self.log_widget: self.log_widget.append("Media wiping complete.")
            # Ensure final progress update is 100%
            self.progress_updated.emit(100, "Wiping complete.")
            self.finished.emit()

        except Exception as e:
            logging.error(f"Unexpected error during media wiping worker: {e}")
            self.error_occurred.emit(f"An unexpected error occurred: {e}")
            # self.finished.emit() # Error signal implies finish


# --- Progress Dialog ---
class ProgressDialog(QDialog):
    # Signal to request cancellation from the main GUI thread
    cancel_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wiping Progress")
        self.setModal(True) # Make it modal
        self.setMinimumWidth(400)
        # Prevent closing via 'X' button while running
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)


        self.progress_bar = QProgressBar(self)
        self.status_label = QLabel("Starting...", self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Optional: Add a cancel button
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.request_cancel)

        layout = QVBoxLayout(self)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)
        self.progress_bar.setValue(0)
        self._is_finished = False # Flag to prevent double close/accept

    @QtCore.pyqtSlot(int, str)
    def update_progress(self, value, message):
        if self._is_finished: return # Don't update if already finished
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        # QApplication.processEvents() # Let the main event loop handle this

    def request_cancel(self):
        self.status_label.setText("Cancellation requested...")
        self.cancel_button.setEnabled(False) # Disable button after click
        self.cancel_requested.emit() # Signal the main window/controller

    def closeEvent(self, event):
        # Prevent closing via 'X' button if operation is running
        if not self._is_finished:
            self.request_cancel()
            event.ignore() # Ignore the close event initially
        else:
            event.accept() # Allow closing if finished

    def mark_finished(self):
        """Marks the dialog as finished, allowing it to be closed."""
        self._is_finished = True
        self.cancel_button.setEnabled(False) # Disable cancel when finished
        # Optionally change button text to "Close"
        # self.cancel_button.setText("Close")
        # self.cancel_button.clicked.disconnect()
        # self.cancel_button.clicked.connect(self.accept)
        # self.cancel_button.setEnabled(True)


# --- Main GUI Application ---
# Keep wipe_media for CLI usage, GUI will use WipeWorker
def wipe_media(target_dir, secure_method='none', verbose=False, extensions=None,
               include_video=False, include_audio=False, include_images=False,
               include_documents=False, log_widget=None):
    """
    Wipes media files from the specified directory based on selected categories and custom extensions using the chosen method.
    secure_method: 'none', 'random', 'dod', 'random_35pass'
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logging.info(f"Starting media wiping from: {target_dir}")
    if log_widget:
        log_widget.append(f"Starting media wiping from: {target_dir}")

    # Build the list of extensions to wipe
    extensions_to_wipe = set()
    if include_video:
        extensions_to_wipe.update(FILE_CATEGORIES["Video"])
    if include_audio:
        extensions_to_wipe.update(FILE_CATEGORIES["Audio"])
    if include_images:
        extensions_to_wipe.update(FILE_CATEGORIES["Images"])
    if include_documents:
        extensions_to_wipe.update(FILE_CATEGORIES["Documents"])

    if extensions:
        custom_extensions = [ext.strip() for ext in extensions.split(',')]
        for ext in custom_extensions:
            if ext: # Avoid adding empty strings if there are trailing commas etc.
                extensions_to_wipe.add(ext if ext.startswith('.') else '.' + ext)

    media_extensions = list(extensions_to_wipe)

    if not media_extensions:
        logging.warning("No file extensions specified for wiping. Aborting.")
        if log_widget:
            log_widget.append("No file extensions specified for wiping. Aborting.")
        return

    logging.info(f"Targeting extensions: {', '.join(media_extensions)}")
    if log_widget:
        log_widget.append(f"Targeting extensions: {', '.join(media_extensions)}")

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
        # Set Icon - Ensure the path is correct relative to the script location
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'Icons', 'MediaWiper.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))
        else:
            logging.warning(f"Icon file not found at: {icon_path}")


        # State tracking
        self.is_wiping = False
        self.worker = None
        self.wipe_thread = None
        self.progress_dialog = None

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
        self.extensions_label = QLabel("Custom File Extensions (comma-separated):")
        self.extensions_input = QLineEdit()
        self.extensions_input.setToolTip("Enter any additional custom file extensions to delete, separated by commas (e.g., .log,.tmp).")

        self.video_checkbox = QCheckBox("Include Video Files")
        self.video_checkbox.setToolTip("Include standard video file extensions like .mp4, .avi, .mov, etc.")
        self.audio_checkbox = QCheckBox("Include Audio Files")
        self.audio_checkbox.setToolTip("Include standard audio file extensions like .mp3, .wav, .aac, etc.")
        self.images_checkbox = QCheckBox("Include Image Files")
        self.images_checkbox.setToolTip("Include standard image file extensions like .jpg, .png, .gif, etc.")
        self.documents_checkbox = QCheckBox("Include Document Files")
        self.documents_checkbox.setToolTip("Include standard document file extensions like .pdf, .docx, .txt, etc.")

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
        layout.addWidget(self.video_checkbox)
        layout.addWidget(self.audio_checkbox)
        layout.addWidget(self.images_checkbox)
        layout.addWidget(self.documents_checkbox)
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

        # Load last used directory if available (optional enhancement)
        # self.load_settings()

    # def load_settings(self): # Example
    #     try:
    #         # Use a path relative to user's config or app data dir ideally
    #         settings_path = "mediawiper_settings.json"
    #         if os.path.exists(settings_path):
    #             with open(settings_path, "r") as f:
    #                 settings = json.load(f)
    #                 self.target_dir_input.setText(settings.get("last_directory", ""))
    #     except Exception as e:
    #         logging.warning(f"Could not load settings: {e}")

    # def save_settings(self): # Example
    #     try:
    #         settings_path = "mediawiper_settings.json"
    #         settings = {"last_directory": self.target_dir_input.text()}
    #         with open(settings_path, "w") as f:
    #             json.dump(settings, f)
    #     except Exception as e:
    #         logging.warning(f"Could not save settings: {e}")


    def browse_directory(self):
        start_dir = self.target_dir_input.text() if os.path.isdir(self.target_dir_input.text()) else os.path.expanduser("~") # Start in home dir if input invalid
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", start_dir)
        if directory:
            self.target_dir_input.setText(directory)
            # self.save_settings() # Save selection if using settings

    def toggle_scheduling(self, state):
        is_checked = (state == Qt.CheckState.Checked.value)
        self.schedule_interval_combo.setEnabled(is_checked)
        self.schedule_date_edit.setEnabled(is_checked)
        self.schedule_time_edit.setEnabled(is_checked)
        # Disable immediate wipe button if scheduling is enabled
        self.wipe_button.setDisabled(is_checked)
        if is_checked:
             self.wipe_button.setToolTip("Disable scheduling to enable immediate wipe.")
        else:
             self.wipe_button.setToolTip("Start wiping media files from the selected directory.")


    def start_wiping(self):
        if self.is_wiping:
            QMessageBox.warning(self, "Busy", "A wiping operation is already in progress.")
            return

        target_dir = self.target_dir_input.text()
        if not target_dir or not os.path.isdir(target_dir):
            QMessageBox.critical(self, "Error", "Please select a valid target directory.")
            return

        # Get the method value ('none', 'random', 'dod', 'random_35pass') from the combo box data
        secure_method = self.secure_method_combo.currentData() # Correctly gets the data ('none', 'random', etc.)
        verbose = self.verbose_logging_checkbox.isChecked()
        extensions = self.extensions_input.text()
        include_video = self.video_checkbox.isChecked()
        include_audio = self.audio_checkbox.isChecked()
        include_images = self.images_checkbox.isChecked()
        include_documents = self.documents_checkbox.isChecked()
        enable_scheduling = self.enable_scheduling_checkbox.isChecked()


        # --- Scheduling Logic (remains the same, but ensure path is robust) ---
        if enable_scheduling:
            # Ensure scheduler.py exists relative to this script
            script_dir = os.path.dirname(__file__)
            scheduler_path = os.path.join(script_dir, "scheduler.py") # Path relative to media_wiper.py
            if not os.path.exists(scheduler_path):
                 QMessageBox.critical(self, "Error", f"Scheduler script not found at expected location: {scheduler_path}")
                 return

            schedule_interval = self.schedule_interval_combo.currentText()
            schedule_date = self.schedule_date_edit.date()
            schedule_time = self.schedule_time_edit.time()

            schedule_info = { # Create schedule info
                 "interval": schedule_interval.lower(),
                 "date": schedule_date.toString("yyyy-MM-dd"),
                 "time": schedule_time.toString("HH:mm")
            }
            schedule_info_json = json.dumps(schedule_info)

            # Calculate next schedule time (logic seems ok)
            next_schedule_dt = None
            # Use QDateTime for calculations
            current_dt = QtCore.QDateTime(schedule_date, schedule_time)
            now = QtCore.QDateTime.currentDateTime()

            # Ensure the scheduled time is in the future
            if current_dt <= now:
                 # If daily, schedule for tomorrow same time
                 if schedule_interval == "Daily":
                     current_dt = current_dt.addDays(1)
                 # If weekly/monthly, find the next occurrence *after* today
                 elif schedule_interval == "Weekly":
                     while current_dt <= now:
                         current_dt = current_dt.addDays(7)
                 elif schedule_interval == "Monthly":
                     while current_dt <= now:
                         current_dt = current_dt.addMonths(1)

            # Now calculate the *next* schedule after the (potentially adjusted) current_dt
            if schedule_interval == "Daily":
                next_schedule_dt = current_dt # Already adjusted if needed
            elif schedule_interval == "Weekly":
                next_schedule_dt = current_dt # Already adjusted if needed
            elif schedule_interval == "Monthly":
                next_schedule_dt = current_dt # Already adjusted if needed

            # Display the *first* scheduled time if it's in the future,
            # otherwise display the *next* calculated time.
            display_dt = current_dt if current_dt > now else next_schedule_dt
            if display_dt:
                 self.next_schedule_label.setText(f"Next Schedule: {display_dt.toString('yyyy-MM-dd HH:mm')}")
            else:
                 self.next_schedule_label.setText("Next Schedule: N/A")


            try: # Start the scheduler.py script as a separate process
                wipe_args = { # Create a dictionary of wipe arguments
                    "target_dir": target_dir,
                    "secure_method": secure_method, # Pass the method string
                    "verbose": verbose,
                    "extensions": extensions,
                    "include_video": include_video,
                    "include_audio": include_audio,
                     "include_images": include_images,
                     "include_documents": include_documents
                }
                wipe_args_json = json.dumps(wipe_args)

                # Use sys.executable to ensure the correct python interpreter is used
                python_executable = sys.executable
                command = [
                    python_executable, scheduler_path,
                    "--schedule_info", schedule_info_json,
                    "--wipe_args", wipe_args_json
                ]
                logging.info(f"Starting scheduler process: {' '.join(command)}")

                # Run scheduler detached
                subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

                self.log_widget.append("Scheduled media wiping task.")
                QMessageBox.information(self, "Success", "Media wiping scheduled successfully.\nThe scheduler will run in the background.")
            except Exception as e:
                logging.error(f"Failed to start scheduler: {e}")
                QMessageBox.critical(self, "Error", f"Failed to start scheduler: {e}")

        # --- Immediate Wipe Logic (using Worker Thread) ---
        else:
            self.is_wiping = True
            self.wipe_button.setEnabled(False)
            self.enable_scheduling_checkbox.setEnabled(False) # Disable scheduling during wipe
            # Disable other controls maybe?

            # Create and show progress dialog
            self.progress_dialog = ProgressDialog(self)
            self.progress_dialog.cancel_requested.connect(self.cancel_wiping) # Connect cancel signal

            # Create worker and thread
            self.wipe_thread = QThread()
            self.worker = WipeWorker(
                target_dir, secure_method, verbose, extensions,
                include_video, include_audio, include_images, include_documents,
                self.log_widget # Pass log widget reference
            )
            self.worker.moveToThread(self.wipe_thread)

            # Connect signals
            self.worker.progress_updated.connect(self.progress_dialog.update_progress)
            self.worker.finished.connect(self.on_wipe_finished)
            self.worker.error_occurred.connect(self.on_wipe_error)

            # Connect thread signals
            self.wipe_thread.started.connect(self.worker.run)
            # Clean up thread and worker when thread finishes
            self.worker.finished.connect(self.wipe_thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.wipe_thread.finished.connect(self.wipe_thread.deleteLater)

            # Start the thread
            self.wipe_thread.start()

            # Show the modal dialog (blocks until closed)
            self.progress_dialog.exec()

            # Code here runs after the dialog is closed (either normally or via cancel)
            logging.debug("Progress dialog closed.")
            # Final cleanup is handled in on_wipe_finished / on_wipe_error


    @QtCore.pyqtSlot()
    def cancel_wiping(self):
        """Requests cancellation of the running wipe operation."""
        if self.worker:
            logging.info("Cancel requested from GUI.")
            self.worker.cancel()
        # Dialog handling (disabling button etc.) is done in ProgressDialog.request_cancel

    @QtCore.pyqtSlot(str)
    def on_wipe_error(self, message):
        """Handles errors reported by the worker."""
        logging.error(f"Wipe Error: {message}")
        # Ensure cleanup happens even on error
        self.on_wipe_finished(error=True, error_message=message)


    @QtCore.pyqtSlot()
    def on_wipe_finished(self, error=False, error_message=""):
        """Cleans up after the wipe operation is finished or cancelled."""
        logging.debug(f"on_wipe_finished called (error={error}). is_wiping={self.is_wiping}")

        if not self.is_wiping: # Prevent double execution
             logging.warning("on_wipe_finished called but not wiping.")
             return

        # Ensure the thread quits properly before we potentially delete the worker it might be using
        if self.wipe_thread and self.wipe_thread.isRunning():
            logging.debug("Requesting thread quit and waiting...")
            self.wipe_thread.quit()
            if not self.wipe_thread.wait(3000): # Wait up to 3 seconds
                 logging.warning("Thread did not finish quitting gracefully.")
                 # Consider terminating if necessary, but it's risky: self.wipe_thread.terminate()

        if self.progress_dialog:
             if not self.progress_dialog._is_finished:
                 self.progress_dialog.mark_finished()
                 if error:
                     final_message = f"Error: {error_message}" if error_message else "Finished with errors."
                     self.progress_dialog.update_progress(self.progress_dialog.progress_bar.value(), final_message) # Keep last progress value on error
                 else:
                     self.progress_dialog.update_progress(100, "Finished Successfully")

                 # Make dialog closable manually
                 self.progress_dialog.cancel_button.setText("Close")
                 self.progress_dialog.cancel_button.setEnabled(True)
                 try: # Disconnect safely in case it was already disconnected
                      self.progress_dialog.cancel_button.clicked.disconnect()
                 except TypeError:
                      pass # Signal was not connected
                 self.progress_dialog.cancel_button.clicked.connect(self.progress_dialog.accept)

             # --- Auto-close on success ---
             if not error:
                 logging.debug("Operation successful, accepting progress dialog.")
                 self.progress_dialog.accept() # Close dialog automatically on success
             # On error, leave dialog open for user to read message and close manually

        # Reset state AFTER handling dialog
        self.is_wiping = False
        self.wipe_button.setEnabled(not self.enable_scheduling_checkbox.isChecked()) # Re-enable based on scheduling checkbox
        self.enable_scheduling_checkbox.setEnabled(True) # Re-enable scheduling checkbox

        # References should be cleaned up by deleteLater signals connected earlier
        self.worker = None
        self.wipe_thread = None
        self.progress_dialog = None # Clear reference

        logging.info("Wiping process finished and GUI state reset.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Ensure GUI object is created before potential CLI execution
    gui = MediaWiperGUI()

    # --- Command-Line Argument Handling ---
    # Check if there are command-line arguments *other than* the script name
    if len(sys.argv) > 1:
        # Check if the first argument looks like a flag (e.g., -h, --help) or a directory
        # This helps distinguish between running via CLI and just launching the app
        first_arg = sys.argv[1]
        is_cli_run = first_arg.startswith('-') or os.path.isdir(first_arg) or os.path.isfile(first_arg) # Basic check

        if is_cli_run:
            # Parse command-line arguments using the existing parser
            parser = argparse.ArgumentParser(description="Wipe media files from a directory (CLI Mode).")
            # Make target_dir optional for CLI? Or require it? Assuming required for now.
            parser.add_argument("target_dir", help="The directory to wipe media files from.")
            parser.add_argument(
                "--secure-method",
                choices=['none', 'random', 'dod', 'random_35pass'],
                default='none',
                help="Secure deletion method ('none', 'random', 'dod', 'random_35pass'). Default: 'none'."
            )
            parser.add_argument("-v", "--verbose", action="store_true", help="Enable detailed (debug) logging.")
            parser.add_argument("-e", "--extensions", help="Custom file extensions to delete (e.g., '.log,.tmp').")
            parser.add_argument("--include-video", action="store_true", help="Include standard video files.")
            parser.add_argument("--include-audio", action="store_true", help="Include standard audio files.")
            parser.add_argument("--include-images", action="store_true", help="Include standard image files.")
            parser.add_argument("--include-documents", action="store_true", help="Include standard document files.")

            try:
                args = parser.parse_args()

                # Configure logging based on verbose flag for CLI
                if args.verbose:
                    logging.getLogger().setLevel(logging.DEBUG)
                else:
                    logging.getLogger().setLevel(logging.INFO) # Ensure INFO level for CLI default

                logging.info("Running MediaWiper in CLI mode.")
                # Run the original wipe_media function for CLI execution
                # Pass None for log_widget as there's no GUI log area in CLI mode
                wipe_media(
                    args.target_dir,
                    secure_method=args.secure_method,
                    verbose=args.verbose,
                    extensions=args.extensions,
                    include_video=args.include_video,
                    include_audio=args.include_audio,
                    include_images=args.include_images,
                    include_documents=args.include_documents,
                    log_widget=None
                )
                logging.info("CLI execution finished.")
                sys.exit(0) # Exit successfully after CLI run

            except SystemExit as e:
                 # Catch SystemExit from argparse (e.g., for -h or --help)
                 sys.exit(e.code)
            except Exception as e:
                 logging.error(f"Error during CLI execution: {e}")
                 print(f"Error: {e}", file=sys.stderr)
                 sys.exit(1) # Exit with error code

        else:
             # If not a CLI run (no args or args don't look like flags/paths), show GUI
             logging.info("Starting MediaWiper GUI.")
             gui.show()
             sys.exit(app.exec())
    else:
        # No arguments provided, show the GUI
        logging.info("Starting MediaWiper GUI.")
        gui.show()
        sys.exit(app.exec())
