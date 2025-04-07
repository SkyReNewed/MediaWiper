import schedule
import time
import argparse
import json
import logging
import threading
from media_wiper import wipe_media

def main(schedule_info_json=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--schedule_info", type=str, help="JSON string containing schedule information")
    parser.add_argument("--wipe_args", type=str, help="JSON string containing wipe arguments")
    args = parser.parse_args()

    if args.schedule_info:
        schedule_info = json.loads(args.schedule_info)
        interval = schedule_info["interval"]
        time_to_run = schedule_info["time"]
        logging.info(f"Schedule info: interval={interval}, time_to_run={time_to_run}")
    else:
        # Provide default values for testing
        interval = "daily"
        time_to_run = "00:00"
        logging.info(f"Using default schedule info: interval={interval}, time_to_run={time_to_run}")

    # Extract wipe arguments
    if args.wipe_args:
        wipe_args = json.loads(args.wipe_args)
        target_dir = wipe_args["target_dir"]
        target_dir = wipe_args.get("target_dir") # Use .get() for safety
        secure_method = wipe_args.get("secure_method", False)
        verbose = wipe_args.get("verbose", False)
        extensions = wipe_args.get("extensions")
        include_video = wipe_args.get("include_video", False)
        include_audio = wipe_args.get("include_audio", False)
        include_images = wipe_args.get("include_images", False)
        include_documents = wipe_args.get("include_documents", False)
        logging.info(f"Wipe args: target_dir={target_dir}, secure_method={secure_method}, verbose={verbose}, extensions={extensions}, "
                     f"include_video={include_video}, include_audio={include_audio}, include_images={include_images}, include_documents={include_documents}")
    else:
        target_dir = None
        secure_method = "none" # Default to standard delete
        verbose = False
        extensions = None
        include_video = False
        include_audio = False
        include_images = False
        include_documents = False
        logging.info("Using default wipe arguments")

    # Dynamically schedule the wipe_media function using the new parameter name
    # Define the job function with all arguments
    job = lambda: wipe_media(target_dir=target_dir, secure_method=secure_method, verbose=verbose, extensions=extensions,
                             include_video=include_video, include_audio=include_audio, include_images=include_images,
                             include_documents=include_documents)

    # Create a new thread for the wipe_media function
    wipe_thread = threading.Thread(target=job)
    # Start the thread
    wipe_thread.start()

    # Dynamically schedule the job
    if interval == "daily":
        schedule.every().day.at(time_to_run).do(job)
    elif interval == "weekly":
        logging.info(f"Scheduling weekly wipe at {time_to_run}")
        schedule.every().week.at(time_to_run).do(job)
    elif interval == "monthly":
        logging.info(f"Scheduling monthly wipe at {time_to_run}")
        schedule.every().month.at(time_to_run).do(job)
    # Add other intervals as needed

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
