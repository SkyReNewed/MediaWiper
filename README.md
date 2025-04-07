# MediaWiper

MediaWiper is a tool to delete media files from different locations. It can be used from the command line or through a graphical user interface (GUI).

## Usage

To use MediaWiper, you need to have Python installed on your system along with the following packages:

*   PyQt6 (for the GUI)
*   schedule (for the scheduling feature)

### Installing Dependencies

You can install the required packages using pip:

```bash
pip install PyQt6 schedule
```

## Command-Line Usage

1.  **Navigate to the directory** where the `media_wiper.py` file is located.
2.  **Run the script** with the desired arguments.

### Command-Line Arguments

*   `target_dir`:  The directory to wipe. This is a required argument.
*   `--secure-method {none,random,dod,random_35pass}`: Specify the secure deletion method. 'none' performs a standard delete (default). 'random' uses a single pass of random data. 'dod' uses the DoD 5220.22-M 3-pass method. 'random_35pass' uses 35 passes of random data.
*   `-v` or `--verbose`:  Enable verbose logging (shows more detailed information about the deletion process).
*   `-e` or `--extensions`:  Specify file extensions to delete (comma-separated). If not specified, the script will delete all common video and audio file types.
*   `--name`: Specify the name of the output executable.

### Examples

*   **Wipe media files from a directory:**

    ```bash
    python media_wiper.py /path/to/your/directory
    ```

*   **Wipe media files from a directory with verbose logging:**

    ```bash
    python media_wiper.py /path/to/your/directory -v
    ```

*   **Wipe media files using the DoD 3-pass secure method:**

    ```bash
    python media_wiper.py /path/to/your/directory --secure-method dod
    ```

*   **Wipe specific file types from a directory:**

    ```bash
    python media_wiper.py /path/to/your/directory -e ".mp4,.avi,.mov"
    ```

*   **Specify the name of the output executable:**

    ```bash
    pyinstaller --onefile --noconsole --icon=src/icons/MediaWiper.ico --version-file=src/version.txt --name MediaWiperApp src/code/media_wiper.py
    ```

## GUI Usage

To use the GUI, simply run the `media_wiper.py` script without any command-line arguments:

```bash
python media_wiper.py
```

This will open the MediaWiper GUI, which allows you to:

*   Select the target directory to wipe.
*   Select the secure deletion method (Standard, Single Pass Random, DoD 3 Pass, 35 Pass Random).
*   Enable verbose logging.
*   Specify file extensions to delete.
*   Enable and configure scheduled media wiping.

### Scheduling

The GUI allows you to schedule media wiping tasks to run automatically at a specified interval (daily, weekly, or monthly) and time. To enable scheduling, check the "Enable Scheduling" checkbox and select the desired interval, date, and time. The scheduler will run in the background and automatically wipe media files from the specified directory at the scheduled time.

**Note:** The scheduler requires the `scheduler.py` script to be running in the background. The GUI will automatically start the scheduler when scheduling is enabled.

## Releases

You can download the latest release of MediaWiper from [link to releases].
