import os
import datetime

LOG_DIR = "logs/runs"
os.makedirs(LOG_DIR, exist_ok=True)

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)

    with open(f"{LOG_DIR}/latest.log", "a") as f:
        f.write(line + "\n")
