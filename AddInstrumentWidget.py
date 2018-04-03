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


class Widget(QWidget):

    def __init__(self, instruments, parent=None, default="DummyInstrument"):
        """
        Constructor for AddInstrumentWidget window

        :param instruments: Dictionary shared with parent (MainWindow) to be able to add instruments to instruments
        dictionary in the MainWindow
        :param parent: specify object that created this widget
        """
        super(Widget, self).__init__()
        self.instruments = instruments
        self.premade_instruments = {}
        self.populate_premade_instruments()
        self.parent = parent
        self.default = default
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
        self.setWindowTitle("Add new instrument")
        self.setWindowIcon(QtGui.QIcon("osciloscope_icon.png"))
        
        self.cb = QComboBox(self)
        self.cb.move(20, 20)
        self.cb.resize(280, 30)
        for key, value in self.premade_instruments.items():
            self.cb.addItem(key)
        index = self.cb.findText(self.default)
        self.cb.setCurrentIndex(index)
        self.cb.currentIndexChanged.connect(self.update_instrument_data)
        
        self.label = QLabel("Type", self)
        self.label.move(20, 65)
        self.instrument_type = QLineEdit(self)
        self.instrument_type.move(20, 80)
        self.instrument_type.setEnabled(False)
        
        self.label = QLabel("Name", self)
        self.label.move(20, 115)
        self.instrument_name = QLineEdit(self)
        self.instrument_name.move(20, 130)
        
        self.address_label = QLabel("Address", self)
        self.address_label.move(20, 165)
        self.address_label.resize(400, 15)
        self.instrument_address = QLineEdit(self)
        self.instrument_address.move(20, 180)

        self.ok_button = QPushButton("OK", self)
        self.ok_button.move(20, 220)
        self.ok_button.clicked.connect(self.add_instrument)

        self.label_type = QLabel("Type: ", self)
        self.label_type.move(180, 65)
        self.label_num_gates = QLabel("Num. of gates: ", self)
        self.label_num_gates.move(180, 80)
        
        self.update_instrument_data()

    def add_instrument(self):
        """
        Called upon clicking OK. Adds instrument (based on user input) to the instrument dictionary in the main window.
        Data structure -> instruments[name] : [instrument object, sweep/measure, gate to sweep/observe]
        """

        if self.validate_instrument_input():
            return
                
        name = self.instrument_name.text()
        instrument = None
        try:
            instrument = self.create_object()
        except Exception as e:
            show_error_message("Warning", str(e))

        if instrument is not None:
            self.instruments[name] = instrument
            self.parent.update_station_preview()
            self.close()
        
    def update_instrument_data(self):
        """
        Upon selecting one of instruments from dropdown, updates input fields with data availible from class

        :return: NoneType
        """

        instrument_type = self.cb.currentText()
        instrument_class = self.premade_instruments[instrument_type]
        self.instrument_type.setText(instrument_type)

        if issubclass(instrument_class, IPInstrument):
            pass
        elif issubclass(instrument_class, VisaInstrument):
            pass

    """""""""""""""""""""
    Data manipulation
    """""""""""""""""""""
    def validate_instrument_input(self):
        """
        Make sure all fields required for creating an object of a class are filled in with valid data

        :return: True if there is an error, False if there is no errors
        """
        name = self.instrument_name.text()
        address = self.instrument_address.text()

        if len(name) < 1:
            error_message = "Please specify instrument name."
        elif name in self.instruments:
            error_message = "Another instrument already has name: {}" + name + \
                            ". Please change the name of your isntrument"
        elif len(address) < 1:
            error_message = "Please specify instrument address"
        else:
            error_message = ""
        
        if error_message != "":
            show_error_message("Warning", error_message)
            return True
        else:
            return False

    def populate_premade_instruments(self):
        """
        Walks through folder structure and fetches instruments and their classes for further use

        :return: NoneType
        """
        self.premade_instruments["DummyInstrument"] = getattr(importlib.import_module("qcodes.tests.instrument_mocks"), "DummyInstrument")
        not_working = ["Keysight_33500B_channels", "M3201A", "M3300A", "M4i", "ZIUHFLI", "AWGFileParser"]

        path = os.path.dirname(inspect.getfile(qc)) + "\\instrument_drivers"
        brands = get_subfolders(path, True)
        for brand in brands:
            models = get_files_in_folder(path + "\\" + brand, True)
            for model in models:
                if model[0:-3] not in not_working:
                    module_name = "qcodes.instrument_drivers." + brand + "." + model[:-3]
                    module = importlib.import_module(module_name)
                    my_class = 0
                    if model[:-3] not in correct_names.keys():
                        try:
                            my_class = getattr(module, model[:-3])
                        except Exception as e:
                            print(str(e))
                        finally:
                            self.premade_instruments[model[:-3]] = my_class
                    else:
                        try:
                            my_class = getattr(module, correct_names[model[:-3]])
                        except Exception as e:
                            print(str(e))
                        finally:
                            self.premade_instruments[model[:-3]] = my_class

    def create_object(self):
        """
        Creates a new instrument object based on data input by user. Adds newly created instrument to the "instruments"
        dictionary in the MainWindow

        Implements most of the error proofing for creating of the instrument object

        Name of the instrument is taken from current text in the QLineEdit.
        Type of the instrument exctracted after selecting instrument from combobox containing all instruments.
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
