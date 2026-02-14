import time
import subprocess
import redis
import psutil  # for process management
import sys
import os

REDIS_HOST = '192.168.200.51'
REDIS_PORT = 6379
REDIS_KEY = 'flappy_bird:game_on'
REDIS_FLAPPY_HEARTBEAT = 'flappy_bird:heartbeat_time'
REDIS_POLLING_INTERVAL_SECONDS = 1 
REDIS_SUBJECT_ID = 'flappy_bird:subject_id'
REDIS_SIMULATOR_RUN = 'flappy_bird:simulator_run'
REDIS_COMMENTS ='flappy_bird:comments'

def is_main_running(proc):
    return proc and proc.poll() is None

def stop_process(proc):
    if is_main_running(proc):
        proc.terminate()
        try:
            proc.wait(timeout=REDIS_POLLING_INTERVAL_SECONDS)
        except subprocess.TimeoutExpired:
            proc.kill()  
            proc.wait()

def run_main_script(subject_id, simulator_run, comments):
    def to_arg(value):
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return str(value)

    args = [
        sys.executable,
        "main.py",
        "--subject-id",
        to_arg(subject_id),
        "--simulator-run",
        to_arg(simulator_run),
        "--comments",
        to_arg(comments),
    ]
    return subprocess.Popen(args, cwd=os.path.dirname(__file__))

def check_redis_flag(r):
    val = r.get(REDIS_KEY)
    if val is not None:
        val = val.decode('utf-8').lower()
        return val in ['1', 'true', 'yes']
    return False

def get_redis_id_flags(r):
    subject_id = r.get(REDIS_SUBJECT_ID)
    simulator_run = r.get(REDIS_SIMULATOR_RUN)
    comments = r.get(REDIS_COMMENTS)

    print(f"Subject ID: {subject_id.decode('utf-8') if subject_id else 'None'}")
    print(f"Simulator Run: {simulator_run.decode('utf-8') if simulator_run else 'None'}")
    print(f"Comments: {comments.decode('utf-8') if comments else 'None'}")

    return subject_id, simulator_run, comments


def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    proc = None

    while True:
        try:
            flag = check_redis_flag(r)

            proc_is_running = is_main_running(proc)

            if proc_is_running:
                r.set(REDIS_FLAPPY_HEARTBEAT, time.time())

            if flag and not proc_is_running:
                print("Flag is True. Starting main.py...")
                subject_id, simulator_run, comments = get_redis_id_flags(r)
                proc = run_main_script(subject_id, simulator_run, comments)
            elif not flag and proc_is_running:
                print("Flag is False. Stopping main.py...")
                stop_process(proc)
                proc = None

            time.sleep(REDIS_POLLING_INTERVAL_SECONDS)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(REDIS_POLLING_INTERVAL_SECONDS)

if __name__ == '__main__':
    main()