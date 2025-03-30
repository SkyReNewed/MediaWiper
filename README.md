# MediaWiper

MediaWiper is a tool to delete media files from different locations.

## Usage

To use MediaWiper, you need to have Python installed on your system.

1.  **Navigate to the directory** where the `media_wiper.py` file is located.
2.  **Run the script** with the desired arguments.

### Command-Line Arguments

*   `target_dir`:  The directory to wipe. This is a required argument.
*   `-s` or `--secure`:  Enable secure deletion (overwrites the file with random data before deleting).
*   `-v` or `--verbose`:  Enable verbose logging (shows more detailed information about the deletion process).
*   `-e` or `--extensions`:  Specify file extensions to delete (comma-separated). If not specified, the script will delete all common video and audio file types.

### Examples

*   **Wipe media files from a directory:**

    ```bash
    python media_wiper.py /path/to/your/directory
    ```

*   **Wipe media files from a directory with verbose logging:**

    ```bash
    python media_wiper.py /path/to/your/directory -v
    ```

*   **Wipe media files from a directory with secure deletion:**

    ```bash
    python media_wiper.py /path/to/your/directory -s
    ```

*   **Wipe specific file types from a directory:**

    ```bash
    python media_wiper.py /path/to/your/directory -e ".mp4,.avi,.mov"
