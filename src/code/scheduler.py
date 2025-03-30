import schedule
import time
import argparse
import json
import logging
from media_wiper import wipe_media  # Import the wipe_media function

def main(schedule_info_json=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--schedule_info", type=str, help="JSON string containing schedule information")
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


    # Dynamically schedule the wipe_media function
    if interval == "daily":
        logging.info(f"Scheduling daily wipe at {time_to_run}")
        schedule.every().day.at(time_to_run).do(wipe_media)
    elif interval == "weekly":
        logging.info(f"Scheduling weekly wipe at {time_to_run}")
        schedule.every().week.at(time_to_run).do(wipe_media)
    elif interval == "monthly":
        logging.info(f"Scheduling monthly wipe at {time_to_run}")
        schedule.every().month.at(time_to_run).do(wipe_media)
    # Add other intervals as needed

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
