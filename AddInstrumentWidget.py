"""
qcodes/instrument/base.py -> line 263
There u can find a set function for setting paramater defined by "name" to a value defined by "value"
"""

from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QLabel, QComboBox, QShortcut, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal

import inspect
import sys
import importlib

import qcodes as qc
from qcodes.instrument_drivers.QuTech.IVVI import IVVI
from qcodes.instrument_drivers.tektronix.AWG5014 import Tektronix_AWG5014
from instrument_imports import *
from InstrumentData import *
from Helpers import *


class Widget(QWidget):

    submitted = pyqtSignal(object)

    def __init__(self, instruments, parent=None, default="DummyInstrument"):
        """
        Constructor for AddInstrumentWidget window

        :param instruments: Dictionary shared with parent (MainWindow) to be able to add instruments to instruments
        dictionary in the MainWindow
        :param parent: specify object that created this widget
        :param default: instrument data (type, name, address) is filled based on what is passed as a default instrument
        """
        super(Widget, self).__init__()
        # list of instruments shared with the mainWindow (contains all instruments created so far)
        self.instruments = instruments

        # dictionary containing pointers to all available instrument classes with instrument type as keys
        self.premade_instruments = {}
        # call to a function that fills the above dict
        self.populate_premade_instruments()
        # pointer to a parent widget
        self.parent = parent
        # specifies an instrument to be show in the combobox by default
        self.default = default
        self.init_ui()
        self.show()

    """""""""""""""""""""
    User interface
    """""""""""""""""""""
    def init_ui(self):
        """
        Initialisation of the user interface (as the function name suggests, why am i even writing this ?
        Is this real world ? Am i real ? WOW !)

        :return: NoneType
        """

        # define the starting position and dimensions of the widget
        self.setGeometry(256, 256, 320, 260)
        self.setMinimumSize(320, 260)
        # define name and the icon of the widget
        self.setWindowTitle("Add new instrument")
        self.setWindowIcon(QtGui.QIcon("img/osciloscope_icon.png"))

        self.vertical_layout = QVBoxLayout()
        self.setLayout(self.vertical_layout)

        # combobox filled with all instrument classes that were found in the qcodes directory: "instrument drivers"
        self.cb = QComboBox()
        self.vertical_layout.addWidget(self.cb)
        for key, value in self.premade_instruments.items():
            self.cb.addItem(key)
        index = self.cb.findText(self.default)
        self.cb.setCurrentIndex(index)
        self.cb.currentIndexChanged.connect(self.update_instrument_data)

        # text box that displays the type of the instrument currently selected
        type_label = QLabel("Type")
        self.vertical_layout.addWidget(type_label)
        self.instrument_type = QLineEdit()
        self.instrument_type.setEnabled(False)
        self.vertical_layout.addWidget(self.instrument_type)

        # text box for choosing a name of the instrument (if it exists in the InstrumentData.py then it will be filled
        # automatically
        name_label = QLabel("Name")
        self.vertical_layout.addWidget(name_label)
        self.instrument_name = QLineEdit()
        self.vertical_layout.addWidget(self.instrument_name)

        # tex box for address, filled automatically if instrument exists in InstrumentData.py
        address_label = QLabel("Address")
        self.vertical_layout.addWidget(address_label)
        self.instrument_address = QLineEdit()
        self.vertical_layout.addWidget(self.instrument_address)

        # It's a button, that says OK, what do u think it does ?
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.add_instrument)
        self.vertical_layout.addWidget(self.ok_button)

        # Define some shortcuts
        add_shortcut = QShortcut(QtGui.QKeySequence(Qt.Key_Return), self)
        add_shortcut.activated.connect(self.add_instrument)
        add_shortcut = QShortcut(QtGui.QKeySequence(Qt.Key_Enter), self)
        add_shortcut.activated.connect(self.add_instrument)
        close_shortcut = QShortcut(QtGui.QKeySequence(Qt.Key_Escape), self)
        close_shortcut.activated.connect(self.close)

        # After initializing the window, fill the boxes with data if it exists
        self.update_instrument_data()

    def add_instrument(self):
        """
        Called upon clicking OK. Adds instrument (based on user input) to the instrument dictionary in the main window.
        Data structure -> {name : instrument object}
        """

        # Validate data, if validation returns True then some mistake was found, abort further execution
        if self.validate_instrument_input():
            return

        # fetch the name of the instrument
        name = self.instrument_name.text()
        instrument = None
        try:
            # Try to create an instance of the instrument class
            instrument = self.create_object()
        except Exception as e:
            show_error_message("Warning", str(e))
        else:
            if isinstance(instrument, IVVI):
                for i in range(instrument._numdacs):
                    param_name = "dac" + str(i + 1)
                    parameter = instrument.parameters[param_name]
                    parameter.step = 100
                    parameter.inter_delay = 0

        # if some instrument was created, add it to a dict of instruments shared with the main window and update
        # preview of the instruments in the main window
        if instrument is not None:
            self.instruments[name] = instrument
            self.submitted.emit(instrument)
            # self.parent.update_station_preview()
            self.close()
        
    def update_instrument_data(self):
        """
        Upon selecting one of instruments from dropdown, updates input fields with data availible from class
        Additionally if the instrument has data bound to it in the InstrumentData file, also update that data

        :return: NoneType
        """

        # grab the type of the instrument from the dropdown (combobox)
        instrument_type = self.cb.currentText()
        # if this type exists in InstrumentData.py fill the other fields with data found in that file.
        # InstrumentData.Py file contains a dict of instrument type with names and addresses as their values.
        # From there it is assumed that whenever an instrument of that class is being created that it will allways have
        # the same desired name and address, therefor they are automatically filled in from the file
        # Of course data can be changed after if necessary.
        if instrument_type in instrument_data:
            instrument_name = instrument_data[instrument_type][0]
            instrument_address = instrument_data[instrument_type][1]
            self.instrument_name.setText(instrument_name)
            self.instrument_address.setText(instrument_address)
        else:
            self.instrument_name.setText("")
            self.instrument_address.setText("")
        self.instrument_type.setText(instrument_type)

    """""""""""""""""""""
    Data manipulation
    """""""""""""""""""""
    def validate_instrument_input(self):
        """
        Make sure all fields required for creating an object of a class are filled in with valid data

        :return: True if there is an error, False if there is no errors
        """
        # Fetch the name and the address provided by user
        name = self.instrument_name.text()
        address = self.instrument_address.text()

        # if name is shorter then 1 (meaning no name was provided) request user to input a name
        if len(name) < 1:
            error_message = "Please specify instrument name."
        # if name already exists in instruments (another instrument has that name) request user to change a name
        elif name in self.instruments:
            error_message = "Another instrument already has name: {}" + name + \
                            ". Please change the name of your isntrument"
        # If address was not provided, request address
        elif len(address) < 1:
            error_message = "Please specify instrument address"
        # In all other cases keep your mouth shut u goddamn boring shit program
        else:
            error_message = ""

        # if error message exists, show it and return True, otherwise just return false
        if error_message != "":
            show_error_message("Warning", error_message)
            return True
        else:
            return False

    def populate_premade_instruments(self):
        """
        Walks through folder structure and fetches instruments and their classes for further use. To be more specific
        to be able to populate the dropdown for selecting an instrument to create and also holds pointers to classes
        of all the instruments so that instantiating an instrument from class name is posible by looking into the
        premade_instruments dictionary and from the key that is a string representing the name of the class it fetches
        the class stored under that key.

        NOTE: Contains a list of instruments (not_working[]) that specifies instruments that throw errors (possibly they
        require some extra drivers made by instrument manufacturer, instruments starting with "Infiniium" ending with
        "Keithley_2600_Channels" were not throwing errors prior to qcodes commit (date cca. 06.04.2018))

        :return: NoneType
        """
        self.premade_instruments["DummyInstrument"] = getattr(importlib.import_module("DemoDummy"), "DummyInstrument")
        not_working = ["Keysight_33500B_channels", "M3201A", "M3300A", "M4i", "AWGFileParser", "Infiniium",
                       "KeysightAgilent_33XXX", "Model_336", "Base_SPDT", "RC_SP4T", "RC_SPDT", "USB_SPDT", "ZIUHFLI",
                       "QDac_channels", "RTO1000", "ZNB", "SR860", "SR86x", "AWG5208", "AWG70000A", "AWG70002A",
                       "Keithley_2600_channels", "Keysight_N5183B", "Keysight_N6705B", "N52xx", "AG_UC8",
                       "MercuryiPS_VISA", ]

        path = os.path.dirname(inspect.getfile(qc)) + "\\instrument_drivers"
        brands = get_subfolders(path, True)
        for brand in brands:
            models = get_files_in_folder(path + "\\" + brand, True)
            for model in models:
                if model[0:-3] not in not_working:
                    module_name = "qcodes.instrument_drivers." + brand + "." + model[:-3]
                    module = importlib.import_module(module_name)
                    if model[:-3] not in correct_names.keys():
                        try:
                            my_class = getattr(module, model[:-3])
                        except Exception as e:
                            show_error_message("Warning",str(e))
                        else:
                            self.premade_instruments[model[:-3]] = my_class
                    else:
                        try:
                            my_class = getattr(module, correct_names[model[:-3]])
                        except Exception as e:
                            show_error_message("Warning",str(e))
                        else:
                            self.premade_instruments[model[:-3]] = my_class

    def create_object(self):
        """
        Creates a new instrument object based on data input by user. Adds newly created instrument to the "instruments"
        dictionary in the MainWindow

        Implements most of the error proofing for creating of the instrument object

        Name of the instrument:
            is taken from current text in the QLineEdit.
        Type of the instrument:
            exctracted after selecting instrument from combobox containing all instruments.
        Instrument objects are created with help of the dict in instrument_imports.py file.
        Each key->value pair in that file is a combination of instrument type and the name of the class representing
        that instrument (as set by qcodes development team)

        :return: NoneType
        """
        classname = self.instrument_type.text()
        name = self.instrument_name.text()
        instrument = None
        if classname == "DummyInstrument":
            try:
                instrument = self.premade_instruments[classname](name, gates=["g1", "g2"])
            except Exception as e:
                if "VI_ERROR_RSRC_NFOUND" in str(e):
                    show_error_message("Critical error", str(e) +
                                       "\n\nTranslated to human language: Your address is probably incorrect")
                else:
                    show_error_message("Critical error", str(e))
        else:
            address = self.instrument_address.text()
            try:
                if name == "AWG":
                    address_string = 'TCPIP0::' + address + '::inst0::INSTR'
                    instrument = self.premade_instruments[classname](name, address_string)
                else:
                    instrument = self.premade_instruments[classname](name, address)
            except Exception as e:
                if "VI_ERROR_RSRC_NFOUND" in str(e):
                    show_error_message("Critical error", str(e) +
                                       "\n\nTranslated to human language: Your address is probably incorrect")
                else:
                    show_error_message("Critical error", str(e))
        return instrument
    """""""""""""""""""""
    Helper functions
    """""""""""""""""""""


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Widget([])
    sys.exit(app.exec_())
