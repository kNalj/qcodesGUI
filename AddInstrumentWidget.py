from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QLabel, QComboBox, QVBoxLayout, \
    QRadioButton, QMessageBox
from PyQt5 import QtGui
import sys
import os

from qcodes.tests.instrument_mocks import DummyInstrument
from instrument_imports import *


class Widget(QWidget):

    def __init__(self, instruments, parent=None):
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
        self.init_ui()
        self.show()

    def init_ui(self):
        """
        Initialisation of the user interface (as the function name suggests)

        :return: NoneType
        """

        self.setGeometry(256, 256, 320, 260)
        self.setWindowTitle("Add new instrument")
        self.setWindowIcon(QtGui.QIcon("osciloscope_icon.png"))
        
        self.cb = QComboBox(self)
        self.cb.move(20, 20)
        self.cb.resize(280, 30)
        for key, value in self.premade_instruments.items():
            self.cb.addItem(key)
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
        
        self.label = QLabel("Gates (example: v1, v2)", self)
        self.label.move(20, 165)
        self.instrument_gates = QLineEdit(self)
        self.instrument_gates.move(20, 180)

        self.b1 = QRadioButton("Sweep", self)
        self.b1.move(200, 80)
        self.b2 = QRadioButton("Measure", self)
        self.b2.move(200, 100)

        self.label = QLabel("Observed gate", self)
        self.label.move(160, 165)
        self.observed_gate = QLineEdit(self)
        self.observed_gate.move(160, 180)

        self.ok_button = QPushButton("OK", self)
        self.ok_button.move(20, 220)
        self.ok_button.resize(280, 30)
        #self.ok_button.clicked.connect(self.add_instrument)
        self.ok_button.clicked.connect(self.create_object)
        
        self.update_instrument_data()

    def add_instrument(self):
        """
        Called upon clicking OK. Adds instrument (based on user input) to the instrument dictionary in the main window.
        Data structure -> instruments[name] : [instrument object, sweep/measure, gate to sweep/observe]
        """

        if self.validate_instrument_input():
            return
                
        instrument = self.premade_instruments[self.instrument_type.text()]
        gates = self.instrument_gates.text().split(",")
        name = self.instrument_name.text()
        gate = self.observed_gate.text()
        
        if self.b1.isChecked():  # sweep
            self.instruments[name] = [instrument(name, gates=gates), "sweep", gate]
        elif self.b2.isChecked():
            self.instruments[name] = [instrument(name, gates=gates), "measure", gate]

        self.parent.update_station_preview()
        self.close()
        
    def update_instrument_data(self):
        """
        Upon selecting one of instruments from dropdown, updates input fields with data availible from class

        :return: NoneType
        """
        
        self.instrument_type.setText(self.cb.currentText())
        self.instrument_gates.setText("g1,g2,g3")
        
    def show_error_message(self, title, message):
        """
        Function for displaying warnings/errors

        :param title: Title of the displayed watning window
        :param message: Message shown by the displayed watning window
        :return: NoneType
        """
        msg_box = QMessageBox()
        msg_box.setIcon(QtGui.QMessageBox.Warning)
        msg_box.setWindowIcon(QtGui.QIcon("warning_icon.png"))
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QtGui.QMessageBox.Ok)
        msg_box.exec_()
        
    def validate_instrument_input(self):
        """
        Make sure all fields required for creating an object of a class are filled in with valid data

        :return: NoneType
        """
        if len(self.instrument_name.text()) < 1:
            # should also check is there is an instrument with a same name
            error_message = "Please specify instrument name."
        elif len(self.instrument_gates.text()) < 1:
            # validate with REGEX maaaaybe ?
            error_message = "Please specify instrument gates."
        elif len(self.observed_gate.text()) < 1:
            # should add check if specified gate is withing gates
            error_message = "Please specify observed gate."
        elif self.observed_gate.text() not in self.instrument_gates.text().split(","):
            error_message = "Observed gate not in list of instrument gates " \
                            + str(self.instrument_gates.text().split(","))
        elif self.b1.isChecked() is False and self.b2.isChecked() is False:
            error_message = "Please specify instrument action (sweep/measure)"
        else:
            error_message = ""
        
        if error_message != "":
            self.show_error_message("Warning", error_message)
            return True
        else:
            return False

    def populate_premade_instruments(self):
        pass

    def instanciate_instrument_from_classname(self, classname):
        """
        Function that creates object of "classname" class and returns it

        :param classname: name of the instrument class as a string
        :return: instance of a "classname" class
        """
        id = classname
        constructor = globals()[id]
        #print(type(constructor()))
        return constructor()

    def create_object(self):
        self.instanciate_instrument_from_classname(self.instrument_type.text())

    def get_subfolders(self, path, instrument_brands_only=False):
        """
        Helper function to find all folders within folder specified by "path"

        :param path: path to folder to scrap subfolders from
        :param instrument_brands_only: set to True if you want to filter brands of instruments only
        :return: list[] of subfolders from specified path
        """
        if instrument_brands_only:
            return [f.name for f in os.scandir(path) if f.is_dir() and f.name[0] != "_"]
        return [f.name for f in os.scandir(path) if f.is_dir() and f.name[0]]

    def get_files_in_folder(self, path, instrument_drivers_only=False):
        """
        Helper function to find all files within folder specified by path

        :param path: path to folder to scrap files from
        :param instrument_drivers_only: if True, apply set of rules that filter only instrument driver files
        :return: list[] of files from specified path
        """
        if instrument_drivers_only:
            return[f.name for f in os.scandir(path) if f.is_file() and f.name[0].upper() == f.name[0] and f.name[0] != "_"]
        return[f.name for f in os.scandir(path) if f.is_file()]


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Widget([])
    sys.exit(app.exec_())
