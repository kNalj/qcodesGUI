from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QLabel, QComboBox

import sys

from Helpers import *
from qcodes.instrument_drivers.devices import VoltageDivider


class DividerWidget(QWidget):
    def __init__(self, instruments, dividers, parameter=None, instrument_name=None, parent=None):
        """
        Constructor for AddInstrumentWidget window

        :param instruments: Dictionary shared with parent (MainWindow) to be able to add instruments to instruments
        dictionary in the MainWindow
        :param parent: specify object that created this widget
        """
        super(DividerWidget, self).__init__()
        self.instruments = instruments
        self.dividers = dividers
        self.parameter = parameter
        self.instrument_name = instrument_name
        if self.instrument_name is not None:
            self.instrument = self.instruments[self.instrument_name]
        else:
            self.instrument = None
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
        self.setWindowIcon(QtGui.QIcon("img/osciloscope_icon.png"))

        label = QLabel("Parameter:", self)
        label.move(25, 40)
        self.parameter_cb = QComboBox(self)
        self.parameter_cb.resize(180, 30)
        self.parameter_cb.move(45, 60)
        if self.parameter is not None:
            display_member_string = "[" + self.instrument_name + "] " + self.parameter
            value_member = self.instrument.parameters[self.parameter]
            self.parameter_cb.addItem(display_member_string, value_member)
        else:
            if self.instrument is not None:
                for parameter in self.instrument.parameters:
                    display_member_string = "[" + self.instrument_name + "] " + parameter
                    value_member = self.instrument.parameters[parameter]
                    self.parameter_cb.addItem(display_member_string, value_member)
            else:
                for name, instrument in self.instruments.items():
                    for parameter in instrument.parameters:
                        display_member_string = "[" + name + "] " + parameter
                        value_member = instrument.parameters[parameter]
                        self.parameter_cb.addItem(display_member_string, value_member)

        label = QLabel("Division", self)
        label.move(25, 100)
        self.division_value_textbox = QLineEdit(self)
        self.division_value_textbox.move(40, 120)
        self.division_value_textbox.resize(180, 30)

        self.remove_divider_btn = QPushButton("Remove", self)
        self.remove_divider_btn.move(170, 180)
        self.remove_divider_btn.resize(60, 30)
        self.remove_divider_btn.clicked.connect(self.remove_divider)

        self.attach_divider_btn = QPushButton("Add", self)
        self.attach_divider_btn.resize(60, 30)
        self.attach_divider_btn.move(240, 180)
        self.attach_divider_btn.clicked.connect(self.attach_divider)

    def attach_divider(self):

        parameter = self.parameter_cb.currentData()

        if self.division_value_textbox.text() != "1":
            try:
                division = float(self.division_value_textbox.text())
            except Exception as e:
                show_error_message("Warning", str(e))
            else:
                vd = VoltageDivider(parameter, division)
                self.dividers[str(parameter)] = vd
                self.close()
                self.parent.parent.make_open_instrument_edit(self.instrument_name)()
                self.parent.close()
        else:
            self.remove_divider()

    def remove_divider(self):
        parameter = self.parameter_cb.currentData()
        del self.dividers[str(parameter)]


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DividerWidget({})
    sys.exit(app.exec_())
