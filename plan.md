# Plan for MediaWiper Development

## 1. Choose the Core Language
*   [x] Python
*   [ ] C++
*   [ ] Go
*   [ ] Rust

## 2. Implement Core Logic
*   [x] Refactor the batch file logic in Python using the `os` and `shutil` modules.

## 3. Implement CLI
*   [x] Use `argparse` or `Click` to create a command-line interface for advanced users.

## 4. Create GUI
*   [x] Use `Tkinter`, `PyQt`, or `Kivy` to create a graphical user interface for easier interaction.

## 5. Implement Scheduling
*   [ ] Use the `schedule` library to schedule automatic media wiping tasks.
*   [ ] Users should be able to schedule future wipes in an intuitive manner (date picker and time picker).
*   [ ] users should be provided with next schedule date and time as per their selection
*   [ ] Users should be able to schedule recurring wipe schedules such as one time half hour, hourly, daily, weekly 
*   [ ] logs should be maintained when scheduled wipe begins and ends and errors along the way.
*   [ ] a dialog box should be presented to the user when they are scheduling wipes as a confirmation

## 6. Implement Reporting and Logging
*   [ ] Use the `logging` module to log deletion activities and generate reports.

## 7. Implement Advanced Features
*   [ ] Add support for file preview.
*   [ ] Add support for network shares.
*   [ ] Add support for cloud storage.
*   [ ] Add a "restore" feature to recover accidentally deleted files (if possible).

## 8. Potential Rust Migration
*   [ ] Evaluate performance bottlenecks in the Python implementation.
*   [ ] Rewrite performance-critical sections in Rust.
*   [ ] Integrate the Rust code with the Python application.
