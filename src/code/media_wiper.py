import os
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def wipe_media(target_dir):
    """
    Wipes media files from the specified directory.
    """
    logging.info(f"Wiping media files from: {target_dir}")

    # Define media file extensions
    video_extensions = ['.mp4', '.avi', '.flv', '.wmv', '.mov', '.webm', '.mkv', '.f4v', '.vob', '.ogg', '.gifv', '.amv', '.mpg', '.mp2', '.mpeg', '.mpe', '.mpv', '.m4v', '.3gp']
    audio_extensions = ['.wav', '.aiff', '.mp3', '.acc', '.wma', '.ogg', '.flac']

    for root, _, files in os.walk(target_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_extension = os.path.splitext(file)[1].lower()

            if file_extension in video_extensions or file_extension in audio_extensions:
                try:
                    # Perform secure deletion (optional)
                    # shutil.rmtree(file_path) # For directories
                    os.remove(file_path) # For files
                    logging.info(f"Deleted: {file_path}")
                except Exception as e:
                    logging.error(f"Error deleting {file_path}: {e}")

    logging.info("Media wiping complete.")

if __name__ == "__main__":
    target_directory = input("Enter the target directory to wipe: ")
    wipe_media(target_directory)
