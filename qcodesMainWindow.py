from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QMenu, QPushButton, QLabel, QFrame, QFileDialog, \
    QLineEdit, QShortcut, QTableWidget, QTableWidgetItem, QHeaderView, QTableView
from PyQt5.QtCore import pyqtSlot, QThreadPool

import sys
import inspect

from PyQt5.QtCore import Qt
import qcodes as qc
from Helpers import *
from ViewTree import ViewTree
from TextEditWidget import Notepad
from AddInstrumentWidget import Widget
from SetupLoopsWidget import LoopsWidget
from EditInstrumentWidget import EditInstrumentWidget
from ThreadWorker import Worker, progress_func, print_output, thread_complete, destroy_worker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()
        self.init_menu_bar()

        self.instruments = {}
        self.station_instruments = {}
        self.loops = {}
        self.shown_loops = []
        self.actions = []

        self.edit_button_dict = {}

        # Thread pool for adding separate threads
        # (execute qcodes in another thread [to not freeze GUI thread while executing])
        self.thread_pool = QThreadPool()
        self.workers = []

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

        self.setGeometry(64, 64, 640, 400)
        self.setMinimumSize(640, 400)
        self.setWindowTitle("qcodes starter")
        self.setWindowIcon(QtGui.QIcon("img/osciloscope_icon.png"))
        
        label = QLabel("Instruments:", self)
        label.move(25,  30)

        self.instruments_table = QTableWidget(0, 3, self)
        self.instruments_table.move(45, 65)
        self.instruments_table.resize(400, 160)
        self.instruments_table.setHorizontalHeaderLabels(("Name", "Type", "Edit"))
        header = self.instruments_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.instruments_table.setSelectionBehavior(QTableView.SelectRows)

        label = QLabel("Loops", self)
        label.move(25, 240)
        self.show_loop_details_btn = QPushButton("Show tree", self)
        self.show_loop_details_btn.move(80, 240)
        self.show_loop_details_btn.resize(100, 30)
        icon = QtGui.QIcon("img/binary_tree_icon.png")
        self.show_loop_details_btn.setIcon(icon)
        self.show_loop_details_btn.clicked.connect(self.open_tree)


        self.loops_table = QTableWidget(0, 2, self)
        self.loops_table.move(45, 280)
        self.loops_table.resize(400, 100)
        self.loops_table.setHorizontalHeaderLabels(("Name", "Edit"))
        header = self.loops_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.instruments_table.setSelectionBehavior(QTableView.SelectRows)

        self.btn_add_instrument = QPushButton("Add instrument", self)
        self.btn_add_instrument.move(480, 50)
        self.btn_add_instrument.resize(140, 40)
        icon = QtGui.QIcon("img/osciloscope_icon.png")
        self.btn_add_instrument.setIcon(icon)
        self.btn_add_instrument.clicked.connect(lambda checked, name="DummyInstrument": self.add_new_instrument(name))

        self.btn_setup_loops = QPushButton("Setup loops", self)
        self.btn_setup_loops.move(480, 95)
        self.btn_setup_loops.resize(140, 40)
        icon = QtGui.QIcon("img/measure.png")
        self.btn_setup_loops.setIcon(icon)
        self.btn_setup_loops.clicked.connect(self.setup_loops)

        label = QLabel("Output file name", self)
        label.move(480, 185)
        self.output_file_name = QLineEdit(self)
        self.output_file_name.move(480, 210)
        self.output_file_name.resize(140, 30)

        self.btn_select_save_location = QPushButton("Select save location", self)
        self.btn_select_save_location.move(480, 140)
        self.btn_select_save_location.resize(140, 40)
        icon = QtGui.QIcon("img/save_icon.png")
        self.btn_select_save_location.setIcon(icon)
        self.btn_select_save_location.clicked.connect(self.select_save_location)

        self.stop_btn = QPushButton("STOP", self)
        self.stop_btn.move(480, 280)
        self.stop_btn.resize(140, 40)
        icon = QtGui.QIcon("img/cancel_1-512.png")
        self.stop_btn.setIcon(icon)
        self.stop_btn.clicked.connect(self.stop_all_workers)

        self.open_text_edit_btn = QPushButton("Text", self)
        self.open_text_edit_btn.move(200, 240)
        self.open_text_edit_btn.resize(100, 30)
        self.open_text_edit_btn.clicked.connect(self.open_text_editor)
        icon = QtGui.QIcon("img/text_icon.png")
        self.open_text_edit_btn.setIcon(icon)

        self.plot_btn = QPushButton("Plot", self)
        self.plot_btn.move(480, 330)
        self.plot_btn.resize(60, 40)
        self.plot_btn.clicked.connect(self.run_with_plot)
        icon = QtGui.QIcon("img/plot_icon.png")
        self.plot_btn.setIcon(icon)
        
        self.btn_run = QPushButton("Run", self)
        self.btn_run.move(560, 330)
        self.btn_run.resize(60, 40)
        self.btn_run.clicked.connect(self.run_qcodes)
        icon = QtGui.QIcon("img/play_icon.png")
        self.btn_run.setIcon(icon)

        self.statusBar().showMessage("Ready")

        add_shortcut = QShortcut(QtGui.QKeySequence(Qt.Key_F1), self)
        add_shortcut.activated.connect(self.setup_loops)

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
        start_new_measurement_action.triggered.connect(lambda checked, name="DummyInstrument": self.add_new_instrument(name))

        start_new_measurement_menu.addAction(start_new_measurement_action)
        start_new_measurement_menu.addSeparator()

        path = os.path.dirname(inspect.getfile(qc)) + "\\instrument_drivers"
        brands = get_subfolders(path, True)
        for brand in brands:
            current_brand_menu = QMenu(brand, self)
            start_new_measurement_menu.addMenu(current_brand_menu)
            models = get_files_in_folder(path + "\\" + brand, True)
            for model in models:
                if model[0:-3] not in ["M3201A", "M3300A", "M4i", "ZIUHFLI", "Keithley_2600_channels", "AWGFileParser",
                                       "Keysight_33500B_channels", "Infiniium", "KeysightAgilent_33XXX", "Model_336",
                                       "Base_SPDT", "RC_SP4T", "RC_SPDT", "USB_SPDT", "QDac_channels", "RTO1000", "ZNB",
                                       "SR860", "SR86x", "AWG5208", "AWG70000A", "AWG70002A", "Keithley_2600_channels"]:
                    current_model_action = QAction(model[0:-3], self)
                    current_model_action.setData(model[0:-3])
                    current_brand_menu.addAction(current_model_action)
                    current_model_action.triggered.connect(lambda checked, name=current_model_action.data(): self.add_new_instrument(name))
                else:
                    current_model_action = QAction(model[0:-3], self)
                    current_model_action.setEnabled(False)
                    current_model_action.setIcon(QtGui.QIcon("img/disabled.png"))
                    current_brand_menu.addAction(current_model_action)
                    current_model_action.triggered.connect(lambda checked, name=current_model_action.data(): self.add_new_instrument(name))

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(exit_action)
        file_menu.addMenu(start_new_measurement_menu)

    """""""""""""""""""""
    Data manipulation
    """""""""""""""""""""
    def update_station_preview(self):
        """
        When new instrument is added, updates the main window to display data about most recent instrument
         added to the instruments dictionary.

        :return: NoneType
        """
        for instrument in self.instruments:
            if instrument not in self.station_instruments:
                current_instrument = self.instruments[instrument]
                rows = self.instruments_table.rowCount()
                self.instruments_table.insertRow(rows)
                item = QTableWidgetItem(instrument)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.instruments_table.setItem(rows, 0, item)
                item = QTableWidgetItem(str(current_instrument))
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.instruments_table.setItem(rows, 1, item)
                current_instrument_btn = QPushButton("Edit")
                current_instrument_btn.resize(35, 20)
                current_instrument_btn.clicked.connect(self.make_open_instrument_edit(instrument))
                self.instruments_table.setCellWidget(rows, 2, current_instrument_btn)
                self.edit_button_dict[instrument] = current_instrument_btn
                self.station_instruments[instrument] = self.instruments[instrument]

    def update_loops_preview(self):
        """
        This function is called from child class (SetupLoopsWidget) each time a new loop is created.
        Displays all loops on the MainWindow

        :return: NoneType
        """
        for name, loop in self.loops.items():
            if name not in self.shown_loops:
                rows = self.loops_table.rowCount()
                self.loops_table.insertRow(rows)
                item = QTableWidgetItem(name)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.loops_table.setItem(rows, 0, item)
                current_loop_btn = QPushButton("Edit", self)
                current_loop_btn.resize(35, 20)
                current_loop_btn.clicked.connect(lambda checked, loop_name=name: self.setup_loops(loop_name))
                self.loops_table.setCellWidget(rows, 1, current_loop_btn)
                self.shown_loops.append(name)

    def run_qcodes(self, with_plot=False):
        """
        Runs qcodes with specified instruments and parameters. Checks for errors in data prior to runing qcodes

        :return: NoneType
        """
        station = qc.Station()
        for name, instrument in self.instruments.items():
            station.add_component(instrument, name)

        if len(self.actions):
            loop = self.actions[-1]
            data = loop.get_data_set(name=self.output_file_name.text())

            if with_plot:
                parameter = get_plot_parameter(loop)
                parameter_name = str(parameter)
                plot = qc.QtPlot(fig_x_position=0.05, fig_y_position=0.4)
                plot.add(getattr(data, parameter_name))
                worker = Worker(loop.with_bg_task(plot.update, plot.save).run)
            else:
                worker = Worker(loop.run)
            self.workers.append(worker)

            worker.signals.result.connect(print_output)
            worker.signals.finished.connect(thread_complete)
            worker.signals.progress.connect(progress_func)
            worker.signals.kill.connect(destroy_worker)

            self.thread_pool.start(worker)

        else:
            show_error_message("Oops !", "Looks like there is no loop to be ran !")
        self.statusBar().showMessage("Measurement done")

    def run_with_plot(self):
        self.run_qcodes(with_plot=True)

    @pyqtSlot()
    def select_save_location(self):
        save_location = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        loc_provider = qc.data.location.FormatLocation(fmt=save_location + '/{date}/#{counter}_{name}_{time}')
        qc.data.data_set.DataSet.location_provider = loc_provider

    """""""""""""""""""""
    Helper functions
    """""""""""""""""""""
    @pyqtSlot()
    def exit(self):
        """
        Close the main window
        :return: NoneType
        """
        for name, instrument in self.instruments.items():
            print("Closing", instrument)
            instrument.close()

        self.close()

    @pyqtSlot()
    def add_new_instrument(self, name):
        """
        Opens a new Widget (window) with text inputs for parameters of an instrument, creates new instrument(s)
        :return: NoneType
        """
        self.add_instrument = Widget(self.instruments, parent=self, default=name)
        self.add_instrument.show()

    @pyqtSlot()
    def open_tree(self):
        """
        Open a TreeView to inspect created loops

        :return: NoneType
        """
        self.view_tree = ViewTree({name: loop.snapshot_base() for name, loop in self.loops.items()})
        self.view_tree.show()

    @pyqtSlot()
    def setup_loops(self, loop_name=""):
        """
        Open a new widget for creating loops based on instruments added to "instruments" dictionary trough
        AddInstrumentWidget. Loops created with this widget are added to MainWindows "loops" dictionary, also for each
        loop an action to be executed is created and added to MainWindows "actions" list

        :return:
        """
        self.setup_loops_widget = LoopsWidget(self.instruments, self.loops, self.actions, parent=self, loop_name=loop_name)
        self.setup_loops_widget.show()

    @pyqtSlot()
    def open_text_editor(self):
        """
        Open a simple text editor as a new widget (possible custom tool creation)

        :return: NoneType
        """
        self.text_editor = Notepad()
        self.text_editor.show()

    def stop_all_workers(self):
        for worker in self.workers:
            pass

    # This is a function factory
    def make_open_instrument_edit(self, instrument):
        """
        Hi, i am a function factory, and for each button you see next to an instrument i create a new function to edit
        that particular instrument. After creating that function i return it so it can be called with a click on the
        button.

        :param instrument: refers to an instrument to be edited
        :return: newly created function to open "EditInstrumentWidget" with this particular instrument
        """
        def open_instrument_edit():
            """
            Open a new widget and pass it an instrument that can be edited through the newly opened widget

            :return: NoneType
            """
            self.edit_instrument = EditInstrumentWidget(self.instruments, parent=self, instrument_name=instrument)
            self.edit_instrument.show()
        return open_instrument_edit


def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
