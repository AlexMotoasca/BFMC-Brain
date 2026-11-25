from src.templates.workerprocess import WorkerProcess
from src.autonomy.threads.threadAutonomy import threadAutonomy


class processAutonomy(WorkerProcess):
    def __init__(self, queueList, ready_event=None, debugging=False):
        self.queuesList = queueList
        self.debugging = debugging
        super().__init__(self.queuesList, ready_event)

    def _init_threads(self):
        autonomyThread = threadAutonomy(self.queuesList, self.debugging)
        self.threads.append(autonomyThread)