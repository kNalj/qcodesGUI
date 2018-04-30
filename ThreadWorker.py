from PyQt5.QtCore import pyqtSlot, QRunnable, QObject, pyqtSignal
import traceback
import sys
import time


class Worker(QRunnable):
    """
    This is a worker thread that inherits from QRunnable to be able to handle thread setup and maintenance

    """

    def __init__(self, func, repeat, *args, **kwargs):
        """
        This is a constructor for the worker class, it runs any function passed to it as a separate thread

        :param func: pointer to the function to be ran in a separate thread
        :param args: arguments (for passing to run() method)
        :param kwargs: key word arguments (for passing to run() method)
        """
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        self.stop_requested = False
        if repeat == True:
            self.repeat = True
        else:
            self.repeat = False

        # Add the callback to our kwargs
        # kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        """
        Initialise the runner function with passed args, kwargs.
        """
        # Retrieve args/kwargs here; and fire processing using them

        # if what we want is to repeat this action until a stop is called then True will be passed
        if self.repeat:
            # stop requested is a signal used and checked on each iteration of this loop to check if the loop execution
            # should proceed
            while not self.stop_requested:
                try:
                    result = self.func(*self.args, **self.kwargs)
                except:
                    traceback.print_exc()
                    exctype, value = sys.exc_info()[:2]
                    self.signals.error.emit((exctype, value, traceback.format_exc()))
                else:
                    self.signals.result.emit(result)  # Return the result of the processing
                finally:
                    self.signals.finished.emit()  # Done
                # this time sleep determines how long to wait before continuing with the loop
                time.sleep(3)
            else:
                print("Stop has been requested !")
        # otherwise if we dont want it to loop, but rather execute just once, then False will be passed and this code
        # will get executed
        else:
            try:
                result = self.func(*self.args, **self.kwargs)
            except:
                traceback.print_exc()
                exctype, value = sys.exc_info()[:2]
                self.signals.error.emit((exctype, value, traceback.format_exc()))
            else:
                self.signals.result.emit(result)  # Return the result of the processing
            finally:
                self.signals.finished.emit()  # Done


class WorkerSignals(QObject):
    """
       Defines the signals available from a running worker thread.

       Supported signals are:

       finished
           No data

       error
           `tuple` (exctype, value, traceback.format_exc() )

       result
           `object` data returned from processing, anything

       progress
           `int` indicating % progress

    """
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


def progress_func(progress):
    """
    Helper function for thread worker

    :param progress: integer representing percentage of the job that is already done
    :return: NoneType
    """
    print("%d%% done" % progress)


def print_output(output):
    """
    Helper function for thread worker

    :param output: String returned (if any) by function that was processed in a thread
    :return: NoneType
    """
    if output is not None:
        print(output)


def thread_complete():
    """
    Helper function for thread worker, prints out this message after finishing the thread job.

    :return: NoneType
    """
    print("Thread executed successfully")
