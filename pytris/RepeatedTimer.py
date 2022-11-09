import threading 
import time
from enum import Enum

class RepeatedTimer(object):
    class State(Enum):
        INITIATED = 0,
        RUNNING = 1,
        PAUSED = 2,
        STOPPED = 3

    def __init__(self, interval: float, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.state = self.State.INITIATED
        self.next_call = time.time()

    def _run(self):
        self.state = self.State.STOPPED
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.state is self.State.RUNNING:
            self.next_call += self.interval
            self._timer = threading.Timer(self.next_call - time.time(), self._run)
            self._timer.start()
            self.state = self.State.RUNNING

    def stop(self):
        if not self._timer is None:
            self._timer.cancel()
        self.state = self.State.STOPPED

    def pause(self):
        self.stop()
        self.pause_time = time.time()
        self.state = self.State.PAUSED

    def resume(self):
        if self.is_paused():
            # add passed time since pause minus one interval, which will be readded by start()
            self.next_call += time.time() - self.pause_time - self.interval
        self.start()

    def is_running(self):
        return self.state is self.State.RUNNING

    def is_paused(self):
        return self.state is self.State.PAUSED

    def is_stopped(self):
        return self.state is self.State.STOPPED