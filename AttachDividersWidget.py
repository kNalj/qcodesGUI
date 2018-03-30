from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QLabel, QComboBox, QVBoxLayout, \
    QRadioButton, QMessageBox
from PyQt5 import QtGui

import inspect
import sys
import importlib

import qcodes as qc
from instrument_imports import *
from Helpers import *
from qcodes.instrument.ip import IPInstrument
from qcodes.instrument.visa import VisaInstrument


class DividerWidget(QWidget):

    def __init__(self, instruments, parent=None):
        """
        Constructor for AddInstrumentWidget window

        :param instruments: Dictionary shared with parent (MainWindow) to be able to add instruments to instruments
        dictionary in the MainWindow
        :param parent: specify object that created this widget
        """
        super(DividerWidget, self).__init__()
        self.instruments = instruments
        self.parent = parent
        self.init_ui()
        self.show()

    """""""""""""""""""""
    User interface
    """""""""""""""""""""

    def init_ui(self):
        """
        Initialisation of the user interface (as the function name suggests)

        :return: NoneType
        """

        self.setGeometry(256, 256, 320, 260)
        self.setMinimumSize(320, 260)
        self.setWindowTitle("Attach divider")
        self.setWindowIcon(QtGui.QIcon("osciloscope_icon.png"))

        label = QLabel("Parameter:", self)
        label.move(25, 40)
        self.parameter_cb = QComboBox(self)
        self.parameter_cb.resize(180, 30)
        self.parameter_cb.move(45, 60)
        for name, instrument in self.instruments.items():
            for parameter in instrument.parameters:
                display_member_string = "[" + name + "] " + parameter
                value_member = instrument.parameters[parameter]
                self.parameter_cb.addItem(display_member_string, value_member)
        self.attach_divider_btn = QPushButton("Add", self)
        self.attach_divider_btn.resize(60, 30)
        self.attach_divider_btn.move(240, 140)
        self.attach_divider_btn.clicked.connect(self.attach_divider)


    def attach_divider(self):
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DividerWidget({})
    sys.exit(app.exec_())
