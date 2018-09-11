"""
qcodes/instrument/base.py -> line 263
There u can find a set function for setting paramater defined by "name" to a value defined by "value"
"""

from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QLabel, QShortcut, QVBoxLayout, QHBoxLayout
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

        # set initial size and position od the widget
        self.setGeometry(256, 256, 480, 260)
        self.setMinimumSize(320, 260)
        # set window title and icon of the widget
        self.setWindowTitle("Edit " + self.parameter.name + " parameter")
        self.setWindowIcon(QtGui.QIcon("img/osciloscope_icon.png"))

        self.setLayout(QVBoxLayout())

        # parameters that can be edited with this window are it the list below
        extras = ["step", "inter_delay", "_min_value", "_max_value"]
        # for each parameter in the list create text box and get/set buttons
        for name in extras:
            horizontal = QHBoxLayout()
            self.layout().addLayout(horizontal)
            if name == "step":
                if hasattr(self.parameter, name):
                    self.textboxes_real_values[name] = QLineEdit(str(self.parameter.step))
            elif name == "inter_delay":
                if hasattr(self.parameter, name):
                    self.textboxes_real_values[name] = QLineEdit(str(self.parameter.inter_delay))
            else:
                if hasattr(self.parameter.vals, name):
                    self.textboxes_real_values[name] = QLineEdit(str(getattr(self.parameter.vals, name)))
            if name in self.textboxes_real_values:
                label = QLabel(name)
                horizontal.addWidget(label)
                horizontal.addWidget(self.textboxes_real_values[name])
                self.textboxes_real_values[name].setDisabled(True)
            if name == "step":
                self.textboxes[name] = QLineEdit(str(self.parameter.step))
            elif name == "inter_delay":
                self.textboxes[name] = QLineEdit(str(self.parameter.inter_delay))
            else:
                if hasattr(self.parameter.vals, name):
                    self.textboxes[name] = QLineEdit(str(getattr(self.parameter.vals, name)))
            if name in self.textboxes:
                horizontal.addWidget(self.textboxes[name])
                if hasattr(self.parameter, "set"):
                    set_value_btn = QPushButton("Set")
                    horizontal.addWidget(set_value_btn)
                    set_value_btn.clicked.connect(self.make_set_value(name))
                get_value_btn = QPushButton("Get")
                horizontal.addWidget(get_value_btn)
                get_value_btn.clicked.connect(self.update_displayed_values)

        # Its just an CLOSE button man, dont read this
        self.OK_btn = QPushButton("Close")
        self.layout().addWidget(self.OK_btn)
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
            # parameter is passed to the widgets constructor, and widget at any point know what parameter is he editing
            parameter = self.parameter
            # depending on which of possible parameters is being modified do the appropriate action
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
        # update editable texbox with the new value
        for name, textbox in self.textboxes.items():
            if name == "step":
                textbox.setText(str(self.parameter.step))
            elif name == "inter_delay":
                textbox.setText(str(self.parameter.inter_delay))
            else:
                textbox.setText(str(getattr(self.parameter.vals, name)))

        # update non-editable textbox with the new value
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
