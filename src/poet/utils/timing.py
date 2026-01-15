import time

TimerState = tuple[float | None, float]


class Stopwatch:
    # A collection of timers that can be started, paused, resumed and stopped.
    # Use start_timer() to create and start a new timer
    # pause_timer() and resume_timer() do exactly what you think
    # stop_timer() deletes the timer and returns the current value

    def __init__(self) -> None:
        self.timers: dict[str, TimerState] = {}

    def now(self) -> float:
        return time.monotonic()

    def has_time(self, timer_name: str) -> bool:
        return timer_name in self.timers

    def get_time(self, timer_name: str) -> float:
        assert timer_name in self.timers
        ts = self.timers[timer_name]

        if ts[0] is None:  # Timer paused
            return ts[1]
        else:  # Timer running
            return ts[1] + self.now() - ts[0]

    def set_time(self, timer_name: str, time_value: float) -> None:
        self.timers[timer_name] = (None, time_value)

    def start_timer(self, timer_name: str) -> None:
        if timer_name in self.timers:
            start, elapsed = self.timers[timer_name]
            assert start is None
            self.timers[timer_name] = (self.now(), elapsed)
        else:
            self.timers[timer_name] = (self.now(), 0.0)

    def pause_timer(self, timer_name: str) -> float:
        assert timer_name in self.timers
        assert self.timers[timer_name][0] is not None

        elapsed = self.get_time(timer_name)
        self.timers[timer_name] = (None, elapsed)

        return elapsed

    def stop_timer(self, timer_name: str) -> float:
        assert timer_name in self.timers

        elapsed = self.get_time(timer_name)
        del self.timers[timer_name]

        return elapsed
