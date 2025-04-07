"""
Core file wiping logic for MediaWiper, including the CLI version.
"""

import os
import shutil
import logging

# Import constants from the same package level
from .constants import FILE_CATEGORIES, CHUNK_SIZE

def _overwrite_file(file_path, passes, method, log_widget=None):
    """Helper function to overwrite a file securely."""
    try:
        file_size = os.path.getsize(file_path)
        logging.debug(f"Overwriting {file_path} ({file_size} bytes) using method '{method}' ({passes} passes)...")
        # log_widget is primarily for GUI, might be None in CLI context
        if log_widget:
            # Check if log_widget is a GUI widget or just for logging
            # Assuming it might be used for direct logging if not None
            try:
                log_widget.append(f"Overwriting {file_path} ({file_size} bytes) using method '{method}' ({passes} passes)...")
            except AttributeError: # If it's not a widget with append
                 logging.info(f"Overwriting {file_path} ({file_size} bytes) using method '{method}' ({passes} passes)...")


        with open(file_path, 'wb') as f:
            for p in range(passes):
                logging.debug(f"Pass {p+1}/{passes} for {file_path}")
                f.seek(0) # Go to the beginning for each pass
                bytes_written = 0
                while bytes_written < file_size:
                    chunk = b''
                    # Determine data pattern for the pass
                    if method == 'random':
                        chunk = os.urandom(min(CHUNK_SIZE, file_size - bytes_written))
                    elif method == 'dod':
                        if p == 0: # Pass 1: Zeros
                            chunk = bytes(min(CHUNK_SIZE, file_size - bytes_written))
                        elif p == 1: # Pass 2: Ones
                            chunk = b'\xFF' * min(CHUNK_SIZE, file_size - bytes_written)
                        else: # Pass 3: Random
                            chunk = os.urandom(min(CHUNK_SIZE, file_size - bytes_written))
                    elif method == 'random_35pass':
                        # 35 passes using random data
                        chunk = os.urandom(min(CHUNK_SIZE, file_size - bytes_written))
                    else: # Default to random if method unknown (should not happen)
                         chunk = os.urandom(min(CHUNK_SIZE, file_size - bytes_written))

                    f.write(chunk)
                    bytes_written += len(chunk)
                f.flush()
                os.fsync(f.fileno()) # Ensure data is written to disk
        logging.debug(f"Finished overwriting {file_path}")
        if log_widget:
            try:
                log_widget.append(f"Finished overwriting {file_path}")
            except AttributeError:
                 logging.info(f"Finished overwriting {file_path}")
        return True
    except Exception as e:
        logging.error(f"Error overwriting {file_path}: {e}")
        if log_widget:
            try:
                log_widget.append(f"Error overwriting {file_path}: {e}")
            except AttributeError:
                 logging.error(f"Error overwriting {file_path}: {e}") # Log error if append fails
        return False

def wipe_media(target_dir, secure_method='none', verbose=False, extensions=None,
               include_video=False, include_audio=False, include_images=False,
               include_documents=False, log_widget=None):
    """
    Wipes media files from the specified directory (CLI Version / Core Logic).
    secure_method: 'none', 'random', 'dod', 'random_35pass'
    log_widget: Optional GUI widget for logging (used by older GUI code, None in CLI).
    """
    if verbose:
        # Ensure logger level is set appropriately if called directly
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        # Ensure logger level is INFO if not verbose
        logging.getLogger().setLevel(logging.INFO)


    logging.info(f"Starting media wiping from: {target_dir}")
    if log_widget:
        try:
            log_widget.append(f"Starting media wiping from: {target_dir}")
        except AttributeError:
            logging.info(f"Starting media wiping from: {target_dir}") # Log if not a widget

    # Build the list of extensions to wipe
    extensions_to_wipe = set()
    if include_video:
        extensions_to_wipe.update(FILE_CATEGORIES["Video"])
    if include_audio:
        extensions_to_wipe.update(FILE_CATEGORIES["Audio"])
    if include_images:
        extensions_to_wipe.update(FILE_CATEGORIES["Images"])
    if include_documents:
        extensions_to_wipe.update(FILE_CATEGORIES["Documents"])

    if extensions:
        custom_extensions = [ext.strip() for ext in extensions.split(',')]
        for ext in custom_extensions:
            if ext: # Avoid adding empty strings if there are trailing commas etc.
                extensions_to_wipe.add(ext if ext.startswith('.') else '.' + ext)

    media_extensions = list(extensions_to_wipe)

    if not media_extensions:
        logging.warning("No file extensions specified for wiping. Aborting.")
        if log_widget:
            try:
                log_widget.append("No file extensions specified for wiping. Aborting.")
            except AttributeError:
                 logging.warning("No file extensions specified for wiping. Aborting.")
        return

    logging.info(f"Targeting extensions: {', '.join(media_extensions)}")
    if log_widget:
        try:
            log_widget.append(f"Targeting extensions: {', '.join(media_extensions)}")
        except AttributeError:
            logging.info(f"Targeting extensions: {', '.join(media_extensions)}")

    files_processed_count = 0
    files_deleted_count = 0
    errors_encountered = 0

    try:
        for root, _, files in os.walk(target_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_extension = os.path.splitext(file)[1].lower()

                if file_extension in media_extensions:
                    files_processed_count += 1
                    try:
                        if secure_method == 'none':
                            os.remove(file_path)
                            logging.debug(f"Deleted (standard): {file_path}")
                            if log_widget:
                                try:
                                    log_widget.append(f"Deleted (standard): {file_path}")
                                except AttributeError: pass # Ignore if not widget
                            files_deleted_count += 1
                        else:
                            logging.info(f"Securely deleting ({secure_method}): {file_path}")
                            if log_widget:
                                try:
                                    log_widget.append(f"Securely deleting ({secure_method}): {file_path}")
                                except AttributeError: pass

                            # Pass None to _overwrite_file if log_widget isn't suitable
                            overwrite_log_target = None # Assume None unless log_widget is valid
                            if log_widget and hasattr(log_widget, 'append'):
                                overwrite_log_target = log_widget

                            overwrite_successful = _overwrite_file(file_path, passes={'random': 1, 'dod': 3, 'random_35pass': 35}.get(secure_method, 1), method=secure_method, log_widget=overwrite_log_target)

                            if overwrite_successful:
                                os.remove(file_path)
                                logging.debug(f"Deleted (secure, {secure_method}): {file_path}")
                                if log_widget:
                                    try:
                                        log_widget.append(f"Deleted (secure, {secure_method}): {file_path}")
                                    except AttributeError: pass
                                files_deleted_count += 1
                            else:
                                logging.error(f"Skipping deletion of {file_path} due to overwrite error.")
                                if log_widget:
                                    try:
                                        log_widget.append(f"Skipping deletion of {file_path} due to overwrite error.")
                                    except AttributeError: pass
                                errors_encountered += 1

                    except Exception as e:
                        logging.error(f"Error processing {file_path}: {e}")
                        if log_widget:
                            try:
                                log_widget.append(f"Error processing {file_path}: {e}")
                            except AttributeError: pass
                        errors_encountered += 1
    except Exception as e:
        logging.error(f"Error during media wiping walk: {e}")
        if log_widget:
            try:
                log_widget.append(f"Error during media wiping walk: {e}")
            except AttributeError: pass
        errors_encountered += 1

    completion_message = f"Media wiping complete. Processed: {files_processed_count}, Deleted: {files_deleted_count}, Errors: {errors_encountered}."
    logging.info(completion_message)
    if log_widget:
        try:
            log_widget.append(completion_message)
        except AttributeError: pass
