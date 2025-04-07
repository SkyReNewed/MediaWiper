"""
Progress dialog window for the MediaWiper GUI.
"""

from PyQt6.QtWidgets import QDialog, QProgressBar, QLabel, QPushButton, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal # pyqtSlot is in QtCore in PyQt6
from PyQt6 import QtCore # Import QtCore explicitly for pyqtSlot decorator

class ProgressDialog(QDialog):
    # Signal to request cancellation from the main GUI thread
    cancel_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wiping Progress")
        self.setModal(True) # Make it modal
        self.setMinimumWidth(400)
        # Prevent closing via 'X' button while running initially
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)

        self.progress_bar = QProgressBar(self)
        self.status_label = QLabel("Starting...", self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.request_cancel)

        layout = QVBoxLayout(self)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)
        self.progress_bar.setValue(0)
        self._is_finished = False # Flag to prevent double close/accept

    # Use the decorator for slots in PyQt6
    @QtCore.pyqtSlot(int, str)
    def update_progress(self, value, message):
        """Updates the progress bar and status label."""
        if self._is_finished: return # Don't update if already finished
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        # QApplication.processEvents() # Avoid this here; let the main event loop handle updates

    def request_cancel(self):
        """Handles the cancel button click."""
        self.status_label.setText("Cancellation requested...")
        self.cancel_button.setEnabled(False) # Disable button after click
        self.cancel_requested.emit() # Signal the main window/controller

    def closeEvent(self, event):
        """Prevents closing via 'X' button while the operation is running."""
        if not self._is_finished:
            # Optionally ask for confirmation before cancelling
            # reply = QMessageBox.question(self, 'Cancel Operation',
            #                              "Are you sure you want to cancel the wiping process?",
            #                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            #                              QMessageBox.StandardButton.No)
            # if reply == QMessageBox.StandardButton.Yes:
            #      self.request_cancel()
            # event.ignore()
            self.request_cancel() # Directly request cancel if X is clicked
            event.ignore() # Ignore the close event initially
        else:
            event.accept() # Allow closing if finished

    def mark_finished(self):
        """Marks the dialog as finished, allowing it to be closed normally."""
        self._is_finished = True
        # Allow closing via 'X' button now
        self.setWindowFlags(Qt.WindowType.Dialog) # Restore default flags
        self.show() # Re-show to apply flag changes if needed

        self.cancel_button.setEnabled(False) # Keep cancel disabled
        # Optionally change button text to "Close" and connect to accept
        # self.cancel_button.setText("Close")
        # try: self.cancel_button.clicked.disconnect()
        # except TypeError: pass
        # self.cancel_button.clicked.connect(self.accept)
        # self.cancel_button.setEnabled(True)
