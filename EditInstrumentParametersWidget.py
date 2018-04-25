"""
qcodes/instrument/base.py -> line 263
There u can find a set function for setting paramater defined by "name" to a value defined by "value"
"""

from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QLabel, QShortcut
from PyQt5.QtCore import Qt

import sys

from Helpers import *


class EditInstrumentParameterWidget(QWidget):

    def __init__(self, instruments, instrument, parameter, dividers, parent=None):
        """
        Constructor for EditInstrumentWidget window

        :param instruments: dict of all instruments that are currently in the station (shared with the mainWindow)
        :param instrument: Instance of an instrument to be edited
        :param parameter: name of the parameter that is being edited with current instance of this widget
        :param dividers: dict of all dividers created in this session of using this GUI
        :param parent: specify object that created this widget
        """
        super(EditInstrumentParameterWidget, self).__init__()
        self.parent = parent

        self.instruments = instruments
        self.instrument = instrument
        self.parameter = self.instrument.parameters[parameter]
        self.dividers = dividers

        self.textboxes = {}
        self.textboxes_real_values = {}

        self.init_ui()
        self.show()

    """""""""""""""""""""
    User interface
    """""""""""""""""""""

    def init_ui(self):
        """
        “In a closed society where everybody's guilty, the only crime is getting caught.
        In a world of thieves, the only final sin is stupidity.”

        Hunter S. Thompson

        :return: NoneType
        """

        self.setGeometry(256, 256, 480, 260)
        self.setMinimumSize(320, 260)
        self.setWindowTitle("Edit " + self.parameter.name + " parameter")
        self.setWindowIcon(QtGui.QIcon("img/osciloscope_icon.png"))

        extras = ["step", "inter_delay", "_min_value", "_max_value"]
        start_y = 25
        for name in extras:
            label = QLabel(name, self)
            label.move(30, start_y)
            label.show()
            if name == "step":
                self.textboxes_real_values[name] = QLineEdit(str(self.parameter.step), self)
            elif name == "inter_delay":
                self.textboxes_real_values[name] = QLineEdit(str(self.parameter.inter_delay), self)
            else:
                self.textboxes_real_values[name] = QLineEdit(str(getattr(self.parameter.vals, name)), self)
            self.textboxes_real_values[name].move(120, start_y)
            self.textboxes_real_values[name].resize(40, 20)
            self.textboxes_real_values[name].setDisabled(True)
            if name == "step":
                self.textboxes[name] = QLineEdit(str(self.parameter.step), self)
            elif name == "inter_delay":
                self.textboxes[name] = QLineEdit(str(self.parameter.inter_delay), self)
            else:
                self.textboxes[name] = QLineEdit(str(getattr(self.parameter.vals, name)), self)
            self.textboxes[name].move(180, start_y)
            set_value_btn = QPushButton("Set", self)
            set_value_btn.move(340, start_y)
            set_value_btn.resize(40, 20)
            set_value_btn.clicked.connect(self.make_set_value(name))
            get_value_btn = QPushButton("Get", self)
            get_value_btn.move(390, start_y)
            get_value_btn.resize(40, 20)
            get_value_btn.clicked.connect(self.update_displayed_values)
            start_y += 25

        label = QLabel("Division", self)
        label.move(30, start_y + 25)
        label.show()
        if str(self.parameter) in self.dividers:
            self.division_value = QLineEdit(str(self.dividers[str(self.parameter)].division_value), self)
        else:
            self.division_value = QLineEdit("1", self)
        self.division_value.move(120, start_y + 25)

        self.OK_btn = QPushButton("Close", self)
        self.OK_btn.move(400, 220)
        self.OK_btn.clicked.connect(self.close)

        close_shortcut = QShortcut(QtGui.QKeySequence(Qt.Key_Escape), self)
        close_shortcut.activated.connect(self.close)

    """""""""""""""""""""
    Data manipulation
    """""""""""""""""""""
    def make_set_value(self, value_name):
        """
        Function factory for making a function that manipulates parameter values (delay and step)
        Button send the name of a value to be set (either step or delay) and a function is created and executed based on
        the parameter passed to the factory.

        :param value_name: name of the value to be changed
        :return: function set_value that updates the requested value (read from QLineEdit)
        """
        def set_value():
            """
            IT SETS A VALUE TO SOMETHING, WHAT DID U THINK IT WOULD DO !?

            :return:
            """
            parameter = self.parameter
            if value_name == "step":
                try:
                    value = float(self.textboxes[value_name].text())
                    parameter.step = value
                except Exception as e:
                    show_error_message("Warning", str(e))
                else:
                    self.update_displayed_values()

            elif value_name == "inter_delay":
                try:
                    value = float(self.textboxes[value_name].text())
                    parameter.inter_delay = value
                except Exception as e:
                    show_error_message("Warning", str(e))
                else:
                    self.update_displayed_values()
            else:
                try:
                    value = float(self.textboxes[value_name].text())
                    setattr(self.parameter.vals, value_name, value)
                except Exception as e:
                    show_error_message("Warning", str(e))
                else:
                    self.update_displayed_values()

        return set_value

    def update_displayed_values(self):
        """
        Usually called after changing step/delay of a parameter, updates displayed data to match the real values on
        the instruments.

        :return: NoneType
        """
        for name, textbox in self.textboxes.items():
            if name == "step":
                textbox.setText(str(self.parameter.step))
            elif name == "inter_delay":
                textbox.setText(str(self.parameter.inter_delay))
            else:
                textbox.setText(str(getattr(self.parameter.vals, name)))

        for name, textbox in self.textboxes_real_values.items():
            if name == "step":
                textbox.setText(str(self.parameter.step))
            elif name == "inter_delay":
                textbox.setText(str(self.parameter.inter_delay))
            else:
                textbox.setText(str(getattr(self.parameter.vals, name)))

    """""""""""""""""""""
    Helper functions
    """""""""""""""""""""


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = EditInstrumentParameterWidget({}, "")
    sys.exit(app.exec_())
