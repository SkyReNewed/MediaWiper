#!/usr/bin/env python
"""
Main launcher script for the MediaWiper application.

This script ensures the package structure is correctly handled
and runs the main application logic (GUI or CLI).
Run this script from the project root directory.
"""

import sys
import os
import logging

# --- Path Setup ---
# Add the 'src' directory to sys.path to allow importing the 'code' package
# Gets the directory where this launcher script resides (project root)
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')

if src_path not in sys.path:
    sys.path.insert(0, src_path)
    logging.debug(f"Added '{src_path}' to sys.path")

# --- Application Execution ---
if __name__ == "__main__":
    # Configure basic logging for the launcher itself (optional)
    # The main app configures logging further based on args
    logging.basicConfig(level=logging.INFO, format='Launcher: %(levelname)s - %(message)s')
    logging.info("MediaWiper Launcher starting...")

    try:
        # Import the main function from the application's entry point within the package
        from src.code.media_wiper import main as mediawiper_main

        # Call the application's main function
        mediawiper_main()

    except ImportError as e:
        logging.exception(f"Failed to import application modules: {e}")
        print(f"Error: Failed to import application modules. Ensure 'src' directory is present. Details: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logging.exception(f"An unexpected error occurred during application execution: {e}")
        print(f"Error: An unexpected error occurred. {e}", file=sys.stderr)
        sys.exit(1)

    logging.info("MediaWiper Launcher finished.")
    sys.exit(0) # Explicitly exit with success code if main() finishes without sys.exit
