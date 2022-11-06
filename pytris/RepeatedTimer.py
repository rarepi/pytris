import threading 
import time
from enum import Enum

class RepeatedTimer(object):
    class State(Enum):
        INITIATED = 0,
        RUNNING = 1,
        STOPPED = 2,
        FINISHED = 4

    def __init__(self, interval: float, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.state = self.State.INITIATED
        self.next_call = time.time()

    def _run(self):
        self.state = self.State.FINISHED
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