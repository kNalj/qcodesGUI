"""
qcodes/instrument/base.py -> line 263
There u can find a set function for setting paramater defined by "name" to a value defined by "value"
"""

from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QLabel

import sys

from Helpers import *


class EditInstrumentWidget(QWidget):

    def __init__(self, instruments, parent=None, instrument_name=""):
        """
        Constructor for EditInstrumentWidget window

        :param instrument: Instance of an instrument to be edited
        :param parent: specify object that created this widget
        """
        super(EditInstrumentWidget, self).__init__()
        self.parent = parent
        self.instruments = instruments
        self.instrument_name = instrument_name
        self.instrument = self.instruments[instrument_name]
        self.textboxes = {}
        self.textboxes_real_values = {}
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
        height = len(self.instrument.parameters)*50 + 100
        self.setGeometry(256, height, 320, 260)
        self.setMinimumSize(320, 260)
        self.setWindowTitle("Edit " + self.instrument_name.upper() + " instrument")
        self.setWindowIcon(QtGui.QIcon("osciloscope_icon.png"))

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
            self.textboxes_real_values[name] = QLineEdit(str(self.instrument.get(name)), self)
            self.textboxes_real_values[name].move(80, start_y)
            self.textboxes_real_values[name].resize(40, 20)
            self.textboxes_real_values[name].setDisabled(True)
            self.textboxes[name] = QLineEdit(str(self.instrument.get(name)), self)
            self.textboxes[name].move(130, start_y)
            set_value_btn = QPushButton("Set", self)
            set_value_btn.move(280, start_y)
            set_value_btn.resize(40, 20)
            set_value_btn.clicked.connect(self.make_set_parameter(name))
            start_y += 25

            set_all_to_zero_btn = QPushButton("All zeroes", self)
            set_all_to_zero_btn.move(200, start_y+50)
            set_all_to_zero_btn.clicked.connect(self.set_all_to_zero)

    """""""""""""""""""""
    Data manipulation
    """""""""""""""""""""
    def make_set_parameter(self, parameter):
        print(parameter)
        print(self.textboxes[parameter].text())

        def set_parameter():
            try:
                value = float(self.textboxes[parameter].text())
                self.instrument.set(parameter, value)
            except Exception as e:
                show_error_message("Warning", str(e))
            else:
                self.update_parameters_data()
                self.setStatusTip("Parameter value changed to: " + str(value))
        return set_parameter

    def update_parameters_data(self):
        for name, textbox in self.textboxes.items():
            textbox.setText(str(round(self.instrument.get(name), 3)))
        for name, textbox in self.textboxes_real_values.items():
            textbox.setText(str(round(self.instrument.get(name), 3)))

    def set_all_to_zero(self):

        for name, parameter in self.instrument.parameters.items():
            print(name, parameter)
            if str(self.instrument.get(name)).replace('.', '', 1).isdigit():
                self.instrument.set(name, 0)
            self.update_parameters_data()

    """""""""""""""""""""
    Helper functions
    """""""""""""""""""""


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = EditInstrumentWidget({})
    sys.exit(app.exec_())
