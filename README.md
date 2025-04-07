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

1.  **Navigate to the project root directory** (where `mediawiper_launcher.py` is located).
2.  **Run the launcher script** with the desired arguments.

### Command-Line Arguments

*   `target_dir`:  The directory to wipe. This is a required argument.
*   `--secure-method {none,random,dod,random_35pass}`: Specify the secure deletion method. 'none' performs a standard delete (default). 'random' uses a single pass of random data. 'dod' uses the DoD 5220.22-M 3-pass method. 'random_35pass' uses 35 passes of random data.
*   `-v` or `--verbose`:  Enable verbose logging (shows more detailed information about the deletion process).
*   `-e` or `--extensions`:  Specify file extensions to delete (comma-separated). If not specified, the script defaults to deleting common video and audio file types (e.g., `.mp4`, `.avi`, `.mp3`, `.wav`, etc. - see `src/code/core/constants.py` for the full default list).

### Examples

*   **Wipe media files from a directory:**

    ```bash
    python mediawiper_launcher.py /path/to/your/directory
    ```

*   **Wipe media files from a directory with verbose logging:**

    ```bash
    python mediawiper_launcher.py /path/to/your/directory -v
    ```

*   **Wipe media files using the DoD 3-pass secure method:**

    ```bash
    python mediawiper_launcher.py /path/to/your/directory --secure-method dod
    ```

*   **Wipe specific file types from a directory:**

    ```bash
    python mediawiper_launcher.py /path/to/your/directory -e ".mp4,.avi,.mov"
    ```

## Project Structure

A brief overview of the project layout:

*   `mediawiper_launcher.py`: The main entry point script to run the application.
*   `src/`: Contains the core source code.
    *   `code/`: Main Python package for the application.
        *   `media_wiper.py`: Handles command-line argument parsing and launches CLI or GUI mode.
        *   `scheduler.py`: Contains the logic for scheduled wiping tasks.
        *   `core/`: Core functionalities like file wiping logic.
        *   `ui/`: GUI components built with PyQt6.
    *   `Icons/`: Application icons.
    *   `version.txt`: Contains version information used for building.

## GUI Usage

To use the GUI, simply run the `mediawiper_launcher.py` script from the project root directory without any command-line arguments:

```bash
python mediawiper_launcher.py
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

**Note:** A pre-built executable for Windows may be available in the `dist/` folder within the project directory.

## Releases

You can download the latest release of MediaWiper from [here](https://github.com/SkyReNewed/MediaWiper/releases).
