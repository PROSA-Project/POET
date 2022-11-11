import time

class Stopwatch:
    # A collection of timers that can be started, paused, resumed and stopped.
    # Use start_timer() to create and start a new timer
    # pause_timer() and resume_timer() do exactly what you think
    # stop_timer() deletes the timer and returns the current value

    def __init__(self) -> None:
        self.timers = {}

    def now(self):
        return time.monotonic()

    def has_time(self, timer_name):
        return timer_name in self.timers

    def get_time(self, timer_name):
        assert timer_name in self.timers
        ts = self.timers[timer_name]
        
        if ts[0] is None:   # Timer paused
            return ts[1]
        else:               # Timer running
            return ts[1] + self.now() - ts[0]

    def set_time(self, timer_name, time):
        self.timers[timer_name] = (None, time)
    
    def start_timer(self, timer_name):
        if timer_name in self.timers:
            assert self.timers[timer_name][0] is None
            self.timers[timer_name][0] = self.now()
        else:
            self.timers[timer_name] = (self.now(), 0.0)
            
    def pause_timer(self, timer_name):
        assert timer_name in self.timers
        assert self.timers[timer_name][0] is not None

        time = self.get_time(timer_name)
        self.timers[timer_name] = (None, time)

        return time


    def stop_timer(self, timer_name):
        assert timer_name in self.timers

        time = self.get_time(timer_name)
        del self.timers[timer_name]

        return time