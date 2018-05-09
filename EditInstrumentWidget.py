"""
qcodes/instrument/base.py -> line 263
There u can find a set function for setting paramater defined by "name" to a value defined by "value"
"""

from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QLabel, QShortcut, QDesktopWidget
from PyQt5.QtCore import Qt, pyqtSlot

import sys

from Helpers import *
from ThreadWorker import Worker, progress_func, print_output, thread_complete
from EditInstrumentParametersWidget import EditInstrumentParameterWidget
from qcodes.instrument_drivers.QuTech.IVVI import IVVI


class EditInstrumentWidget(QWidget):

    def __init__(self, instruments, dividers, active, thread_pool,
                 tracked_parameter=None, parent=None, instrument_name=""):
        """
        Constructor for EditInstrumentWidget window

        :param instruments: dictionary containing all instruments created in this instance of GUI
        :param dividers: dict of all divider created in this instance of GUI
        :param active: list of all opened instruments windows (one must be able to remove self from that list)
        :param thread_pool: thread managing pool of threads (shared with mainWindow)
        :param tracked_parameter: used for live mode of the instrument, only updates value of this parameter
        :param instrument_name: Name of an instrument to be edited
        :param parent: specify object that created this widget
        """
        super(EditInstrumentWidget, self).__init__()
        self.parent = parent

        # a dict of all instruments that have been created so far
        self.instruments = instruments
        # a dict of all dividers that have been created so far (to be able to display them if any of them is attached to
        # currently observed instrument
        self.dividers = dividers
        # a list of EditInstrumentWidgets that are currently opened (to be able to remove self from that list)
        self.active = active
        # shared thread pool to be able to run longer actions in separate threads
        self.thread_pool = thread_pool
        # name of the instrument that is currently being edited
        self.instrument_name = instrument_name
        # instance of the instrument that is currently being edited
        self.instrument = self.instruments[instrument_name]

        # keep track of workers messing with this window
        self.live = False
        self.worker = None
        self.tracked_parameter = tracked_parameter

        # references to textboxes, because they need to be accessed often, to updated the values if live monitoring of
        # the instrument is turned on
        self.textboxes = {}
        self.textboxes_real_values = {}
        self.textboxes_divided_values = {}

        # references to buttons for editing inner parameters of each instrument parameter
        self.inner_parameter_btns = {}

        self.init_ui()
        self.show()

    """""""""""""""""""""
    User interface
    """""""""""""""""""""
    def init_ui(self):
        """
        Hello

        :return: NoneType
        """
        # define initial position and size of this widget
        # position is defined in relative size to the size of the monitor
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        window_height = len(self.instrument.parameters)*30 + 200
        self.setGeometry((width - 600), int(0.05*height), 580, window_height)
        self.setMinimumSize(320, 260)
        # define title and icon of the widget
        self.setWindowTitle("Edit " + self.instrument_name.upper() + " instrument")
        self.setWindowIcon(QtGui.QIcon("img/osciloscope_icon.png"))

        # show the name of the instrument that is being edited
        label = QLabel("Name:", self)
        label.move(30, 30)
        self.instrument_name_txtbox = QLineEdit(self.instrument_name, self)
        self.instrument_name_txtbox.move(80, 30)
        self.instrument_name_txtbox.setDisabled(True)

        # button to start live updating of the parameters of this instrument
        self.go_live_btn = QPushButton("Go live", self)
        self.go_live_btn.move(460, 30)
        self.go_live_btn.resize(90, 40)
        self.go_live_btn.clicked.connect(self.toggle_live)

        label = QLabel("Original", self)
        label.move(260, 60)
        label = QLabel("Applied", self)
        label.move(310, 60)

        if isinstance(self.instrument, IVVI):
            params_to_show = {}
            for i in range(self.instrument._numdacs):
                name = "dac" + str(i + 1)
                params_to_show[name] = getattr(self.instrument, name)
        else:
            params_to_show = self.instrument.parameters


        # create a row for each of the parameters of this instrument with fields for displaying original and applied
        # values, also field for editing, and buttons for geting and seting a value
        start_y = 80
        for name, parameter in params_to_show.items():
            label = QLabel(name, self)
            label.move(30, start_y)
            label.show()

            self.inner_parameter_btns[name] = QPushButton("Edit " + name, self)
            self.inner_parameter_btns[name].move(140, start_y)
            self.inner_parameter_btns[name].resize(110, 20)
            self.inner_parameter_btns[name].clicked.connect(self.make_edit_parameter(name))

            if is_numeric(self.instrument.get(name)):
                val = round(float(self.instrument.get(name)), 3)
            else:
                val = self.instrument.get(name)
            self.textboxes_real_values[name] = QLineEdit(str(val), self)
            self.textboxes_real_values[name].move(255, start_y)
            self.textboxes_real_values[name].resize(50, 20)
            self.textboxes_real_values[name].setDisabled(True)
            if str(parameter) in self.dividers:
                self.textboxes_divided_values[name] = QLineEdit(str(round(self.dividers[str(parameter)].get_raw(), 3)), self)
                self.textboxes_divided_values[name].resize(50, 20)
                self.textboxes_divided_values[name].move(310, start_y)
                self.textboxes_divided_values[name].setDisabled(True)
            self.textboxes[name] = QLineEdit(str(val), self)
            self.textboxes[name].move(365, start_y)
            self.textboxes[name].resize(80, 20)
            if hasattr(parameter, "set"):
                set_value_btn = QPushButton("Set", self)
                set_value_btn.move(460, start_y)
                set_value_btn.resize(40, 20)
                set_value_btn.clicked.connect(self.make_set_parameter(name))
            if hasattr(parameter, "get"):
                get_value_btn = QPushButton("Get", self)
                get_value_btn.move(510, start_y)
                get_value_btn.resize(40, 20)
                get_value_btn.clicked.connect(lambda checked, parameter_name=name: self.update_parameters_data(parameter_name))
            start_y += 25

        # U can read right ?
        set_all_to_zero_btn = QPushButton("All zeroes", self)
        set_all_to_zero_btn.move(480, start_y + 20)
        set_all_to_zero_btn.clicked.connect(self.call_worker(self.set_all_to_zero))

        # Sets all to values currently displayed in the text boxes that are editable
        set_all_btn = QPushButton("SET ALL", self)
        set_all_btn.move(390, start_y + 20)
        # set_all_btn.clicked.connect(self.call_worker(self.set_all))
        set_all_btn.clicked.connect(self.set_all)

        # gets all parameters and updates the displayed values
        set_all_btn = QPushButton("GET ALL", self)
        set_all_btn.move(390, start_y + 50)
        set_all_btn.clicked.connect(self.call_worker(self.update_parameters_data))

        # if u click this button u get a house and a car on Bahamas, also your partner suddenly becomes the most
        # attractive person in the world, in addition to this you get a Nobel prize for whatever u want ... Easy life
        ok_btn = QPushButton("Close", self)
        ok_btn.move(480, start_y + 50)
        ok_btn.clicked.connect(self.close)

        close_shortcut = QShortcut(QtGui.QKeySequence(Qt.Key_Escape), self)
        close_shortcut.activated.connect(self.close)

    """""""""""""""""""""
    Data manipulation
    """""""""""""""""""""
    def make_set_parameter(self, parameter):
        """
        Function factory that createc function for each of the set buttons. Takes in name of the instrument parameter
        and passes it to the inner function. Function returns newly created function.

        :param parameter: name of the parameter that is being set
        :return: function that sets the parameter
        """

        def set_parameter():
            """
            Fetches the data from textbox belonging to the parameter (data set by user) and sets the parameter value
            to that data. Also implements some data validation

            Added handling with dividers attached (add detailed explanation)

            :return: NoneType
            """
            # full name is composed of the instrument name and parameter name (Example: IVVI_dac1)
            full_name = str(self.instrument.parameters[parameter])
            try: # look into qcodes/utils/validators, think of a way
                value = float(self.textboxes[parameter].text())
                if full_name in self.dividers:
                    self.dividers[full_name].set_raw(value)
                else:
                    self.instrument.set(parameter, value)
            except Exception as e:
                show_error_message("Warning", str(e))
            else:
                self.update_parameters_data()
        return set_parameter

    def make_edit_parameter(self, parameter):
        """
        Function factory for creating functions that open new window for editing parameters of an instrument

        :param parameter: name of the parameter to be edited
        :return: reference to a function "edit_instrument"
        """
        def edit_parameter():
            self.edit_instrument_parameters = EditInstrumentParameterWidget(self.instruments, self.instrument,
                                                                            parameter, self.dividers, parent=self)
            self.edit_instrument_parameters.show()

        return edit_parameter

    def update_parameters_data(self, name=None):
        """
        Updates values of all parameters after a change has been made. Implements data validation (has to be number)
        Also used to "Get all", well, cause it gets all ... :/

        If name is passed update only value of that single parameter

        :param name: if this parameter is set to something(string) get the value of only that single parameter
        :return: NoneType
        """
        if name is not None:
            full_name = str(self.instrument.parameters[name])
            if full_name in self.dividers:
                self.textboxes[name].setText(str(round(self.dividers[full_name].get_raw(), 3)))
            else:
                if is_numeric(self.instrument.get(name)):
                    self.textboxes[name].setText(str(round(self.instrument.get(name), 3)))
                else:
                    self.textboxes[name].setText(str(self.instrument.get(name)))
            if is_numeric(self.instrument.get(name)):
                self.textboxes_real_values[name].setText(str(round(self.instrument.get(name), 3)))
            else:
                self.textboxes_real_values[name].setText(str(self.instrument.get(name)))
        else:
            for name, textbox in self.textboxes.items():
                full_name = str(self.instrument.parameters[name])
                if full_name in self.dividers:
                    textbox.setText(str(round(self.dividers[full_name].get_raw(), 3)))
                else:
                    if is_numeric(self.instrument.get(name)):
                        textbox.setText(str(round(float(self.instrument.get(name)), 3)))
                    else:
                        textbox.setText(str(self.instrument.get(name)))
            for name, textbox in self.textboxes_real_values.items():
                if is_numeric(self.instrument.get(name)):
                    textbox.setText(str(round(float(self.instrument.get(name)), 3)))
                else:
                    if is_numeric(self.instrument.get(name)):
                        textbox.setText(str(round(float(self.instrument.get(name)), 3)))
                    else:
                        textbox.setText(str(self.instrument.get(name)))
            self.update_divided_values()

    def single_update(self):
        # used to live update only a single parameter that is being swept by the currently running loop
        if self.tracked_parameter is not None:
            self.update_parameters_data(self.tracked_parameter)

    def update_divided_values(self):
        for name, textbox in self.textboxes_divided_values.items():
            # get values from the divider
            textbox.setText(str(round(self.dividers[str(self.instrument.parameters[name])].get_raw(), 3)))

    def set_all_to_zero(self):
        """
        Set value of all numeric type parameters to be zero

        :return: NoneType
        """
        # some instruments already have this method implemented, so why bother, on the other hand, some instruments
        # dont have it so i have to implement it anyway, wow, im so smart
        if hasattr(self.instrument, "set_dacs_zero"):
            self.instrument.set_dacs_zero()
        else:
            for name, parameter in self.instrument.parameters.items():
                if is_numeric(self.instrument.get(name)):
                    if name[0:3] == "dac" and len(name) == (4 or 5):
                        self.instrument.set(name, 0)
        self.update_parameters_data()

    def set_all(self):
        """
        Sets and updates displayed values for all parameters at the same time (if multiple parameters were edited)

        :return: NoneType
        """
        for name, parameter in self.instrument.parameters.items():
            full_name = str(parameter)
            if is_numeric(self.instrument.get(name)):
                try:
                    value = float(self.textboxes[name].text())
                    if full_name in self.dividers:
                        self.dividers[full_name].set_raw(value)
                    else:
                        self.instrument.set(name, value)
                    print(name)
                except Exception as e:
                    show_error_message("Warning", str(e))
                    continue
                else:
                    self.setStatusTip("Parameter value changed to: " + str(value))
        self.update_parameters_data()

    """""""""""""""""""""
    Helper functions
    """""""""""""""""""""
    def call_worker(self, func):
        """
        Function factory for instantiating worker objects that run a certain function in a separate thread

        :param func:
        :return:
        """
        def instantiate_worker():
            # creata a new worker, False meaning that it is not a looping worker, it only does its thing once
            worker = Worker(func, False)
            worker.signals.result.connect(print_output)
            worker.signals.finished.connect(thread_complete)
            worker.signals.progress.connect(progress_func)

            self.thread_pool.start(worker)

        return instantiate_worker

    def closeEvent(self, a0: QtGui.QCloseEvent):
        # overriding close method to remove self from list of active windows, obviously if one is closed, one is no
        # longer active, is that obvious only to me ? It should be to everyone right ? Right ?
        self.active.remove(self)

    def toggle_live(self):
        # if the widget is currently in live mode, turn of the live mode and kill all+delete all workers.
        if self.live:
            self.worker.stop_requested = True
            self.go_live_btn.setText("Go live")
            self.worker = None
            for tb in self.textboxes:
                self.textboxes[tb].setDisabled(False)
            self.live = False
        # if the widget is currently in non-live mode, go live mode, create worker, and start it
        else:
            self.go_live_btn.setText("STOP")
            if len(self.parent.actions):
                self.tracked_parameter = self.parent.actions[-1].sweep_values.name
            for tb in self.textboxes:
                self.textboxes[tb].setDisabled(True)
            self.worker = Worker(self.single_update, True)
            self.thread_pool.start(self.worker)
            self.live = True


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = EditInstrumentWidget({})
    sys.exit(app.exec_())
