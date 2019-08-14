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

        self.thread = threading.Thread(target=self.listen)

        self.thread.start()

        self.expired = time.time() + timeout

        self.running = True

    def write_line(self, line):
        self.lines += line

    def stop(self):
        self.running = False

    def send(self):
        if len(self.lines):
            requests.post(self.url, data=self.lines)

            self.lines = ""

    def listen(self):
        while self.running:
            current_time = time.time()

            if current_time > self.expired:
                self.send()

                self.expired = current_time + self.timeout

        self.send()

async def read_stream(stream, streamer):
    while True:
        line = await stream.readline()

        if line:
            streamer.write_line(line)

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

def start(script_path, project_path, url, timeout):
    command_line = "python " + script_path + " --project " + project_path + " --name experiment --allow_resume True"

    os.popen("chmod a+x " + script_path)

    execute(command_line, Streamer(url, int(timeout)))

def main(*args):
    script_path = args[0][1]

    project_path = args[0][2]

    url = args[0][3]

    timeout = args[0][4]

    start(script_path, project_path, url, timeout)

if __name__ == '__main__':
    main(sys.argv)
