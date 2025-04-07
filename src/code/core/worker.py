"""
Worker thread class for performing media wiping asynchronously for the GUI.
"""

import os
import logging
import time
from PyQt6.QtCore import QObject, pyqtSignal, QThread # Removed QApplication import

# Import from sibling modules within the 'core' package
from .constants import FILE_CATEGORIES
from .wiper import _overwrite_file # Import the helper function

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
        self.log_widget = log_widget # Reference to the GUI log widget
        self._is_cancelled = False # Flag for cancellation

    def cancel(self):
        """Sets the cancellation flag."""
        logging.info("Cancellation requested for wipe worker.")
        self._is_cancelled = True

    def run(self):
        """Performs the wiping operation, emitting signals for progress."""
        try:
            # Note: Setting logger level here might affect global logging if not careful.
            # Consider passing logger instance or configuring per-module.
            if self.verbose:
                logging.getLogger().setLevel(logging.DEBUG)

            logging.info(f"Worker starting media wiping from: {self.target_dir}")
            # Safely update GUI log widget if provided (using invokeMethod is safer but more complex)
            if self.log_widget and hasattr(self.log_widget, 'append'):
                 # For simplicity, direct append is used, assuming it's handled safely by Qt/GUI thread
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
                if self.log_widget and hasattr(self.log_widget, 'append'):
                    self.log_widget.append("No file extensions specified.")
                self.error_occurred.emit("No file extensions specified for wiping.")
                return # Exit run method

            logging.info(f"Targeting extensions: {', '.join(media_extensions)}")
            if self.log_widget and hasattr(self.log_widget, 'append'):
                 self.log_widget.append(f"Targeting extensions: {', '.join(media_extensions)}")

            # --- First Pass: Scan for files to count total ---
            files_to_wipe = []
            self.progress_updated.emit(0, "Scanning for files...")
            # QApplication.processEvents() # Avoid calling this from worker thread

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
                    # Yield control if scan is very long (optional)
                    # QThread.msleep(1) # Small sleep to allow event processing
            except Exception as e:
                if self._is_cancelled:
                    logging.info("Wiping cancelled during scan error handling.")
                    self.finished.emit()
                    return
                logging.error(f"Error scanning directory {self.target_dir}: {e}")
                self.error_occurred.emit(f"Error scanning directory: {e}")
                return

            total_files = len(files_to_wipe)
            logging.info(f"Found {total_files} files to wipe.")
            if self.log_widget and hasattr(self.log_widget, 'append'):
                 self.log_widget.append(f"Found {total_files} files to wipe.")

            if total_files == 0:
                self.progress_updated.emit(100, "No matching files found to wipe.")
                self.finished.emit()
                return

            # --- Second Pass: Wipe files ---
            processed_files = 0
            for file_path in files_to_wipe:
                if self._is_cancelled:
                    logging.info("Wiping cancelled.")
                    progress_percent = int((processed_files / total_files) * 100) if total_files > 0 else 0
                    self.progress_updated.emit(progress_percent, "Wiping cancelled.")
                    self.finished.emit()
                    return

                processed_files += 1
                progress_percent = int((processed_files / total_files) * 100)
                display_filename = os.path.basename(file_path)
                if len(display_filename) > 50: display_filename = display_filename[:23] + "..." + display_filename[-24:]
                status_message = f"Wiping ({processed_files}/{total_files}): {display_filename}"
                self.progress_updated.emit(progress_percent, status_message)
                logging.debug(status_message)

                try:
                    if self.secure_method == 'none':
                        os.remove(file_path)
                        logging.debug(f"Deleted (standard): {file_path}")
                    else:
                        logging.info(f"Securely deleting ({self.secure_method}): {file_path}")
                        # Pass None for log_widget to _overwrite_file as it's mainly for CLI/direct use
                        overwrite_successful = _overwrite_file(file_path, passes={'random': 1, 'dod': 3, 'random_35pass': 35}.get(self.secure_method, 1), method=self.secure_method, log_widget=None)

                        if overwrite_successful:
                            os.remove(file_path)
                            logging.debug(f"Deleted (secure, {self.secure_method}): {file_path}")
                        else:
                            logging.error(f"Skipping deletion of {file_path} due to overwrite error.")
                            if self.log_widget and hasattr(self.log_widget, 'append'):
                                self.log_widget.append(f"Skipping deletion of {file_path} due to overwrite error.")
                            # Optionally emit specific error for this file
                            # self.error_occurred.emit(f"Overwrite failed: {os.path.basename(file_path)}")

                except Exception as e:
                    logging.error(f"Error processing {file_path}: {e}")
                    if self.log_widget and hasattr(self.log_widget, 'append'):
                        self.log_widget.append(f"Error processing {file_path}: {e}")
                    # Decide whether to emit error and stop or continue
                    # self.error_occurred.emit(f"Error processing {os.path.basename(file_path)}: {e}")
                    # continue # Or return based on desired behavior

                # Yield control periodically (optional, use with caution)
                # QThread.msleep(1)

            # Final check for cancellation before completion signals
            if self._is_cancelled:
                 logging.info("Wiping cancelled before final completion signal.")
                 self.finished.emit()
                 return

            logging.info("Media wiping complete.")
            if self.log_widget and hasattr(self.log_widget, 'append'):
                 self.log_widget.append("Media wiping complete.")
            self.progress_updated.emit(100, "Wiping complete.")
            self.finished.emit()

        except Exception as e:
            # Catch any unexpected errors during the run
            logging.error(f"Unexpected error during media wiping worker: {e}", exc_info=True)
            # Ensure finished is emitted even after unexpected error if possible
            try:
                self.error_occurred.emit(f"An unexpected error occurred: {e}")
            except Exception as sig_e:
                 logging.error(f"Failed to emit error signal: {sig_e}")
            finally:
                 # Try to emit finished regardless
                 try:
                      self.finished.emit()
                 except Exception as fin_e:
                      logging.error(f"Failed to emit finished signal after error: {fin_e}")
