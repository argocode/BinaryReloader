#!/usr/bin/python

""" Binary Executable Reloader """

from signal import SIGTERM
from subprocess import check_output
from sys import argv
from time import ctime
from time import sleep
import os

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

__author__ = "Jin Pan"
__email__ = "jin@argo.io"

RESTART_DELAY = 0.5  # in seconds


def createProcess(cmd, args=None):
    pid = os.fork()
    if pid == 0:
        os.execvp(cmd, [cmd] + (args or []))
        os._exit(0)
    else:
        return pid


class RespawnHandler(FileSystemEventHandler):

    def __init__(self, cmd, args, pid):
        self.cmd = cmd
        self.args = args
        self.pid = pid


    # TODO: make this robust to different compile patterns
    def on_created(self, event):
        if event.src_path.endswith(self.cmd):
            # some compilers create the executable and rapidly apply
            # modifications, might need to tweak RESTART_DELAY or take a
            # more involved approach
            sleep(RESTART_DELAY)

            msg = "Detected change in %s executable at %s, restarting %s" % (
                self.cmd,
                ctime(),
                self.cmd,
            )
            print "%s\n%s\n%s" % ("*" * len(msg), msg, "*" * len(msg))

            os.kill(self.pid, SIGTERM)
            self.pid = createProcess(self.cmd, self.args)


if __name__ == "__main__":
    assert len(argv) >= 2
    cmd, args = argv[1], argv[2:]
    pid = createProcess(cmd, args)

    # figure out the parent directory of the executable
    process_dir = check_output(["which", cmd]).strip()
    process_dir = '/'.join(process_dir.split('/')[:-1])

    event_handler = RespawnHandler(cmd, args, pid)

    # watch the directory and listen for keyboard interrupts
    observer = Observer()
    observer.schedule(event_handler, process_dir)
    observer.start()
    try:
        while True:
            sleep(0.1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

