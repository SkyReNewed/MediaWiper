"""
Main entry point for the MediaWiper application.
Handles command-line arguments or launches the GUI.
"""

import os
import sys
import argparse
import logging
from PyQt6.QtWidgets import QApplication

# Configure logging (can be configured further based on args)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Relative Imports from within the 'code' package ---
try:
    from .ui.main_window import MediaWiperGUI
    # Import the CLI function and rename it to avoid conflict if needed
    from .core.wiper import wipe_media as wipe_media_cli
except ImportError as e:
    logging.error(f"Import Error: {e}. Ensure the application structure is correct and running from the intended directory.")
    # Attempt absolute import as fallback if running script directly for testing? Risky.
    # from ui.main_window import MediaWiperGUI
    # from core.wiper import wipe_media as wipe_media_cli
    sys.exit(f"Failed to import necessary modules. Please check installation/structure. Error: {e}")


if __name__ == "__main__":
    # --- Command-Line Argument Handling ---
    parser = argparse.ArgumentParser(
        description="Wipe media files from a directory. Run without arguments for GUI.",
        add_help=False # Add help manually to avoid conflict with GUI launch
    )
    # Add arguments for CLI mode
    parser.add_argument("target_dir", nargs='?', help="The directory to wipe media files from (required for CLI mode).")
    parser.add_argument(
        "--secure-method",
        choices=['none', 'random', 'dod', 'random_35pass'],
        default='none',
        help="Secure deletion method ('none', 'random', 'dod', 'random_35pass'). Default: 'none'."
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable detailed (debug) logging.")
    parser.add_argument("-e", "--extensions", help="Custom file extensions to delete (e.g., '.log,.tmp').")
    parser.add_argument("--include-video", action="store_true", help="Include standard video files.")
    parser.add_argument("--include-audio", action="store_true", help="Include standard audio files.")
    parser.add_argument("--include-images", action="store_true", help="Include standard image files.")
    parser.add_argument("--include-documents", action="store_true", help="Include standard document files.")
    # Add explicit help argument
    parser.add_argument(
        '-h', '--help', action='help', default=argparse.SUPPRESS,
        help='Show this help message and exit.'
    )

    # Parse known args first to see if it's likely a CLI call
    # Use parse_known_args to avoid errors if extra args are passed (e.g., by Qt)
    args, unknown = parser.parse_known_args()

    # Determine if running in CLI mode
    # Simple check: if target_dir is provided, assume CLI.
    # More robust: check if any CLI-specific args were given beyond the script name.
    is_cli_run = args.target_dir is not None

    if is_cli_run:
        # --- CLI Mode ---
        logging.info("Running MediaWiper in CLI mode.")

        # Configure logging level based on CLI args
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.INFO)

        # Validate target directory for CLI mode
        if not os.path.isdir(args.target_dir):
             print(f"Error: Target directory '{args.target_dir}' not found or is not a directory.", file=sys.stderr)
             sys.exit(1)

        try:
            # Run the imported CLI wipe function
            wipe_media_cli(
                args.target_dir,
                secure_method=args.secure_method,
                verbose=args.verbose,
                extensions=args.extensions,
                include_video=args.include_video,
                include_audio=args.include_audio,
                include_images=args.include_images,
                include_documents=args.include_documents,
                log_widget=None # No GUI log widget in CLI mode
            )
            logging.info("CLI execution finished.")
            sys.exit(0) # Exit successfully after CLI run

        except Exception as e:
             logging.error(f"Error during CLI execution: {e}", exc_info=True)
             print(f"An unexpected error occurred: {e}", file=sys.stderr)
             sys.exit(1) # Exit with error code

    else:
        # --- GUI Mode ---
        logging.info("Starting MediaWiper GUI.")
        # Note: QApplication might modify sys.argv, which is why parse_known_args was used.
        app = QApplication(sys.argv)
        gui = MediaWiperGUI()
        gui.show()
        sys.exit(app.exec())
