import sys
import curses
import pygame
import argparse
from rx.subject import BehaviorSubject

sys.path.insert(0, ".")

from count_down_timer import CountDownTimer, Time
from utils import format_time

pygame.mixer.init()


# Try putting in a logger like https://stackoverflow.com/a/24036294/170243

class TimerWindow:
    def __init__(self, parent_window) -> None:
        self.parent_window_height, self.parent_window_width = parent_window.getmaxyx()
        self.window_width = 40
        self.window_height = 10
        self.window_begin_y = 2
        self.window_begin_x = (self.parent_window_width - self.window_width) // 2 + 2
        self.window = curses.newwin(self.window_height, self.window_width, self.window_begin_y, self.window_begin_x)

    def render_remaining_time(self, t: Time) -> None:
        self.window.clear()
        time_remaining = format_time(t)
        self.window.addstr(time_remaining)
        self.window.refresh()


class ControlsHelpWindow:
    def __init__(self, parent_window) -> None:
        self.parent_window_height, self.parent_window_width = parent_window.getmaxyx()

        self.window_width = self.parent_window_width
        self.window_height = 2
        self.window_begin_y = self.parent_window_height - self.window_height
        self.window_begin_x = 0
        self.window = curses.newwin(self.window_height, self.window_width, self.window_begin_y, self.window_begin_x)

        self.controls_help = {
            "[q]": "Quit",
            "[space]": "Pause | Resume",
            "[s]": "Start"
        }
        self.render_controls_help()

    def render_timer_state(self, timer_state: int) -> None:
        self.window.clear()
        self.render_controls_help()
        self.window.refresh()

    def render_controls_help(self) -> None:
        right_margin_size = 4
        begin_x = 0
        begin_y = 0
        for key, action_text in self.controls_help.items():
            control_help_text = " {} {} ".format(key, action_text)
            self.window.addstr(begin_y, begin_x, control_help_text, curses.A_REVERSE)
            begin_x += len(control_help_text) + right_margin_size
        self.window.refresh()


class CLICountDownTimer:
    def __init__(self, minutes, seconds) -> None:
        self.timer_duration = Time(minutes=minutes, seconds=seconds)
        self.count_down_timer = CountDownTimer(self.timer_duration)
        self.time_remaining_subscription = None
        self.time_depleted_subscription = None

        self.time_depleted = False
        self.time_depleted_sound = pygame.mixer.Sound("sounds/door-bell-sound.wav")
        self.timer_paused = False

        self.timer_paused_event = BehaviorSubject(False)
        self.timer_paused_subscription = None

        self.quit_timer = False

    def init(self, main_window) -> None:
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)

        self.main_window = main_window
        self.main_window_width, self.main_window_height = (curses.COLS, 20)

        self.timer_window = TimerWindow(self.main_window)


        self.timer_window.render_remaining_time(self.timer_duration)
        self.controls_help_window = ControlsHelpWindow(self.main_window)
        self.start()
        self.run_event_loop()


    def start(self) -> None:
        self.time_remaining_subscription = self.count_down_timer.time_remaining.subscribe(
            self.timer_window.render_remaining_time)
        self.time_depleted_subscription = self.count_down_timer.depleted.subscribe(self.on_time_depleted)
        self.timer_paused_subscription = self.timer_paused_event.subscribe(self.on_timer_paused)
        self.run_event_loop()

    def run_event_loop(self) -> None:
        try:
            while not self.quit_timer:
                pressed_key = self.main_window.getkey()
                if pressed_key == "q":
                    self.quit()
                if pressed_key == " " and (self.timer_paused and not self.time_depleted):
                    self.timer_paused_event.on_next(False)
                elif pressed_key == " " and (not self.timer_paused and not self.time_depleted):
                    self.timer_paused_event.on_next(True)
                elif pressed_key == "r" and (self.time_depleted or self.timer_paused):
                    self.restart()
                elif pressed_key == "s" and not (self.timer_paused or self.time_depleted):
                    self.start()
        except:
            self.quit()
        return

    def quit(self) -> None:
        self.dispose_subscriptions()
        self.quit_timer = True

    def on_timer_paused(self, is_timer_paused: bool):
        if is_timer_paused:
            self.pause()
        else:
            self.resume()

    def on_time_depleted(self, is_time_depleted) -> None:
        if is_time_depleted:
            self.time_depleted = True
            self.controls_help_window.render_timer_state(2)
            self.time_depleted_sound.play()

    def pause(self) -> None:
        self.count_down_timer.pause()
        self.timer_paused = True
        self.controls_help_window.render_timer_state(1)

    def resume(self) -> None:
        self.count_down_timer.resume()
        self.timer_paused = False
        self.controls_help_window.render_timer_state(0)

    def restart(self):
        self.dispose_subscriptions()
        self.count_down_timer = CountDownTimer(self.timer_duration)
        self.time_depleted = False
        self.timer_paused = False
        self.start()

    def dispose_subscriptions(self) -> None:
        if self.time_remaining_subscription:
            self.time_remaining_subscription.dispose()
        if self.time_depleted_subscription:
            self.time_depleted_subscription.dispose()
        if self.timer_paused_subscription:
            self.timer_paused_subscription.dispose()


cli_count_down_timer = CLICountDownTimer(1, 0)
curses.wrapper(cli_count_down_timer.init)
