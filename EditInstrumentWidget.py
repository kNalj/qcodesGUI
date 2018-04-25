"""
qcodes/instrument/base.py -> line 263
There u can find a set function for setting paramater defined by "name" to a value defined by "value"
"""

from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QLabel, QShortcut, QDesktopWidget
from PyQt5.QtCore import Qt, pyqtSlot
from AttachDividersWidget import DividerWidget
from PyQt5 import QtGui

import sys

from Helpers import *
from ThreadWorker import Worker, progress_func, print_output, thread_complete
from EditInstrumentParametersWidget import EditInstrumentParameterWidget


class EditInstrumentWidget(QWidget):

    def __init__(self, instruments, dividers, thread_pool, parent=None, instrument_name=""):
        """
        Constructor for EditInstrumentWidget window

        :param instrument_name: Name of an instrument to be edited
        :param parent: specify object that created this widget
        """
        super(EditInstrumentWidget, self).__init__()
        self.parent = parent

        self.instruments = instruments
        self.dividers = dividers
        self.thread_pool = thread_pool
        self.instrument_name = instrument_name
        self.instrument = self.instruments[instrument_name]
        self.division = 1

        self.textboxes = {}
        self.textboxes_real_values = {}
        self.textboxes_divided_values = {}

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
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        window_height = len(self.instrument.parameters)*30 + 100
        self.setGeometry((width - 500), int(0.05*height), 480, window_height)
        self.setMinimumSize(320, 260)
        self.setWindowTitle("Edit " + self.instrument_name.upper() + " instrument")
        self.setWindowIcon(QtGui.QIcon("img/osciloscope_icon.png"))

        label = QLabel("Name:", self)
        label.move(30, 30)
        self.instrument_name_txtbox = QLineEdit(self.instrument_name, self)
        self.instrument_name_txtbox.move(80, 30)
        self.instrument_name_txtbox.setDisabled(True)

        """label = QLabel("Division:", self)
        label.move(310, 30)
        self.division_textbox = QLineEdit("1", self)
        self.division_textbox.move(360, 30)
        self.division_textbox.resize(40, 20)
        self.apply_division = QPushButton("Apply", self)
        self.apply_division.move(410, 30)
        self.apply_division.resize(40, 20)
        self.apply_division.clicked.connect(self.update_divided_values)"""

        label = QLabel("Original", self)
        label.move(160, 60)
        label = QLabel("Applied", self)
        label.move(210, 60)

        start_y = 80
        for name, parameter in self.instrument.parameters.items():
            label = QLabel(name, self)
            label.move(30, start_y)
            label.show()

            self.inner_parameter_btns[name] = QPushButton("Edit " + name, self)
            self.inner_parameter_btns[name].move(70, start_y)
            self.inner_parameter_btns[name].resize(80, 20)
            self.inner_parameter_btns[name].clicked.connect(self.make_edit_parameter(name))

            if is_numeric(self.instrument.get(name)):
                val = round(self.instrument.get(name), 3)
            else:
                val = self.instrument.get(name)
            self.textboxes_real_values[name] = QLineEdit(str(val), self)
            self.textboxes_real_values[name].move(155, start_y)
            self.textboxes_real_values[name].resize(50, 20)
            self.textboxes_real_values[name].setDisabled(True)
            if str(parameter) in self.dividers:
                self.textboxes_divided_values[name] = QLineEdit(str(self.dividers[str(parameter)].get_raw()), self)
                self.textboxes_divided_values[name].resize(50, 20)
                self.textboxes_divided_values[name].move(210, start_y)
                self.textboxes_divided_values[name].setDisabled(True)
            self.textboxes[name] = QLineEdit(str(val), self)
            self.textboxes[name].move(265, start_y)
            self.textboxes[name].resize(80, 20)
            set_value_btn = QPushButton("Set", self)
            set_value_btn.move(360, start_y)
            set_value_btn.resize(40, 20)
            set_value_btn.clicked.connect(self.make_set_parameter(name))
            get_value_btn = QPushButton("Get", self)
            get_value_btn.move(410, start_y)
            get_value_btn.resize(40, 20)
            get_value_btn.clicked.connect(lambda checked, parameter_name=name: self.update_parameters_data(parameter_name))
            start_y += 25

        set_all_to_zero_btn = QPushButton("All zeroes", self)
        set_all_to_zero_btn.move(380, start_y + 20)
        set_all_to_zero_btn.clicked.connect(self.call_worker(self.set_all_to_zero))

        set_all_btn = QPushButton("SET ALL", self)
        set_all_btn.move(290, start_y + 20)
        # set_all_btn.clicked.connect(self.call_worker(self.set_all))
        set_all_btn.clicked.connect(self.set_all)

        set_all_btn = QPushButton("GET ALL", self)
        set_all_btn.move(290, start_y + 50)
        set_all_btn.clicked.connect(self.call_worker(self.update_parameters_data))

        ok_btn = QPushButton("Close", self)
        ok_btn.move(380, start_y + 50)
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
            full_name = str(self.instrument.parameters[parameter])
            try:
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
                        textbox.setText(str(round(self.instrument.get(name), 3)))
                    else:
                        textbox.setText(str(self.instrument.get(name)))
            for name, textbox in self.textboxes_real_values.items():
                if is_numeric(self.instrument.get(name)):
                    textbox.setText(str(round(self.instrument.get(name), 3)))
                else:
                    if is_numeric(self.instrument.get(name)):
                        textbox.setText(str(round(self.instrument.get(name), 3)))
                    else:
                        textbox.setText(str(self.instrument.get(name)))
            self.update_divided_values()

    def update_divided_values(self):
        for name, textbox in self.textboxes_divided_values.items():
            textbox.setText(str(self.dividers[str(self.instrument.parameters[name])].get_raw()))

    def set_all_to_zero(self):
        """
        Set value of all numeric type parameters to be zero

        :return: NoneType
        """
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
                    # self.instrument.set(name, value)
                    if full_name in self.dividers:
                        self.dividers[full_name].set_raw(value)
                    else:
                        self.instrument.set(name, value)
                    print(name)
                except Exception as e:
                    show_error_message("Warning", str(e))
                    #show_error_message("Warning", "Unable to set parameter {} to value {}"
                    #                   .format(str(parameter), self.textboxes[name].text()))
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
            worker = Worker(func)
            worker.signals.result.connect(print_output)
            worker.signals.finished.connect(thread_complete)
            worker.signals.progress.connect(progress_func)

            self.thread_pool.start(worker)

        return instantiate_worker


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = EditInstrumentWidget({})
    sys.exit(app.exec_())
