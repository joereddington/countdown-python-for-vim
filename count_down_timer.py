from collections import namedtuple
import math 
import pygame
import time
import os
import rx
from rx.core import Observable
from rx.subject import BehaviorSubject
from rx.operators import do_action, map


Time = namedtuple("Time", ["minutes", "seconds"])


class CountDownTimer:
    def __init__(self, duration: Time) -> None:
        self._minutes = min(duration.minutes, 59)
        self._remaining_minutes = self._minutes

        self._seconds = min(duration.seconds, 59)
        self._remaining_seconds = self._seconds + 1

        self._tick_size = 1

        self.depleted = BehaviorSubject(False)

    @property
    def time_remaining(self) -> Observable:

        return rx.timer(0.0, period=1).pipe(
            do_action(lambda _, this=self: this._tick()),
            map(lambda _, this=self: Time(this._remaining_minutes, this._remaining_seconds))
        )



    def _tick(self) -> None:
        is_time_depleted = self.depleted.value
        if not is_time_depleted:
            if self._remaining_minutes == 0 and self._remaining_seconds == 0:
                self.depleted.on_next(True)
                return
            if self._remaining_minutes == 0 and self._remaining_seconds == 10:
                pygame.mixer.music.load('sounds/drown.wav')
                pygame.mixer.music.play(1)
            if  self._remaining_seconds == 0:
                self._remaining_minutes -= 1
                self._remaining_seconds = 59
                return

            
            if self._remaining_seconds % 3 == 0: 
                #Joe code
                self.set_clock_from_inbox_age()
                pass
            self._remaining_seconds -= self._tick_size

    def set_clock_from_inbox_age(self):
                age_of_inbox_in_seconds=int(time.time()-os.path.getmtime("../inbox.md"))
                seconds_for_the_clock=600-age_of_inbox_in_seconds 
                self._remaining_minutes = math.floor(seconds_for_the_clock/60)
                self._remaining_seconds = seconds_for_the_clock-60*self._remaining_minutes

    def pause(self) -> None:
        self._tick_size = 0

    def resume(self) -> None:
        self._tick_size = 1
