import os
import re
import sys
import threading
import time

import requests
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

JOIN_RE = r"(.*) joined the game"
LEFT_RE = r"(.*) left the game"


def _send_webhook(webhook_url, payload):
    requests.post(webhook_url, json=payload, timeout=3)


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, filename, webhook_url):
        self.filename = filename
        self.file = open(  # pylint: disable=consider-using-with
            self.filename, "r", encoding="utf-8"
        )
        # Go to the end of the file
        self.file.seek(0, 2)

        self.webhook_url = webhook_url

    def on_modified(self, event):
        if not event.is_directory and event.src_path == self.filename:
            line = self.file.readline()
            while line:
                print(line, end="")
                line = self.file.readline()

                match = re.match(JOIN_RE, line)
                payload = None
                if match:
                    print("[LOGIN] joined the game", match.group(1))
                    payload = {
                        "username": "Minecraft Watch",
                        "content": f"{match.group(1)} がサーバーに入りました",
                    }

                match = re.match(LEFT_RE, line)
                if match:
                    print("[LOGIN] left the game", match.group(1))
                    payload = {
                        "username": "Minecraft Watch",
                        "content": f"{match.group(1)} がサーバーから退出しました",
                    }

                if payload:
                    # _send_webhook in another thread
                    thr = threading.Thread(
                        target=_send_webhook, args=(self.webhook_url, payload)
                    )
                    thr.start()

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

    event_handler = FileChangeHandler(filename, webhook_url)
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
