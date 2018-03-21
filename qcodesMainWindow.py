from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QMenu, QPushButton, QLineEdit, QLabel
from PyQt5 import QtGui
from AddInstrumentWidget import Widget
import time
import sys

import qcodes as qc
from qcodes.tests.instrument_mocks import DummyInstrument

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()
        self.init_menu_bar()

        self.instruments = {}

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
        
        self.label = QLabel("Parameters", self)
        self.label.move(25,  25)
        
        for i in range(len(labels)):
            self.label = QLabel(labels[i], self)
            self.label.move(first_location[0] + i*150, first_location[1]-25)
        
        self.textbox_lower_limit = QLineEdit(self)
        self.textbox_lower_limit.move(first_location[0],first_location[1])
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
        
        self.label = QLabel("Instruments", self)
        self.label.move(25,  130)
        
        self.btn_add_instrument = QPushButton("Add instrument", self)
        self.btn_add_instrument.move(490,150)
        self.btn_add_instrument.resize(140, 40)
        self.btn_add_instrument.clicked.connect(self.add_new_instrument)
        
        self.btn_run = QPushButton("Run", self)
        self.btn_run.move(560,320)
        self.btn_run.resize(60, 40)
        self.btn_run.clicked.connect(self.run_qcodes)
        
        self.btn_show_station = QPushButton("Show station instruments", self)
        self.btn_show_station.move(560,260)
        self.btn_show_station.resize(60, 40)
        self.btn_show_station.clicked.connect(self.show_station)

        self.statusBar().showMessage("Ready")

    def init_menu_bar(self):
        """
        Initializes menu bar, creates actions and submenus within menu bar, connects actions to menu items
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
        self.add_instrument = Widget(self.instruments)
        self.add_instrument.show()
        
    def run_qcodes(self):
        
        #should enclose into try-catch
        self.lower = float(self.textbox_lower_limit.text()) if self.textbox_lower_limit.text() != "" else 0
        self.upper = float(self.textbox_upper_limit.text()) if self.textbox_upper_limit.text() != "" else 1
        self.num = float(self.textbox_num.text()) if self.textbox_num.text() != "" else 10
        self.step = float(self.textbox_step.text()) if self.textbox_step.text() != "" else 0
        
        station = qc.Station()
        for key, value in self.instruments.items():
            station.add_component(value[0], key)
            if value[1] == "sweep":
                sweep_parameter  = self.instruments[key][0].parameters[value[2]]
            elif value[1] == "measure":
                measure_parameter = self.instruments[key][0].parameters[value[2]]
        
        #look into this dmm.v1 (how the hell is this v1 created, some dynamic magical monstrosity)
        #Found it at InstrumentBase.parameters -> dictionary with parameter string as keys
        #C:\Users\nanoelectronics\Anaconda3\envs\qcodes\lib\site-packages\qcodes\instrument\base.py -> line 53
        #lp = qc.Loop(dac.ch1.sweep(self.lower, self.upper, num=self.num), self.step).each(dmm.v1)
        lp = qc.Loop(sweep_parameter.sweep(self.lower, self.upper, num=self.num), self.step).each(measure_parameter)
        data = lp.run('data/dataset')
        
    def show_station(self):
        for key, value in self.instruments.items():
            print(key)
            print(value[0].parameters)
        
    
#pprint(station.snapshot())
#print(data.snapshot())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())
