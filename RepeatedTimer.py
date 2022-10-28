import threading 
import time

class RepeatedTimer(object):
  def __init__(self, interval: float, function, *args, **kwargs):
    self._timer = None
    self.interval = interval
    self.function = function
    self.args = args
    self.kwargs = kwargs
    self.is_running = False
    self.is_stopped = False
    self.next_call = time.time()
    self.start()

  def _run(self):
    self.is_running = False
    self.start()
    self.function(*self.args, **self.kwargs)

  def start(self):
    if not self.is_running and not self.is_stopped:
      self.next_call += self.interval
      self._timer = threading.Timer(self.next_call - time.time(), self._run)
      self._timer.start()
      self.is_running = True

  def restart(self):
    self.is_stopped = False
    self.start()

  def stop(self):
    self._timer.cancel()
    self.is_running = False
    self.is_stopped = True