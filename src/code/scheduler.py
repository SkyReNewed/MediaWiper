import schedule
import time
import argparse
import json
import logging
from media_wiper import wipe_media  # Import the wipe_media function

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
        secure_delete = wipe_args["secure_delete"]
        verbose = wipe_args["verbose"]
        extensions = wipe_args["extensions"]
        logging.info(f"Wipe args: target_dir={target_dir}, secure_delete={secure_delete}, verbose={verbose}, extensions={extensions}")
    else:
        target_dir = None
        secure_delete = False
        verbose = False
        extensions = None
        logging.info("Using default wipe arguments")

    # Dynamically schedule the wipe_media function
    if interval == "daily":
        logging.info(f"Scheduling daily wipe at {time_to_run}")
        schedule.every().day.at(time_to_run).do(wipe_media, target_dir=target_dir, secure_delete=secure_delete, verbose=verbose, extensions=extensions)
    elif interval == "weekly":
        logging.info(f"Scheduling weekly wipe at {time_to_run}")
        schedule.every().week.at(time_to_run).do(wipe_media, target_dir=target_dir, secure_delete=secure_delete, verbose=verbose, extensions=extensions)
    elif interval == "monthly":
        logging.info(f"Scheduling monthly wipe at {time_to_run}")
        schedule.every().month.at(time_to_run).do(wipe_media, target_dir=target_dir, secure_delete=secure_delete, verbose=verbose, extensions=extensions)
    # Add other intervals as needed

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
