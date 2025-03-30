import os
import shutil
import unittest
from unittest.mock import patch
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from media_wiper import wipe_media

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
        wipe_media(self.test_dir)
        self.assertEqual(len(os.listdir(self.test_dir)), 0)

    def test_wipe_media_with_media_files(self):
        # Test that the function correctly deletes media files with the default extensions
        with open(os.path.join(self.test_dir, "test_file.mp4"), "w") as f:
            f.write("test content")
        with open(os.path.join(self.test_dir, "test_file.avi"), "w") as f:
            f.write("test content")
        with open(os.path.join(self.test_dir, "test_file.txt"), "w") as f:
            f.write("test content")

        wipe_media(self.test_dir)
        self.assertEqual(len(os.listdir(self.test_dir)), 1)  # Only the txt file should remain
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "test_file.txt")))

    def test_wipe_media_with_non_media_files(self):
        # Test that the function doesn't delete non-media files
        with open(os.path.join(self.test_dir, "test_file.txt"), "w") as f:
            f.write("test content")

        wipe_media(self.test_dir)
        self.assertEqual(len(os.listdir(self.test_dir)), 1)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "test_file.txt")))

    @patch("media_wiper.os.remove")
    def test_wipe_media_secure_delete(self, mock_remove):
        # Test that the secure delete option works correctly (mocking the secure deletion logic)
        with open(os.path.join(self.test_dir, "test_file.mp4"), "w") as f:
            f.write("test content")

        wipe_media(self.test_dir, secure_delete=True)
        mock_remove.assert_called_once()

    def test_wipe_media_custom_extensions(self):
        # Test that the function correctly deletes files with custom extensions specified by the user
        with open(os.path.join(self.test_dir, "test_file.custom"), "w") as f:
            f.write("test content")
        with open(os.path.join(self.test_dir, "test_file.txt"), "w") as f:
            f.write("test content")

        wipe_media(self.test_dir, extensions="custom")
        self.assertEqual(len(os.listdir(self.test_dir)), 1)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "test_file.txt")))

    @patch("media_wiper.logging.debug")
    def test_wipe_media_verbose_logging(self, mock_logging_debug):
        # Test that the verbose logging option logs the correct messages
        with open(os.path.join(self.test_dir, "test_file.mp4"), "w") as f:
            f.write("test content")

        wipe_media(self.test_dir, verbose=True)
        mock_logging_debug.assert_called()

if __name__ == "__main__":
    unittest.main()
