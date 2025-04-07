"""
Main GUI window class for the MediaWiper application.
"""

import os
import sys
import json
import subprocess
import logging
from PyQt6 import QtGui, QtCore
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
                             QCheckBox, QTextEdit, QFileDialog, QComboBox,
                             QTimeEdit, QMessageBox, QDateEdit)
from PyQt6.QtCore import Qt, QTime, QDate, QThread

# Import other UI components and core logic using relative paths
from .progress_dialog import ProgressDialog
from ..core.worker import WipeWorker
# Assuming scheduler is still in the parent 'code' directory
# If scheduler moves, adjust this import
# from ..scheduler import ... # Example if scheduler moves

class MediaWiperGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MediaWiper")

        # --- Icon Path Handling ---
        # Get base path robustly (works when run as script or bundled)
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle, the base path is sys._MEIPASS
            base_path = sys._MEIPASS
        else:
            # If run as a normal script, base path is directory of this file
            # Go up two levels from ui/main_window.py to src/
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

        icon_path = os.path.join(base_path, 'Icons', 'MediaWiper.ico')
        logging.debug(f"Attempting to load icon from: {icon_path}")
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))
        else:
            logging.warning(f"Icon file not found at: {icon_path}")

        # State tracking
        self.is_wiping = False
        self.worker = None
        self.wipe_thread = None
        self.progress_dialog = None

        # --- UI Element Creation ---
        self.target_dir_label = QLabel("Target Directory:")
        self.target_dir_input = QLineEdit()
        self.target_dir_input.setToolTip("Enter the directory to wipe media files from.")
        self.target_dir_button = QPushButton("Browse")
        self.target_dir_button.setToolTip("Browse to select the target directory.")

        self.secure_method_label = QLabel("Secure Deletion Method:")
        self.secure_method_combo = QComboBox()
        self.secure_method_combo.addItem("Standard Delete (Not Secure)", "none")
        self.secure_method_combo.addItem("Secure: Single Pass (Random)", "random")
        self.secure_method_combo.addItem("Secure: DoD 5220.22-M (3 Pass)", "dod")
        self.secure_method_combo.addItem("Secure: 35 Pass (Random)", "random_35pass")
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

        # Initialize button for immediate wipe state
        self.wipe_button = QPushButton("Wipe Media Now")
        self.wipe_button.setToolTip("Start wiping media files immediately.")

        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.next_schedule_label = QLabel("Next Schedule: N/A")

        # --- Layout ---
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
        layout.addWidget(self.next_schedule_label)
        layout.addWidget(self.wipe_button)
        layout.addWidget(self.log_widget)
        self.setLayout(layout)

        # --- Connect Signals ---
        self.target_dir_button.clicked.connect(self.browse_directory)
        self.enable_scheduling_checkbox.stateChanged.connect(self.toggle_scheduling)
        self.wipe_button.clicked.connect(self.start_wiping)

        # Load last used directory if available (optional enhancement)
        # self.load_settings()

    # --- Methods ---

    # def load_settings(self): # Example
    #     # ... (implementation as before) ...

    # def save_settings(self): # Example
    #     # ... (implementation as before) ...

    def browse_directory(self):
        start_dir = self.target_dir_input.text() if os.path.isdir(self.target_dir_input.text()) else os.path.expanduser("~")
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", start_dir)
        if directory:
            self.target_dir_input.setText(directory)
            # self.save_settings()

    def toggle_scheduling(self, state):
        is_checked = (state == Qt.CheckState.Checked.value)
        self.schedule_interval_combo.setEnabled(is_checked)
        self.schedule_date_edit.setEnabled(is_checked)
        self.schedule_time_edit.setEnabled(is_checked)
        # Keep button enabled, but change text and tooltip
        # self.wipe_button.setDisabled(is_checked) # REMOVED this line
        if is_checked:
             self.wipe_button.setText("Apply Schedule")
             self.wipe_button.setToolTip("Apply the selected schedule settings and run the scheduler in the background.")
        else:
             self.wipe_button.setText("Wipe Media Now")
             self.wipe_button.setToolTip("Start wiping media files immediately.")

    def start_wiping(self):
        if self.is_wiping:
            QMessageBox.warning(self, "Busy", "A wiping operation is already in progress.")
            return

        target_dir = self.target_dir_input.text()
        if not target_dir or not os.path.isdir(target_dir):
            QMessageBox.critical(self, "Error", "Please select a valid target directory.")
            return

        secure_method = self.secure_method_combo.currentData()
        verbose = self.verbose_logging_checkbox.isChecked()
        extensions = self.extensions_input.text()
        include_video = self.video_checkbox.isChecked()
        include_audio = self.audio_checkbox.isChecked()
        include_images = self.images_checkbox.isChecked()
        include_documents = self.documents_checkbox.isChecked()
        enable_scheduling = self.enable_scheduling_checkbox.isChecked()

        # --- Scheduling Logic ---
        if enable_scheduling:
            # Path to scheduler relative to this file's location (ui/main_window.py)
            script_dir = os.path.dirname(os.path.dirname(__file__)) # Go up one level to 'code' dir
            scheduler_path = os.path.join(script_dir, "scheduler.py")
            logging.debug(f"Looking for scheduler at: {scheduler_path}")

            if not os.path.exists(scheduler_path):
                 QMessageBox.critical(self, "Error", f"Scheduler script not found at expected location: {scheduler_path}")
                 return

            schedule_interval = self.schedule_interval_combo.currentText()
            schedule_date = self.schedule_date_edit.date()
            schedule_time = self.schedule_time_edit.time()

            schedule_info = {
                 "interval": schedule_interval.lower(),
                 "date": schedule_date.toString("yyyy-MM-dd"),
                 "time": schedule_time.toString("HH:mm")
            }
            schedule_info_json = json.dumps(schedule_info)

            # Calculate next schedule time
            next_schedule_dt = None
            current_dt = QtCore.QDateTime(schedule_date, schedule_time)
            now = QtCore.QDateTime.currentDateTime()
            if current_dt <= now:
                 if schedule_interval == "Daily": current_dt = current_dt.addDays(1)
                 elif schedule_interval == "Weekly":
                     while current_dt <= now: current_dt = current_dt.addDays(7)
                 elif schedule_interval == "Monthly":
                     while current_dt <= now: current_dt = current_dt.addMonths(1)

            if schedule_interval == "Daily": next_schedule_dt = current_dt
            elif schedule_interval == "Weekly": next_schedule_dt = current_dt
            elif schedule_interval == "Monthly": next_schedule_dt = current_dt

            display_dt = current_dt if current_dt > now else next_schedule_dt
            if display_dt:
                 self.next_schedule_label.setText(f"Next Schedule: {display_dt.toString('yyyy-MM-dd HH:mm')}")
            else:
                 self.next_schedule_label.setText("Next Schedule: N/A")

            try:
                wipe_args = {
                    "target_dir": target_dir, "secure_method": secure_method,
                    "verbose": verbose, "extensions": extensions,
                    "include_video": include_video, "include_audio": include_audio,
                    "include_images": include_images, "include_documents": include_documents
                }
                wipe_args_json = json.dumps(wipe_args)
                python_executable = sys.executable

                # --- Start of Changes ---
                # 1. Construct command to run scheduler as a module
                command = [
                    python_executable, '-m', 'src.code.scheduler', # Use -m and module path
                    "--schedule_info", schedule_info_json,
                    "--wipe_args", wipe_args_json
                ]
                logging.info(f"Starting scheduler process as module: {' '.join(command)}")

                # 2. Define and add detachment flags for Windows
                DETACHED_PROCESS = 0x00000008
                CREATE_NEW_PROCESS_GROUP = 0x00000200
                flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP

                # 3. Launch subprocess with new command and flags
                # Note: For cross-platform, you'd check sys.platform and use
                # start_new_session=True on Linux/macOS instead of creationflags.
                subprocess.Popen(command, creationflags=flags)
                # --- End of Changes ---

                self.log_widget.append("Scheduled media wiping task (attempting detached).") # Updated log message
                QMessageBox.information(self, "Success", "Media wiping scheduled successfully.\nThe scheduler will attempt to run in the background.") # Updated success message
            except Exception as e:
                logging.error(f"Failed to start scheduler: {e}")
                QMessageBox.critical(self, "Error", f"Failed to start scheduler: {e}")

        # --- Immediate Wipe Logic ---
        else:
            self.is_wiping = True
            self.wipe_button.setEnabled(False)
            self.enable_scheduling_checkbox.setEnabled(False)

            self.progress_dialog = ProgressDialog(self)
            self.progress_dialog.cancel_requested.connect(self.cancel_wiping)

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
            self.wipe_thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.wipe_thread.quit)
            # Use deleteLater for safer cleanup after signals are processed
            self.worker.finished.connect(self.worker.deleteLater)
            self.wipe_thread.finished.connect(self.wipe_thread.deleteLater)

            self.wipe_thread.start()
            self.progress_dialog.exec() # Show modal dialog

            logging.debug("Progress dialog closed.")

    @QtCore.pyqtSlot()
    def cancel_wiping(self):
        if self.worker:
            logging.info("Cancel requested from GUI.")
            self.worker.cancel()

    @QtCore.pyqtSlot(str)
    def on_wipe_error(self, message):
        logging.error(f"Wipe Error: {message}")
        self.on_wipe_finished(error=True, error_message=message)

    @QtCore.pyqtSlot()
    def on_wipe_finished(self, error=False, error_message=""):
        logging.debug(f"on_wipe_finished called (error={error}). is_wiping={self.is_wiping}")
        if not self.is_wiping:
             logging.warning("on_wipe_finished called but not wiping.")
             return

        # Ensure thread quits before potentially deleting worker
        if self.wipe_thread and self.wipe_thread.isRunning():
            logging.debug("Requesting thread quit and waiting...")
            self.wipe_thread.quit()
            if not self.wipe_thread.wait(3000):
                 logging.warning("Thread did not finish quitting gracefully.")

        if self.progress_dialog:
             if not self.progress_dialog._is_finished:
                 self.progress_dialog.mark_finished()
                 if error:
                     final_message = f"Error: {error_message}" if error_message else "Finished with errors."
                     self.progress_dialog.update_progress(self.progress_dialog.progress_bar.value(), final_message)
                 else:
                     self.progress_dialog.update_progress(100, "Finished Successfully")

                 # Make dialog closable manually
                 self.progress_dialog.cancel_button.setText("Close")
                 self.progress_dialog.cancel_button.setEnabled(True)
                 try: self.progress_dialog.cancel_button.clicked.disconnect()
                 except TypeError: pass
                 self.progress_dialog.cancel_button.clicked.connect(self.progress_dialog.accept)

             if not error:
                 logging.debug("Operation successful, accepting progress dialog.")
                 self.progress_dialog.accept() # Auto-close on success

        # Reset state
        self.is_wiping = False
        self.wipe_button.setEnabled(not self.enable_scheduling_checkbox.isChecked())
        self.enable_scheduling_checkbox.setEnabled(True)

        # Clear references (deleteLater handles actual object deletion)
        self.worker = None
        self.wipe_thread = None
        self.progress_dialog = None
        logging.info("Wiping process finished and GUI state reset.")
