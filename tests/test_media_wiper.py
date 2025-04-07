import os
import shutil
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory (project root) to the Python path
# This assumes the tests directory is directly under the project root
# and the media_wiper module is in src/code/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'code')))

# Now import the module
import media_wiper

class TestMediaWiper(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = "test_media_wiper_dir"
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        # Remove the temporary directory after testing
        shutil.rmtree(self.test_dir)

    def test_wipe_media_empty_directory(self):
        # Test that the function handles an empty directory correctly
        media_wiper.wipe_media(self.test_dir)
        self.assertEqual(len(os.listdir(self.test_dir)), 0)

    def test_wipe_media_with_media_files(self):
        # Test that the function correctly deletes media files with the default extensions
        with open(os.path.join(self.test_dir, "test_file.mp4"), "w") as f:
            f.write("test content")
        with open(os.path.join(self.test_dir, "test_file.avi"), "w") as f:
            f.write("test content")
        with open(os.path.join(self.test_dir, "test_file.txt"), "w") as f:
            f.write("test content")

        media_wiper.wipe_media(self.test_dir)
        self.assertEqual(len(os.listdir(self.test_dir)), 1)  # Only the txt file should remain
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "test_file.txt")))

    def test_wipe_media_with_non_media_files(self):
        # Test that the function doesn't delete non-media files
        with open(os.path.join(self.test_dir, "test_file.txt"), "w") as f:
            f.write("test content")

        media_wiper.wipe_media(self.test_dir)
        self.assertEqual(len(os.listdir(self.test_dir)), 1)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "test_file.txt")))

    # Remove the old secure delete test
    # @patch("media_wiper.os.remove")
    # def test_wipe_media_secure_delete(self, mock_remove):
    #     # Test that the secure delete option works correctly (mocking the secure deletion logic)
    #     with open(os.path.join(self.test_dir, "test_file.mp4"), "w") as f:
    #         f.write("test content")
    #
    #     wipe_media(self.test_dir, secure_delete=True) # Old signature
    #     mock_remove.assert_called_once()

    @patch("media_wiper._overwrite_file", return_value=True)
    @patch("media_wiper.os.remove")
    def test_standard_delete(self, mock_remove, mock_overwrite):
        """Test standard deletion (secure_method='none')."""
        file_path = os.path.join(self.test_dir, "test_standard.mp4")
        with open(file_path, "w") as f: f.write("test")

        media_wiper.wipe_media(self.test_dir, secure_method='none')

        mock_overwrite.assert_not_called()
        mock_remove.assert_called_once_with(file_path)

    @patch("media_wiper._overwrite_file", return_value=True)
    @patch("media_wiper.os.remove")
    def test_secure_random(self, mock_remove, mock_overwrite):
        """Test secure deletion with 'random' method."""
        file_path = os.path.join(self.test_dir, "test_random.mp4")
        with open(file_path, "w") as f: f.write("test")

        media_wiper.wipe_media(self.test_dir, secure_method='random')

        mock_overwrite.assert_called_once_with(file_path, passes=1, method='random', log_widget=None)
        mock_remove.assert_called_once_with(file_path)

    @patch("media_wiper._overwrite_file", return_value=True)
    @patch("media_wiper.os.remove")
    def test_secure_dod(self, mock_remove, mock_overwrite):
        """Test secure deletion with 'dod' method."""
        file_path = os.path.join(self.test_dir, "test_dod.mp4")
        with open(file_path, "w") as f: f.write("test")

        media_wiper.wipe_media(self.test_dir, secure_method='dod')

        mock_overwrite.assert_called_once_with(file_path, passes=3, method='dod', log_widget=None)
        mock_remove.assert_called_once_with(file_path)

    @patch("media_wiper._overwrite_file", return_value=True)
    @patch("media_wiper.os.remove")
    def test_secure_random_35pass(self, mock_remove, mock_overwrite): # Renamed test
        """Test secure deletion with 'random_35pass' method."""
        file_path = os.path.join(self.test_dir, "test_random_35pass.mp4") # Renamed test file for clarity
        with open(file_path, "w") as f: f.write("test")

        media_wiper.wipe_media(self.test_dir, secure_method='random_35pass') # Use new method name

        # Check for 35 passes with the correct method name
        mock_overwrite.assert_called_once_with(file_path, passes=35, method='random_35pass', log_widget=None) # Check new method name
        mock_remove.assert_called_once_with(file_path)

    @patch("media_wiper._overwrite_file", return_value=False) # Simulate overwrite failure
    @patch("media_wiper.os.remove")
    def test_secure_overwrite_failure(self, mock_remove, mock_overwrite):
        """Test that os.remove is not called if overwrite fails."""
        file_path = os.path.join(self.test_dir, "test_fail.mp4")
        with open(file_path, "w") as f: f.write("test")

        media_wiper.wipe_media(self.test_dir, secure_method='random')

        mock_overwrite.assert_called_once_with(file_path, passes=1, method='random', log_widget=None)
        mock_remove.assert_not_called() # Crucial check

    def test_wipe_media_custom_extensions(self):
        # Test that the function correctly deletes files with custom extensions specified by the user
        with open(os.path.join(self.test_dir, "test_file.custom"), "w") as f:
            f.write("test content")
        with open(os.path.join(self.test_dir, "test_file.txt"), "w") as f:
            f.write("test content")

        media_wiper.wipe_media(self.test_dir, extensions="custom")
        self.assertEqual(len(os.listdir(self.test_dir)), 1)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "test_file.txt")))

    @patch("media_wiper.logging.debug") # Patching logging within the media_wiper module
    def test_wipe_media_verbose_logging(self, mock_logging_debug):
        # Test that the verbose logging option logs the correct messages
        with open(os.path.join(self.test_dir, "test_file.mp4"), "w") as f:
            f.write("test content")

        media_wiper.wipe_media(self.test_dir, verbose=True)
        mock_logging_debug.assert_called()

if __name__ == "__main__":
    unittest.main()
