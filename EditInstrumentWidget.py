"""
qcodes/instrument/base.py -> line 263
There u can find a set function for setting paramater defined by "name" to a value defined by "value"
"""

from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QLabel, QComboBox, QVBoxLayout, \
    QRadioButton, QMessageBox
from PyQt5 import QtGui

import inspect
import sys
import importlib

import qcodes as qc
from instrument_imports import *
from InstrumentData import *
from Helpers import *
from qcodes.instrument.ip import IPInstrument
from qcodes.instrument.visa import VisaInstrument


class EditInstrumentWidget(QWidget):

    def __init__(self, instruments, parent=None, instrument_name="'name'"):
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

        self.setGeometry(256, len(self.instrument.parameters)*50 + 100, 320, 260)
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
            value = QLineEdit(self.instrument.get(), self)
            value.move(80, start_y)
            start_y += 20



    """""""""""""""""""""
    Data manipulation
    """""""""""""""""""""

    """""""""""""""""""""
    Helper functions
    """""""""""""""""""""


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = EditInstrumentWidget({})
    sys.exit(app.exec_())
