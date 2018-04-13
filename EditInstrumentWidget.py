"""
qcodes/instrument/base.py -> line 263
There u can find a set function for setting paramater defined by "name" to a value defined by "value"
"""

from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QLabel, QShortcut
from PyQt5.QtCore import Qt
from PyQt5 import QtGui

import sys

from Helpers import *
from ThreadWorker import Worker, progress_func, print_output, thread_complete
from EditInstrumentParametersWidget import EditInstrumentParameterWidget


class EditInstrumentWidget(QWidget):

    def __init__(self, instruments, parent=None, instrument_name=""):
        """
        Constructor for EditInstrumentWidget window

        :param instrument_name: Name of an instrument to be edited
        :param parent: specify object that created this widget
        """
        super(EditInstrumentWidget, self).__init__()
        self.parent = parent

        self.instruments = instruments
        self.instrument_name = instrument_name
        self.instrument = self.instruments[instrument_name]

        self.textboxes = {}
        self.textboxes_real_values = {}

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
        # _, _, width, height = QtGui.QDesktopWidget().screenGeometry().getCoords()
        height = len(self.instrument.parameters)*30 + 100
        self.setGeometry(256, 256, 480, height)
        self.setMinimumSize(320, 260)
        self.setWindowTitle("Edit " + self.instrument_name.upper() + " instrument")
        self.setWindowIcon(QtGui.QIcon("img/osciloscope_icon.png"))

        label = QLabel("Name:", self)
        label.move(30, 30)
        self.instrument_name_txtbox = QLineEdit(self.instrument_name, self)
        self.instrument_name_txtbox.move(80, 30)
        self.instrument_name_txtbox.setDisabled(True)

        start_y = 80
        for name, parameter in self.instrument.parameters.items():
            label = QLabel(name, self)
            label.move(30, start_y)
            label.show()

            self.inner_parameter_btns[name] = QPushButton("Edit " + name, self)
            self.inner_parameter_btns[name].move(70, start_y)
            self.inner_parameter_btns[name].resize(80, 20)
            self.inner_parameter_btns[name].clicked.connect(self.make_edit_parameter(name))

            if str(self.instrument.get(name)).replace(".", "", 1).isdigit():
                val = str(round(self.instrument.get(name), 3))
            else:
                val = str(self.instrument.get(name))
            self.textboxes_real_values[name] = QLineEdit(val, self)
            self.textboxes_real_values[name].move(155, start_y)
            self.textboxes_real_values[name].resize(50, 20)
            self.textboxes_real_values[name].setDisabled(True)
            self.textboxes[name] = QLineEdit(str(self.instrument.get(name)), self)
            self.textboxes[name].move(210, start_y)
            set_value_btn = QPushButton("Set", self)
            set_value_btn.move(360, start_y)
            set_value_btn.resize(40, 20)
            set_value_btn.clicked.connect(self.make_set_parameter(name))
            start_y += 25

        set_all_to_zero_btn = QPushButton("All zeroes", self)
        set_all_to_zero_btn.move(200, start_y + 50)
        set_all_to_zero_btn.clicked.connect(self.call_worker(self.set_all_to_zero))

        set_all_btn = QPushButton("SET ALL", self)
        set_all_btn.move(290, start_y + 50)
        set_all_btn.clicked.connect(self.call_worker(self.set_all))

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

            :return: NoneType
            """
            try:
                value = float(self.textboxes[parameter].text())
                self.instrument.set(parameter, value)
            except Exception as e:
                show_error_message("Warning", str(e))
            else:
                self.update_parameters_data()
                self.setStatusTip("Parameter value changed to: " + str(value))
        return set_parameter

    def make_edit_parameter(self, parameter):

        def edit_instrument():
            self.edit_instrument_parameters = EditInstrumentParameterWidget(self.instruments, self.instrument,
                                                                            parameter, parent=self)
            self.edit_instrument_parameters.show()

        return edit_instrument

    def update_parameters_data(self):
        """
        Updates values of all parameters after a change has been made. Implements data validation (has to be number)

        :return: NoneType
        """
        for name, textbox in self.textboxes.items():
            textbox.setText(str(self.instrument.get(name)))
        for name, textbox in self.textboxes_real_values.items():
            if str(self.instrument.get(name)).replace('.', '', 1).isdigit():
                textbox.setText(str(round(self.instrument.get(name), 3)))
            else:
                textbox.setText(str(self.instrument.get(name)))

    def set_all_to_zero(self):
        """
        Set value of all numeric type parameters to be zero

        :return: NoneType
        """
        if hasattr(self.instrument, "set_dacs_zero"):
            self.instrument.set_dacs_zero()
        else:
            for name, parameter in self.instrument.parameters.items():
                if str(self.instrument.get(name)).replace('.', '', 1).isdigit():
                    if name[0:3] == "dac" and len(name) == (4 or 5):
                        self.instrument.set(name, 0)
        self.update_parameters_data()

    def set_all(self):
        """
        Sets and updates displayed values for all parameters at the same time (if multiple parameters were edited)

        :return: NoneType
        """
        for name, parameter in self.instrument.parameters.items():
            if str(self.instrument.get(name)).replace('.', '', 1).isdigit():
                try:
                    value = float(self.textboxes[name].text())
                    self.instrument.set(name, value)
                except Exception as e:
                    show_error_message("Warning", str(e))
                else:
                    self.setStatusTip("Parameter value changed to: " + str(value))
        self.update_parameters_data()

    """""""""""""""""""""
    Helper functions
    """""""""""""""""""""
    def call_worker(self, func):

        def instanciate_worker():

            worker = Worker(func)
            worker.signals.result.connect(print_output)
            worker.signals.finished.connect(thread_complete)
            worker.signals.progress.connect(progress_func)

            self.parent.thread_pool.start(worker)

        return instanciate_worker


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = EditInstrumentWidget({})
    sys.exit(app.exec_())
