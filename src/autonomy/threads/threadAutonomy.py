import time
from src.templates.threadwithstop import ThreadWithStop
from src.utils.messages.allMessages import SteerMotor, StateChange
from src.utils.messages.messageHandlerSender import messageHandlerSender
from src.utils.messages.messageHandlerSubscriber import messageHandlerSubscriber
from src.utils.logConfig import get_logger


class threadAutonomy(ThreadWithStop):
    def __init__(self, queuesList, debugging=False):
        super().__init__()
        self.queuesList = queuesList
        self.debugging = debugging
        self.logger = get_logger("Autonomy")

        # Sender to control steering (-250 to +250, in tenths of a degree)
        self.steerSender = messageHandlerSender(self.queuesList, SteerMotor)

        # Subscribe to StateChange so this only runs in AUTO mode
        self.stateSubscriber = messageHandlerSubscriber(
            self.queuesList, StateChange, "lastOnly", True
        )
        self.auto_active = False
        self.current_angle = 0

    def _check_auto_mode(self):
        """Poll StateChange and return whether AUTO mode is still active."""
        state_msg = self.stateSubscriber.receive()
        if state_msg is not None:
            self.auto_active = (str(state_msg).upper() == "AUTO")
            if not self.auto_active:
                self.current_angle = 0
                self.steerSender.send("0")
        return self.auto_active

    def _smooth_steer(self, target_angle, step=10, delay=0.05):
        """Ramp steering smoothly from current_angle to target_angle."""
        while self.current_angle != target_angle:
            if not self._check_auto_mode():
                return False

            diff = target_angle - self.current_angle
            if abs(diff) <= step:
                self.current_angle = target_angle
            else:
                self.current_angle += step if diff > 0 else -step

            self.steerSender.send(str(self.current_angle))
            time.sleep(delay)

        return True

    def _wait(self, duration, interval=0.05):
        """Sleep in short increments so mode changes respond immediately."""
        end_time = time.time() + duration
        while time.time() < end_time:
            if not self._check_auto_mode():
                return False
            time.sleep(interval)
        return True

    def thread_work(self):
        if not self._check_auto_mode():
            time.sleep(0.1)
            return

        # 1. Smoothly steer right to +20.0 deg, hold 1s
        if not self._smooth_steer(200, step=10, delay=0.04):
            return
        if not self._wait(1.0):
            return

        # 2. Smoothly steer left to -20.0 deg, hold 1s
        if not self._smooth_steer(-200, step=10, delay=0.04):
            return
        if not self._wait(1.0):
            return

        # 3. Smoothly return to center (0.0 deg), hold 1s
        if not self._smooth_steer(0, step=10, delay=0.04):
            return
        self._wait(1.0)