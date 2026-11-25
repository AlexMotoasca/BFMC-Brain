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
        # Sender to control steering (-25.0 to +25.0 degrees, depending on calibration)
        self.steerSender = messageHandlerSender(self.queuesList, SteerMotor)

        # Subscribe to StateChange so this only runs when you switch to AUTO mode
        self.stateSubscriber = messageHandlerSubscriber(
            self.queuesList, StateChange, "lastOnly", True
        )
        self.auto_active = False

    def thread_work(self):
        # Check if the dashboard switched the car's mode
        state_msg = self.stateSubscriber.receive()
        if state_msg is not None:
            self.auto_active = (str(state_msg).upper() == "AUTO")
            if not self.auto_active:
                self.steerSender.send("0.0")  # Center wheels when leaving AUTO

        if not self.auto_active:
            time.sleep(0.1)
            return

        # Center wheels when leaving AUTO
        self.steerSender.send("0")

        # 1. Steer right for 2 seconds
        self.steerSender.send("20")
        time.sleep(2.0)

        # 2. Steer left for 2 seconds
        self.steerSender.send("-20")
        time.sleep(2.0)

        # 3. Center wheels for 1 second
        self.steerSender.send("0")
        time.sleep(1.0)