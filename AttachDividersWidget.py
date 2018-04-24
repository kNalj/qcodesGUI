from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QLabel, QComboBox, QTabWidget, \
    QTableWidget, QTableWidgetItem, QHeaderView, QTableView
from PyQt5.QtCore import Qt


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

        self.tabs = QTabWidget(self)
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.addTab(self.tab1, "Add")
        self.tabs.addTab(self.tab2, "Remove")
        self.tabs.resize(320, 260)
        self.tabs.show()

        """""""""""""""""""""
        First tab, adding new dividers
        """""""""""""""""""""
        label = QLabel("Parameter:", self.tab1)
        label.move(25, 40)
        self.instrument_cb = QComboBox(self.tab1)
        self.instrument_cb.move(45, 60)
        self.instrument_cb.resize(90, 30)
        self.parameter_cb = QComboBox(self.tab1)
        self.parameter_cb.resize(90, 30)
        self.parameter_cb.move(145, 60)
        for name, instrument in self.instruments.items():
            display_member = name
            value_member = instrument
            self.instrument_cb.addItem(display_member, value_member)
        self.instrument_cb.currentIndexChanged.connect(self.update_parameters)
        self.update_parameters()

        label = QLabel("Division", self.tab1)
        label.move(25, 100)
        self.division_value_textbox = QLineEdit(self.tab1)
        self.division_value_textbox.move(40, 120)
        self.division_value_textbox.resize(190, 30)

        self.attach_divider_btn = QPushButton("Add", self.tab1)
        self.attach_divider_btn.resize(60, 30)
        self.attach_divider_btn.move(240, 180)
        self.attach_divider_btn.clicked.connect(self.attach_divider)

        """""""""""""""""""""
        Second tab, removing dividers
        """""""""""""""""""""
        self.dividers_table = QTableWidget(0, 3, self.tab2)
        self.dividers_table.move(0, 0)
        self.dividers_table.resize(300, 240)
        self.dividers_table.setHorizontalHeaderLabels(("Parameter", "Division", "Delete"))
        header = self.dividers_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.dividers_table.setSelectionBehavior(QTableView.SelectRows)

        for name, parameter in self.dividers.items():
            rows = self.dividers_table.rowCount()
            self.dividers_table.insertRow(rows)
            item = QTableWidgetItem(name)
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.dividers_table.setItem(rows, 0, item)
            item = QTableWidgetItem(str(parameter.division_value))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.dividers_table.setItem(rows, 1, item)
            item = QTableWidgetItem(name)
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.dividers_table.setItem(rows, 0, item)
            current_parameter_btn = QPushButton("Delete")
            current_parameter_btn.resize(35, 20)
            current_parameter_btn.clicked.connect(lambda checked, param_name=name: self.remove_divider(name=param_name,
                                                                                                       row=rows))
            self.dividers_table.setCellWidget(rows, 2, current_parameter_btn)

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
        else:
            self.remove_divider()

    def remove_divider(self, name=None, row=None):
        if name is None:
            parameter = self.parameter_cb.currentData()
            if str(parameter) in self.dividers:
                del self.dividers[str(parameter)]
        else:
            if name in self.dividers:
                del self.dividers[name]
        self.dividers_table.removeRow(row)

    def update_parameters(self):
        if len(self.instruments):
            self.parameter_cb.clear()
            instrument = self.instrument_cb.currentData()
            for parameter in instrument.parameters:
                if parameter != "IDN":
                    display_member_string = parameter
                    data_member = instrument.parameters[parameter]
                    self.parameter_cb.addItem(display_member_string, data_member)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DividerWidget({})
    sys.exit(app.exec_())
