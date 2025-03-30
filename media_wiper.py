import os
import shutil
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def wipe_media(target_dir, secure_delete=False, verbose=False, extensions=None):
    """
    Wipes media files from the specified directory.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logging.info(f"Wiping media files from: {target_dir}")

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
                        os.remove(file_path)
                    else:
                        os.remove(file_path)
                        logging.debug(f"Deleted: {file_path}")
                except Exception as e:
                    logging.error(f"Error deleting {file_path}: {e}")

    logging.info("Media wiping complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wipe media files from a directory.")
    parser.add_argument("target_dir", help="The directory to wipe.")
    parser.add_argument("-s", "--secure", action="store_true", help="Enable secure deletion.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging.")
    parser.add_argument("-e", "--extensions", help="Specify file extensions to delete (comma-separated).")

    args = parser.parse_args()

    wipe_media(args.target_dir, args.secure, args.verbose, args.extensions)
