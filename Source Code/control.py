import time
import subprocess
import redis
import psutil  # for process management
import sys
import os

REDIS_HOST = '192.168.200.51'
REDIS_PORT = 6379
REDIS_KEY = 'game_on'

def is_main_running(proc):
    return proc and proc.poll() is None

def stop_process(proc):
    if is_main_running(proc):
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()  
            proc.wait()

def run_main_script():
    return subprocess.Popen([sys.executable, "main.py"], cwd=os.path.dirname(__file__))

def check_redis_flag(r):
    val = r.get(REDIS_KEY)
    if val is not None:
        val = val.decode('utf-8').lower()
        return val in ['1', 'true', 'yes']
    return False

def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    proc = None

    while True:
        try:
            flag = check_redis_flag(r)

            if flag and not is_main_running(proc):
                print("Flag is True. Starting main.py...")
                proc = run_main_script()
            elif not flag and is_main_running(proc):
                print("Flag is False. Stopping main.py...")
                stop_process(proc)
                proc = None

            time.sleep(10)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)

if __name__ == '__main__':
    main()