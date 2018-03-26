from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QMenu, QPushButton, QLineEdit, QLabel, QMessageBox,\
                            QCheckBox
from PyQt5 import QtGui
from AddInstrumentWidget import Widget
import time
import sys
import os
import inspect

import qcodes as qc
from qcodes.tests.instrument_mocks import DummyInstrument

"""
Remember to change AddInstrumentWidget -> line 78
from create_object, to add_instrument
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()
        self.init_menu_bar()

        self.instruments = {}
        self.station_instruments = {}
        self.dividers = {}

        self.statusBar().showMessage("Ready")
        self.show()

    def init_ui(self):
        """
        Initializes the main window user interface, sets dimensions, position, etc. of a main window
        :return: NoneType
        """

        self.setGeometry(128, 128, 640, 400)
        self.setWindowTitle("qcodes starter")
        self.setWindowIcon(QtGui.QIcon("osciloscope_icon.png"))
        
        labels = ["Lower limit", "Upper limit", "Num", "Step"]
        first_location = [40, 80]
        
        label = QLabel("Parameters", self)
        label.move(25,  25)
        
        for i in range(len(labels)):
            label = QLabel(labels[i], self)
            label.move(first_location[0] + i*150, first_location[1]-25)
        
        self.textbox_lower_limit = QLineEdit(self)
        self.textbox_lower_limit.move(first_location[0], first_location[1])
        self.textbox_lower_limit.resize(130, 30)

        self.textbox_upper_limit = QLineEdit(self)
        self.textbox_upper_limit.move(190, 80)
        self.textbox_upper_limit.resize(130, 30)

        self.textbox_num = QLineEdit(self)
        self.textbox_num.move(340, 80)
        self.textbox_num.resize(130, 30)

        self.textbox_step = QLineEdit(self)
        self.textbox_step.move(490, 80)
        self.textbox_step.resize(130, 30)
        
        label = QLabel("Instruments:", self)
        label.move(25,  130)
        
        self.btn_add_instrument = QPushButton("Add instrument", self)
        self.btn_add_instrument.move(490, 150)
        self.btn_add_instrument.resize(140, 40)
        self.btn_add_instrument.clicked.connect(self.add_new_instrument)
        
        self.btn_run = QPushButton("Run", self)
        self.btn_run.move(560, 320)
        self.btn_run.resize(60, 40)
        self.btn_run.clicked.connect(self.run_qcodes)
        
        self.btn_show_station = QPushButton("Show station", self)
        self.btn_show_station.move(560, 260)
        self.btn_show_station.resize(60, 40)
        self.btn_show_station.clicked.connect(self.show_station)

        self.statusBar().showMessage("Ready")

    def init_menu_bar(self):
        """
        Initializes menu bar, creates actions and submenus within menu bar, connects actions to menu items
        KNOWN PROBLEMS -> ["M3201A", "M3300A", "M4i", "ZIUHFLI"] list of instruments that produce bugs

        :return: NoneType
        """

        exit_action = QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.exit)

        start_new_measurement_menu = QMenu("Add instrument", self)
        start_new_measurement_action = QAction("New", self)
        start_new_measurement_action.triggered.connect(self.add_new_instrument)

        start_new_measurement_menu.addAction(start_new_measurement_action)
        start_new_measurement_menu.addSeparator()

        path = os.path.dirname(inspect.getfile(qc)) + "\\instrument_drivers"
        brands = self.get_subfolders(path, True)
        for brand in brands:
            current_brand_menu = QMenu(brand, self)
            start_new_measurement_menu.addMenu(current_brand_menu)
            models = self.get_files_in_folder(path + "\\" + brand, True)
            for model in models:
                if model[0:-3] not in ["M3201A", "M3300A", "M4i", "ZIUHFLI", "Keithley_2600_channels", "AWGFileParser"]:
                    current_model_action = QAction(model[0:-3], self)
                    current_brand_menu.addAction(current_model_action)
                    current_model_action.triggered.connect(self.add_new_instrument)
                else:
                    current_model_action = QAction(model[0:-3], self)
                    current_model_action.setEnabled(False)
                    current_model_action.setIcon(QtGui.QIcon("disabled.png"))
                    current_brand_menu.addAction(current_model_action)
                    current_model_action.triggered.connect(self.add_new_instrument)


        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(exit_action)
        file_menu.addMenu(start_new_measurement_menu)

    def exit(self):
        """
        Close the main window
        :return: NoneType
        """
        self.close()

    def add_new_instrument(self):
        """
        Opens a new Widget (window) with text inputs for parameters of an instrument, creates new instrument(s)
        :return: NoneType
        """
        self.add_instrument = Widget(self.instruments, parent=self)
        self.add_instrument.show()
        
    def run_qcodes(self):
        """
        Runs qcodes with specified instruments and parameters. Checks for erronrs in data prior to runing qcodes

        :return: NoneType
        """
        
        try:
            self.lower = float(self.textbox_lower_limit.text())
            self.upper = float(self.textbox_upper_limit.text())
            self.num = float(self.textbox_num.text())
            self.step = float(self.textbox_step.text())

            station = qc.Station()
            for key, value in self.instruments.items():

                name = key
                instrument = value[0]
                action = value[1]
                parameter = value[2]

                station.add_component(instrument, name)
                if action == "sweep":
                    sweep_parameter = instrument.parameters[parameter]
                elif action == "measure":
                    measure_parameter = instrument.parameters[parameter]

            try:
                sweep_parameter
            except Exception as e:
                raise NameError("Please define sweep parameter.\n" + str(e))
            try:
                measure_parameter
            except Exception as e:
                raise NameError("Please define measure parameter.\n" + str(e))

            # look into this dmm.v1 (how the hell is this v1 created, some dynamic magical monstrosity)
            # Found it at InstrumentBase.parameters -> dictionary with parameter string as keys
            # C:\Users\nanoelectronics\Anaconda3\envs\qcodes\lib\site-packages\qcodes\instrument\base.py -> line 53
            # lp = qc.Loop(dac.ch1.sweep(self.lower, self.upper, num=self.num), self.step).each(dmm.v1)
            lp = qc.Loop(sweep_parameter.sweep(self.lower, self.upper, num=self.num), self.step).each(measure_parameter)
        except Exception as e:
            warning_string = "Errm, looks like something went wrong ! \nHINT: Measurement parameters not set. \n"\
                             + str(e)
            self.show_error_message("Warning", warning_string)
        else:
            data = lp.run('data/dataset')
        
    def show_station(self):
        """
        Helper function, should get removed when no longer needed, used by developer for testing only

        :return: NoneType
        """
        for key, value in self.instruments.items():
            print(key)
            print(value[0].parameters)

        print("Station instruments")
        for key, value in self.station_instruments.items():
            print(key)
            print(value[0].parameters)

    def update_station_preview(self):
        """
        When new instrument is added, updates the main window to display data about most recent instrument
         added to the instruments dictionary.

        :return: NoneType
        """
        if len(self.instruments) == 1:
            header_string = "Nr." + "       " + "Action" + "      " + "Type" + 4*"\t" + "Dividers"
            new_label = QLabel(header_string, self)
            new_label.move(35, 150)
            new_label.resize(500, 20)
            new_label.show()

        for instrument in self.instruments:
            if instrument not in self.station_instruments:
                display_string = str((len(self.instruments))) + ".      " + self.instruments[instrument][1] + "      " \
                                 + str(self.instruments[instrument][0])
                new_label = QLabel(display_string, self)
                new_label.move(35, 170 + 20*len(self.station_instruments))
                new_label.resize(300, 20)
                new_label.show()

                if self.instruments[instrument][1] == "sweep":
                    self.dividers[instrument] = {}
                    for parameter in self.instruments[instrument][0].parameters:
                        if parameter != "IDN":
                            self.dividers[instrument][parameter] = 1

                    # make it so that changing the value of this filed changes the amp value
                    for i, gate in enumerate(self.dividers[instrument]):
                        input_field = QLineEdit(self)
                        input_field.resize(40, 20)
                        input_field.move(310 + 60*i, 170 + 20*len(self.station_instruments))
                        input_field.show()

                self.station_instruments[instrument] = self.instruments[instrument]

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

    def get_subfolders(self, path, instrument_brands_only=False):
        """
        Helper function to find all folders within folder specified by "path"

        :param path: path to folder to scrap subfolders from
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


def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
