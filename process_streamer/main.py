import os

import sys

import shlex

import asyncio

import time

import threading

import requests

class Streamer:
    def __init__(self, url, timeout):
        self.url = url

        self.timeout = timeout

        self.lines = ""

        self.expired = time.time() + timeout

        self.running = True

        self.thread = threading.Thread(target=self.listen)

        self.thread.start()

    def write_line(self, line):
        self.lines += line

    def stop(self):
        self.running = False

    def send(self):
        if len(self.lines):
            print(self.lines)

            requests.post(self.url, data=self.lines.encode('utf-8'))

            self.lines = ""

    def listen(self):
        while self.running:
            current_time = time.time()

            if current_time > self.expired:
                self.send()

                self.expired = current_time + self.timeout

            time.sleep(1)

        self.send()

async def read_stream(stream, streamer):
    while True:
        line = await stream.readline()

        if line:
            streamer.write_line(line.decode("utf-8"))

        else:
            streamer.stop()

            break

async def stream_subprocess(cmd, streamer):
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)

    await asyncio.wait([read_stream(process.stdout, streamer)])

    return await process.wait()

def execute(command_line, streamer):
    loop = asyncio.get_event_loop()

    rc = loop.run_until_complete(stream_subprocess(shlex.split(command_line), streamer))

    loop.close()

    return rc

def start(script_path, project_path, url, timeout, fold, timer):
    command_line = "python " + script_path + " --project " + project_path + " --name experiment --allow_resume True"

    if not (fold == "folds_argument"):
        command_line += " --folds " + fold

    if not (timer == "timer_argument"):
        command_line += " --time " + timer

    os.popen("chmod a+x " + script_path)

    execute(command_line, Streamer(url, int(timeout)))

def main(*args):
    script_path = args[0][1]

    project_path = args[0][2]

    url = args[0][3]

    timeout = args[0][4]

    fold = args[0][5]

    timer = args[0][6]

    print(url)

    start(script_path, project_path, url, timeout, fold, timer)

if __name__ == '__main__':
    main(sys.argv)
