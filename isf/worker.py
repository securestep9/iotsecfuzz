import datetime
import logging
from enum import Enum
from threading import Thread
from util import async_raise as async_raise

logger = logging.getLogger('isf')


class State(Enum):
    IDLE = 'Idle'
    RUNNING = 'Running',
    FINISHED = 'Finished'


class Worker:

    def __init__(self, module, input, callback=None):
        self.module = module
        self.input = input
        self.state = State.IDLE
        self.output = []
        self.start_time = None
        self.thread = None
        self.exc_info = None
        self.callback = callback

    def _run(self):
        try:
            for value in self.module.start(**self.input):
                self.output.append(value)
        except KeyboardInterrupt:
            logger.debug('Module %s stopped due to KeyboardInterrupt'
                         % self.module.qualified_name)
        except Exception as e:
            self.exc_info = e
            logger.debug('Module %s finished with an exception'
                         % self.module.qualified_name,
                         exc_info=e)
        else:
            logger.debug('Module %s exited normally'
                         % self.module.qualified_name)
        finally:
            self.state = State.FINISHED
            if self.callback:
                self.callback(self)

    def start(self):
        if self.state != State.IDLE:
            logger.debug('Cannot start worker %s in state %s' % (
                self.module.qualified_name, self.state.name))
            return
        self.state = State.RUNNING
        self.start_time = datetime.datetime.now()
        self.thread = Thread(target=self._run)
        logger.debug('Starting background worker for module %s'
                     % self.module.qualified_name)
        self.thread.start()

    def stop(self):
        logger.debug('Force-stopping module %s' % self.module.qualified_name)
        async_raise(self.thread, KeyboardInterrupt)
