import os
import sys
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, filename):
        self.filename = filename
        self.file = open(  # pylint: disable=consider-using-with
            self.filename, "r", encoding="utf-8"
        )
        # Go to the end of the file
        self.file.seek(0, 2)

    def on_modified(self, event):
        if not event.is_directory and event.src_path == self.filename:
            line = self.file.readline()
            while line:
                print(line, end="")
                line = self.file.readline()

    def close(self):
        self.file.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python mcjava.py <filename>")
        return

    filename = sys.argv[1]
    webhook_url = os.environ.get("WEBHOOK_URL")
    if webhook_url is None:
        print("WEBHOOK_URL environment variable is not set")
        return

    event_handler = FileChangeHandler(filename)
    observer = Observer()
    observer.schedule(event_handler, path=filename, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    finally:
        event_handler.close()
    observer.join()


if __name__ == "__main__":
    main()
