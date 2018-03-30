from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QMenu, QPushButton, QLabel, QFrame, QFileDialog, QLineEdit
from AddInstrumentWidget import Widget
from SetupLoopsWidget import LoopsWidget
from AttachDividersWidget import DividerWidget
import sys
import inspect

import qcodes as qc
from Helpers import *
from ViewTree import ViewTree
from TextEditWidget import Notepad


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()
        self.init_menu_bar()

        self.instruments = {}
        self.station_instruments = {}
        self.loops = {}
        self.shown_loops = {}
        self.actions = []

        self.statusBar().showMessage("Ready")
        self.show()

    """""""""""""""""""""
    User interface
    """""""""""""""""""""
    def init_ui(self):
        """
        Initializes the main window user interface, sets dimensions, position, etc. of a main window
        :return: NoneType
        """

        self.setGeometry(128, 128, 640, 400)
        self.setMinimumSize(640, 400)
        self.setWindowTitle("qcodes starter")
        self.setWindowIcon(QtGui.QIcon("osciloscope_icon.png"))
        
        label = QLabel("Instruments:", self)
        label.move(25,  30)

        self.instruments_frame = QFrame(self)
        self.instruments_frame.move(45, 65)
        self.instruments_frame.setFrameShape(QFrame.StyledPanel)
        self.instruments_frame.setFrameShadow(QFrame.Sunken)
        self.instruments_frame.resize(400, 160)
        self.instruments_frame.setStyleSheet("background-color: rgb(245, 245, 245)")

        label = QLabel("Loops", self)
        label.move(25, 240)
        self.show_loop_details_btn = QPushButton("Show tree", self)
        self.show_loop_details_btn.move(80, 240)
        self.show_loop_details_btn.resize(100, 30)
        self.show_loop_details_btn.clicked.connect(self.open_tree)
        self.loops_frame = QFrame(self)
        self.loops_frame.move(45, 280)
        self.loops_frame.setFrameShape(QFrame.StyledPanel)
        self.loops_frame.setFrameShadow(QFrame.Sunken)
        self.loops_frame.resize(400, 100)
        self.loops_frame.setStyleSheet("background-color: rgb(245, 245, 245)")
        
        self.btn_add_instrument = QPushButton("Add instrument", self)
        self.btn_add_instrument.move(490, 50)
        self.btn_add_instrument.resize(140, 40)
        self.btn_add_instrument.clicked.connect(self.add_new_instrument)

        self.btn_setup_loops = QPushButton("Setup loops", self)
        self.btn_setup_loops.move(490, 110)
        self.btn_setup_loops.resize(140, 40)
        self.btn_setup_loops.clicked.connect(self.setup_loops)

        self.btn_setup_loops = QPushButton("Attach dividers", self)
        self.btn_setup_loops.move(490, 170)
        self.btn_setup_loops.resize(140, 40)
        self.btn_setup_loops.clicked.connect(self.attach_dividers)

        label = QLabel("Output file name", self)
        label.move(380, 240)
        self.output_file_name = QLineEdit(self)
        self.output_file_name.move(480, 240)
        self.output_file_name.resize(140, 30)

        self.btn_select_save_location = QPushButton("Select save location", self)
        self.btn_select_save_location.move(480, 280)
        self.btn_select_save_location.resize(140, 40)
        self.btn_select_save_location.clicked.connect(self.select_save_location)

        self.open_text_edit_btn = QPushButton("Text", self)
        self.open_text_edit_btn.move(480, 330)
        self.open_text_edit_btn.resize(60, 40)
        self.open_text_edit_btn.clicked.connect(self.open_text_editor)
        
        self.btn_run = QPushButton("Run", self)
        self.btn_run.move(560, 330)
        self.btn_run.resize(60, 40)
        self.btn_run.clicked.connect(self.run_qcodes)

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
        start_new_measurement_action.setShortcut("Ctrl+M")
        start_new_measurement_action.setStatusTip("Open 'Add New Instrument' window")
        start_new_measurement_action.triggered.connect(self.add_new_instrument)

        start_new_measurement_menu.addAction(start_new_measurement_action)
        start_new_measurement_menu.addSeparator()

        path = os.path.dirname(inspect.getfile(qc)) + "\\instrument_drivers"
        brands = get_subfolders(path, True)
        for brand in brands:
            current_brand_menu = QMenu(brand, self)
            start_new_measurement_menu.addMenu(current_brand_menu)
            models = get_files_in_folder(path + "\\" + brand, True)
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

    """""""""""""""""""""
    Data manipulation
    """""""""""""""""""""
    def add_new_instrument(self):
        """
        Opens a new Widget (window) with text inputs for parameters of an instrument, creates new instrument(s)
        :return: NoneType
        """
        self.add_instrument = Widget(self.instruments, parent=self)
        self.add_instrument.show()

    def update_station_preview(self):
        """
        When new instrument is added, updates the main window to display data about most recent instrument
         added to the instruments dictionary.

        :return: NoneType
        """
        if len(self.instruments) == 1:
            header_string = "Nr." + "       " + "Type" + 4*"\t" + "Dividers"
            new_label = QLabel(header_string, self)
            new_label.move(60, 75)
            new_label.resize(500, 20)
            new_label.show()

        for instrument in self.instruments:
            if instrument not in self.station_instruments:
                current_instrument = self.instruments[instrument]
                display_string = str((len(self.instruments))) + ".      " + str(current_instrument) + ".      " + \
                                 str([i for i in current_instrument.parameters.keys()])
                new_label = QLabel(display_string, self)
                new_label.move(60, 95 + 20*len(self.station_instruments))
                new_label.resize(300, 20)
                new_label.show()

                self.station_instruments[instrument] = self.instruments[instrument]

    def update_loops_preview(self):
        """
        This function is called from child class (SetupLoopsWidget) each time a new loop is created.
        Displays all loops on the MainWindow

        :return: NoneType
        """
        for name, loop in self.loops.items():
            if name not in self.shown_loops:
                self.shown_loops[name] = True
                sweep_parameter_string = loop.snapshot_base()["sweep_values"]["parameter"]["full_name"]
                actions = ""
                for action in loop.snapshot_base()["actions"]:
                    actions += str(action)
                new_label = QLabel(name + "\t sweep on: " + sweep_parameter_string + "\t actions:" + actions, self)
                new_label.move(60, 270 + 20 * len(self.loops))
                new_label.resize(300, 20)
                new_label.show()

    def run_qcodes(self):
        """
        Runs qcodes with specified instruments and parameters. Checks for errors in data prior to runing qcodes

        :return: NoneType
        """
        station = qc.Station()
        for name, instrument in self.instruments.items():
            station.add_component(instrument, name)

        if len(self.actions) > 0:
            if len(self.actions) == 1:
                data = self.actions[0].get_data_set(name=self.output_file_name.text())
                self.actions[0].run()

                """instrument = self.actions[0]["actions"][0]["instrument"]
                parameter = instrument.self.actions[0]["actions"][0]["name"]

                print(data)
                plot = qc.QtPlot()
                plot.add(data.parameter)"""

            else:
                # find out what to do when more loops are to be run
                data = self.actions[0].get_data_set(name=self.output_file_name.text())
                self.actions[-1].run()
        else:
            show_error_message("Oops !", "Looks like there is no loop to be ran !")
        self.statusBar().showMessage("Measurement done")

    def setup_loops(self):
        """
        Open a new widget for creating loops based on instruments added to "instruments" dictionary trough
        AddInstrumentWidget. Loops created with this widget are added to MainWindows "loops" dictionary, also for each
        loop an action to be executed is created and added to MainWindows "actions" list

        :return:
        """
        self.setup_loops_widget = LoopsWidget(self.instruments, self.loops, self.actions, parent=self)
        self.setup_loops_widget.show()

    def open_tree(self):
        """
        Open a TreeView to inspect created loops

        :return: NoneType
        """
        self.view_tree = ViewTree({name: loop.snapshot_base() for name, loop in self.loops.items()})
        self.view_tree.show()

    def attach_dividers(self):
        """
        Open a widget for attaching dividers to parameters (not used, implemented a better solution)

        :return: NoneType
        """
        self.divider_widget = DividerWidget(self.instruments, parent=self)
        self.divider_widget.show()

    def open_text_editor(self):
        """
        Open a simple text editor as a new widget (possible custom tool creation)

        :return: NoneType
        """
        self.text_editor = Notepad()
        self.text_editor.show()

    def select_save_location(self):
        save_location = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        loc_provider = qc.data.location.FormatLocation(fmt=save_location + '/{date}/#{counter}_{name}_{time}')
        qc.data.data_set.DataSet.location_provider = loc_provider

    """""""""""""""""""""
    Helper functions
    """""""""""""""""""""
    # Helpers moved to separate file - Helpers.py (functions are shared with others windows)


def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
