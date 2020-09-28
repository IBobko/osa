import threading
import uLogging
import datetime
from collections import namedtuple

TaskResult = namedtuple("TaskResult", ["task_item", "result", "duration"])


def threadpool_safe_acquiriable(target_method):

    def safe_acquire(self, *args, **kwargs):
        try:
            return target_method(self, *args, **kwargs)
        except (Exception, KeyboardInterrupt) as main_exc:
            uLogging.warn("Exception happen in threading pool itself, terminating")
            self.terminateLocked()
            raise main_exc

    return safe_acquire

class ThreadPool(object):

    def __init__(self, workerFun):
        self.workerFun = workerFun
        self.inputQ = []		# task item queue
        self.outputQ = []		# result queue
        self.lock = threading.Lock()
        self.condition = threading.Condition(lock=self.lock)
        self.tasks_number = 0		# number of tasks in process now
        self.terminateFlag = False
        self.threads_count = 0
        self.threads = []
        self.results = []

    def poolWorkerFun(self):
        uLogging.debug('pool worker started')
        i = self.get()
        while i != None:
            uLogging.debug('processing {item}'.format(item=i))
            res = None

            start_time = datetime.datetime.now()
            try:
                res = self.workerFun(i)
            except (Exception, KeyboardInterrupt), e:
                res = e

            self.task_done(item=i, result=res, duration=datetime.datetime.now() - start_time)
            uLogging.debug('{item} processed'.format(item=i))
            i = self.get()
        uLogging.debug('pool worker finished')

    def start(self, threads_count):

        self.threads_count = threads_count
        self.threads = []
        self.results = []

        for x in range(self.threads_count):
            t = threading.Thread(target=self.poolWorkerFun)
            t.start()
            self.threads.append(t)

    @threadpool_safe_acquiriable
    def put(self, item):
        uLogging.debug('Putting {item} in the thread pool'.format(item=item))
        self.condition.acquire()
        self.inputQ.append(item)
        self.tasks_number += 1
        self.condition.notifyAll()
        self.condition.release()

    # get next item for execution
    @threadpool_safe_acquiriable
    def get(self):
        self.condition.acquire()
        try:
            if self.terminateFlag:
                return None
            while not self.inputQ:
                self.condition.wait(1.0)  # we may miss notify() when processing result. so wake up regularly
                if self.terminateFlag:	  # if we woken up by terminate()
                    return None
            i = self.inputQ.pop(0)
            return i
        finally:
            self.condition.release()

    @threadpool_safe_acquiriable
    def task_done(self, item, result, duration):
        self.condition.acquire()
        task_result = TaskResult(task_item=item, result=result, duration=duration)
        self.outputQ.append(task_result)
        self.tasks_number -= 1
        self.condition.notifyAll()
        self.condition.release()

    # returns None if overall job is finished: all tasks processed and result returned
    @threadpool_safe_acquiriable
    def get_result(self):
        res = None
        self.condition.acquire()

        if self.outputQ:
            res = self.outputQ.pop(0)
            self.results.append(res)
        else:
            if self.tasks_number:		# some tasks still not processed

                while not self.outputQ:
                    self.condition.wait(1.0)

                res = self.outputQ.pop(0)
                self.results.append(res)

        self.condition.release()
        return res

    def get_all_non_empty_results(self):

        while self.get_result() is not None:
            pass

        return self.results

    @threadpool_safe_acquiriable
    def terminate(self):
        uLogging.debug("Terminating thread pool")
        self.condition.acquire()
        self.terminateLocked()
        uLogging.debug("Thread pool is terminated")

    def release_locked(self):
        uLogging.debug("Releasing condition lock")
        try:
            self.condition.notifyAll()
            self.condition.release()
        except RuntimeError:
            uLogging.debug("the condition lock was not acquired")
        except threading.ThreadError:
            uLogging.debug("the condition lock was not locked")

    def terminateLocked(self):
        uLogging.debug("Terminating locked workers in pool")
        self.terminateFlag = True
        self.release_locked()

        for t in self.threads:
            t.join()


__all__ = ["ThreadPool"]
