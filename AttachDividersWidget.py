from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QLabel, QComboBox, QTabWidget, \
    QTableWidget, QTableWidgetItem, QHeaderView, QTableView, QVBoxLayout, QHBoxLayout, QGridLayout, QSizePolicy
from PyQt5.QtCore import Qt


import sys

from Helpers import *
from qcodes.instrument_drivers.devices import VoltageDivider


class DividerWidget(QWidget):
    def __init__(self, instruments, dividers, parameter=None, instrument_name=None, parent=None):
        """
        Constructor for the AttachDividerWidget class

        :param instruments: dictionary shared with the mainWindow, contains all instruments created so far
        :param dividers: dictionary shared with the mainWindow, contains all dividers attached so far
        :param parameter:
        :param instrument_name: if instrument_name is passed to the constructor, only parameters of that particular
                instrument will be selectable from the combobox
        :param parent: pointer to the parent widget
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
        Initialisation of the user interface (as the function name suggests). This is where i like to write useless
        comments in case someone ever decides to read this. One might think that this contains some usefull information
        when in reality its just me typing random stuff to make it look pretty.

        :return: NoneType
        """

        # define starting size and position of the widget
        self.setGeometry(256, 256, 320, 260)
        self.setMinimumSize(320, 260)
        # define title and icon of the widget
        self.setWindowTitle("Attach divider")
        self.setWindowIcon(QtGui.QIcon("img/osciloscope_icon.png"))

        # Create two separate tabs of this widget, one for adding and one for deleting existing dividers
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.addTab(self.tab1, "Add")
        self.tabs.addTab(self.tab2, "Remove")
        self.tabs.resize(320, 260)

        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)

        self.grid_layout.addWidget(self.tabs)

        self.tabs.show()

        """""""""""""""""""""
        First tab, adding new dividers
        """""""""""""""""""""
        main_layout_tab1 = QVBoxLayout()
        self.tab1.setLayout(main_layout_tab1)

        label = QLabel("Parameter:")
        main_layout_tab1.addWidget(label)
        # combo boxes for instrument and parameter

        horizontal = QHBoxLayout()

        self.instrument_cb = QComboBox()
        horizontal.addWidget(self.instrument_cb)
        self.parameter_cb = QComboBox()
        horizontal.addWidget(self.parameter_cb)
        main_layout_tab1.addLayout(horizontal)
        for name, instrument in self.instruments.items():
            display_member = name
            value_member = instrument
            self.instrument_cb.addItem(display_member, value_member)
        self.instrument_cb.currentIndexChanged.connect(self.update_parameters)
        self.update_parameters()

        # text box for division value
        label = QLabel("Division")
        main_layout_tab1.addWidget(label)
        self.division_value_textbox = QLineEdit()
        main_layout_tab1.addWidget(self.division_value_textbox)

        # button to confirm adding divider
        self.attach_divider_btn = QPushButton("Add")
        main_layout_tab1.addWidget(self.attach_divider_btn)
        self.attach_divider_btn.clicked.connect(self.attach_divider)

        """""""""""""""""""""
        Second tab, removing dividers
        """""""""""""""""""""

        main_layout_tab2 = QVBoxLayout()
        self.tab2.setLayout(main_layout_tab2)

        # table containing all dividers created so far
        self.dividers_table = QTableWidget(0, 3)
        main_layout_tab2.addWidget(self.dividers_table)
        self.dividers_table.setHorizontalHeaderLabels(("Parameter", "Division", "Delete"))
        header = self.dividers_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.dividers_table.setSelectionBehavior(QTableView.SelectRows)

        # add all dividers to the table
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
            # add a delete button for every divider in the table
            current_parameter_btn = QPushButton("Delete")
            current_parameter_btn.resize(35, 20)
            current_parameter_btn.clicked.connect(self.make_remove_divider(name=name, item=item))
            self.dividers_table.setCellWidget(rows, 2, current_parameter_btn)

    def attach_divider(self):
        """
        Instantiates a VoltageDivider with specified data (only if division_value_textbox is not equal to 1, in case of
        it being 1 there is no need for a voltage divider, therefor its not added.
        Additionaly it adds the newly created divider to a dictionary (dividers) shared with mainWindow

        parameter:
            parameter that is gonna get a divider attched to it
            obtained from the parameter_cb combobox
        division value:
            if you dont know what this is, consider other professions
            obtained from division_value_textbox

        :return: NoneType
        """
        # fetch the selected parameter from the combo box
        parameter = self.parameter_cb.currentData()
        # fetch the division value from the text box
        if self.division_value_textbox.text() != "1":
            try:
                # try to cast division value to float
                division = float(self.division_value_textbox.text())
            except Exception as e:
                show_error_message("Warning", str(e))
            else:
                # if no exception was raised, create a new divider
                vd = VoltageDivider(parameter, division)
                self.dividers[str(parameter)] = vd
                self.close()

    def make_remove_divider(self, name, item):
        """
        Function factory, create a function that removes a divider from the table of dividers

        :param name: name of the parameter (used to remove divider from dict divider shared with mainWindow
        :param item: referes to an item of the tableWidget that we want to remove from the table
        :return: pointer to newly created function that removes wanted item from tableWidget
        """
        def remove_divider():
            """
            Removes a divider from the dictionary of dividers (shared with the mainWindow), also removes a row from the
            divider_table widget in this window.

            :return: NoneType
            """
            if name is None:
                parameter = self.parameter_cb.currentData()
                if str(parameter) in self.dividers:
                    del self.dividers[str(parameter)]
            else:
                if name in self.dividers:
                    del self.dividers[name]
            self.dividers_table.removeRow(self.dividers_table.row(item))
        return remove_divider

    def update_parameters(self):
        """
        Updates parameter combobox by removing all parameters from it, and then re adding those belongig to the
        instrument selected in the instrument combobox

        :return: NoneType
        """
        # get all parameters that belong to this instrument and add them to a combo box so that they can be selected
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
