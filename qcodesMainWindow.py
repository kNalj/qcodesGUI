from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QMenu, QPushButton, QLabel, QFileDialog, \
    QLineEdit, QShortcut, QTableWidget, QTableWidgetItem, QHeaderView, QTableView, QDesktopWidget, QComboBox, QWidget, \
    QGridLayout, QSizePolicy, QSplitter, QHBoxLayout
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThreadPool

import sys
import inspect
from random import randint

from PyQt5.QtCore import Qt
import qcodes as qc
from qcodes.actions import _QcodesBreak
from qcodes.actions import Task

from Helpers import *
from Random import random
from ViewTree import ViewTree
from TextEditWidget import Notepad
from AddInstrumentWidget import Widget
from SetupLoopsWidget import LoopsWidget
from InstrumentData import instrument_data
from AttachDividersWidget import DividerWidget
from EditInstrumentWidget import EditInstrumentWidget
from ThreadWorker import Worker, progress_func, print_output


def trap_exc_during_debug(exctype, value, traceback, *args):
    # when app raises uncaught exception, print info
    print(args)
    print(exctype, value, traceback)


# install exception hook: without this, uncaught exception would cause application to exit
sys.excepthook = trap_exc_during_debug


class MainWindow(QMainWindow):

    loop_started = pyqtSignal()
    loop_finished = pyqtSignal()

    def __init__(self):
        super().__init__()

        # call a function that initializes user interface
        self.init_ui()
        # call a function that initializes menu bar
        self.init_menu_bar()

        # self.instruments is a dictionary containing all instruments that have been connected so far. Form of the dict
        # is: key:value where key is the name of the instrument assigned by you when creating the instrument, and value
        # contains that particular instance of that instrument.
        self.instruments = {}

        # station instruments are used to keep track of the instruments that were added to the instruments table on the
        # main window, each time an instrument is added to the table it is also added to this dict to keep track of
        # which instruments are already displayed
        self.station_instruments = {}

        # loops dictionary containing all loops that have been created so far. Form: key : value where key is the name
        # of the loop that is assigned automatically in order of creation of loops (loop1, loop2, loop3, ...), and the
        # value is an instance of that loop
        self.loops = {}

        # dividers dict holds data about all dividers created so far. Form of the data inside: key : value where key
        # is name of the parameter that the divider is attached to, and value is instance of that particular divider.
        self.dividers = {}

        # Keeping track of the loops that are already displayed in table on the main window (to avoid duplicate adding)
        self.shown_loops = []

        # actions is a list containing list of all loops and the last loop added to this list is the one that will get
        # ran by the run/plot button. I have created this because dictionaries do not have predefined way of puting data
        # into it, meaning that the order of adding items to the dictionary may or may not be the same as the order of
        # getting that same data from the dictionary
        self.actions = []

        # list of references to the EditInstrumentWidget windows that are currently open, used to start live updating
        # of parameters of each of those windows after a measurement has been started. That way only the ones that are
        # currently opened will be automatically self updating
        self.active_isntruments = []

        # instrument workers is a list of handles to the workers that do the above explained actions. Reason for keeping
        # this list is because these workers have to be stopped at some point.
        self.instrument_workers = []

        # contains references to buttons for editing
        self.edit_button_dict = {}

        # Thread pool for adding separate threads
        # (execute qcodes in another thread [to not freeze GUI thread while executing])
        self.thread_pool = QThreadPool()

        # Handles to all active workers (with the idea of stopping them). Contains only workers that run loops, other
        # other workers are stored in different lists
        self.workers = []

        # check this to see if stop has been requested
        self.stop_loop_requested = True

        # holds string representation of folder in which to save measurement data
        self.save_location = ""

        # keep track of number of line traces currently display. Used when loop in a loop is ran to draw the last n
        # line traces only
        self.line_trace_count = 0

        # keep track of live plots in case someone closes one of them that they can be reopened
        self.live_plots = []

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
        # get dimensions of the monitor, and position the window accordingly
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        self.setGeometry(int(0.02 * width), int(0.05 * height), 640, 440)
        # define the size, title and icon of the window
        self.setMinimumSize(640, 440)
        self.setWindowTitle("qcodes starter")
        self.setWindowIcon(QtGui.QIcon("img/osciloscope_icon.png"))

        self.grid_layout = QGridLayout()
        self.splitter = QSplitter(Qt.Vertical)
        self.grid_layout.addWidget(self.splitter, 0, 0, 9, 6)

        self.cw = QWidget(self)
        self.cw.setLayout(self.grid_layout)
        self.setCentralWidget(self.cw)

        # Create and define table for displaying instruments added to the self.instruments dictionary
        label = QLabel("Instruments:")
        self.splitter.addWidget(label)
        self.instruments_table = QTableWidget(0, 3)
        self.splitter.addWidget(self.instruments_table)
        self.instruments_table.setHorizontalHeaderLabels(("Name", "Type", "Edit"))
        header = self.instruments_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.instruments_table.setSelectionBehavior(QTableView.SelectRows)

        horizontal = QSplitter()

        # Create and define table for displaying loops added to the self.loops dictionary
        label = QLabel("Loops")
        horizontal.addWidget(label)
        self.splitter.addWidget(horizontal)

        # Button for displaying data structure of each created loop
        self.show_loop_details_btn = QPushButton("Show tree", self.cw)
        horizontal.addWidget(self.show_loop_details_btn)
        icon = QtGui.QIcon("img/binary_tree_icon.png")
        self.show_loop_details_btn.setIcon(icon)
        self.show_loop_details_btn.clicked.connect(self.open_tree)

        # simple text editor
        self.open_text_edit_btn = QPushButton("Text", self.cw)
        horizontal.addWidget(self.open_text_edit_btn)
        self.open_text_edit_btn.clicked.connect(self.open_text_editor)
        icon = QtGui.QIcon("img/text_icon.png")
        self.open_text_edit_btn.setIcon(icon)

        self.loops_table = QTableWidget(0, 4)
        self.loops_table.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        self.splitter.addWidget(self.loops_table)
        self.loops_table.setHorizontalHeaderLabels(("Name", "Edit", "Run", "Delete"))
        header = self.loops_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.instruments_table.setSelectionBehavior(QTableView.SelectRows)


        # Button for opening a new window that is used for connecting to instruments
        self.btn_add_instrument = QPushButton("Add instrument")
        self.grid_layout.addWidget(self.btn_add_instrument, 0, 6, 1, 2)
        self.btn_add_instrument.resize(200, 200)
        icon = QtGui.QIcon("img/osciloscope_icon.png")
        self.btn_add_instrument.setIcon(icon)
        self.btn_add_instrument.clicked.connect(lambda checked, name="DummyInstrument": self.add_new_instrument(name))

        # Button to open a window that is used to create and manage loops (measurements)
        self.btn_setup_loops = QPushButton("Setup loops")
        self.grid_layout.addWidget(self.btn_setup_loops, 1, 6, 1, 2)
        icon = QtGui.QIcon("img/measure.png")
        self.btn_setup_loops.setIcon(icon)
        self.btn_setup_loops.clicked.connect(self.setup_loops)

        # Button to open a new window that is used for creating, editing and deleting dividers
        self.btn_attach_dividers = QPushButton("Attach dividers")
        self.grid_layout.addWidget(self.btn_attach_dividers, 2, 6, 1, 2)
        icon = QtGui.QIcon("img/rheostat_icon.png")
        self.btn_attach_dividers.setIcon(icon)
        self.btn_attach_dividers.clicked.connect(self.open_attach_divider)

        # text box used to input the desired name of your output file produced by the loop
        label = QLabel("Output file name")
        self.grid_layout.addWidget(label, 4, 6, 1, 1)
        self.output_file_name = QLineEdit()
        self.grid_layout.addWidget(self.output_file_name, 5, 6, 1, 2)


        # btn that opens file dialog for selecting a desired location where to save the ouput file of the loop
        self.btn_select_save_location = QPushButton("Select save location")
        self.grid_layout.addWidget(self.btn_select_save_location, 6, 6, 1, 2)
        icon = QtGui.QIcon("img/save_icon.png")
        self.btn_select_save_location.setIcon(icon)
        self.btn_select_save_location.clicked.connect(self.select_save_location)

        # btn for stoping all currently active loops
        self.stop_btn = QPushButton("STOP")
        self.grid_layout.addWidget(self.stop_btn, 7, 6, 1, 2)
        icon = QtGui.QIcon("img/cancel_1-512.png")
        self.stop_btn.setIcon(icon)
        self.stop_btn.clicked.connect(self.stop_all_workers)

        # run a loop with live ploting as a backgroud task (new window with self updating plot will be opened)
        """self.plot_btn = QPushButton("Plot", self)
        self.plot_btn.move(480, 340)
        self.plot_btn.resize(60, 40)
        self.plot_btn.clicked.connect(self.run_with_plot)
        icon = QtGui.QIcon("img/plot_icon.png")
        self.plot_btn.setIcon(icon)"""

        self.select_loop_cb = QComboBox()
        self.grid_layout.addWidget(self.select_loop_cb, 8, 6, 1, 1)

        # run a loop without displaying the live plot
        self.btn_run = QPushButton("Run")
        self.grid_layout.addWidget(self.btn_run, 8, 7, 1, 1)
        self.btn_run.clicked.connect(self.run_with_plot)
        icon = QtGui.QIcon("img/play_icon.png")
        self.btn_run.setIcon(icon)

        self.statusBar().showMessage("Ready")

        # Defining all shortcuts
        add_shortcut = QShortcut(QtGui.QKeySequence(Qt.Key_F12), self.cw)
        add_shortcut.activated.connect(self.setup_loops)

        # self.setCentralWidget(self)

    def init_menu_bar(self):
        """
        Initializes menu bar, creates actions and submenus within menu bar, connects actions to menu items
        KNOWN PROBLEMS -> ["M3201A", "M3300A", "M4i", "ZIUHFLI"] list of instruments that produce bugs

        :return: NoneType
        """
        # Create action and bind it to a function that exits the application and closes all of its windows
        exit_action = QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.exit)

        # Action for adding a new instrument
        start_new_measurement_menu = QMenu("Add instrument", self)
        start_new_measurement_action = QAction("New", self)
        start_new_measurement_action.setShortcut("Ctrl+M")
        start_new_measurement_action.setStatusTip("Open 'Add New Instrument' window")
        start_new_measurement_action.triggered.connect(lambda checked, name="DummyInstrument": self.add_new_instrument(name))

        start_new_measurement_menu.addAction(start_new_measurement_action)
        start_new_measurement_menu.addSeparator()

        # fetch all instruments defined in qcodes and add then to the Add Instrument menu. Clicking any of these will
        # open AddInstrumentWidget with data for this instrument already filled in that window
        path = os.path.dirname(inspect.getfile(qc)) + "\\instrument_drivers"
        brands = get_subfolders(path, True)
        for brand in brands:
            current_brand_menu = QMenu(brand, self)
            start_new_measurement_menu.addMenu(current_brand_menu)
            models = get_files_in_folder(path + "\\" + brand, True)
            for model in models:
                if model[0:-3] not in ["M3201A", "M3300A", "M4i", "Keithley_2600_channels", "AWGFileParser",
                                       "Keysight_33500B_channels", "Infiniium", "KeysightAgilent_33XXX", "Model_336",
                                       "Base_SPDT", "RC_SP4T", "RC_SPDT", "USB_SPDT", "QDac_channels", "RTO1000", "ZNB",
                                       "SR860", "SR86x", "AWG5208", "AWG70000A", "AWG70002A", "Keithley_2600_channels"]:
                    # above is the list of instruments that produce error when attempting to create them
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

        reopen_plot_window = QAction("Reopen plot", self)
        reopen_plot_window.triggered.connect(self.reopen_plot_windows)

        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(exit_action)
        file_menu.addMenu(start_new_measurement_menu)

        tools_menu = self.menuBar().addMenu("&Tools")
        tools_menu.addAction(reopen_plot_window)

    """""""""""""""""""""
    Data manipulation
    """""""""""""""""""""
    def update_station_preview(self):
        """
        When new instrument is added, add a line to instrument_table widget containing some data (name and type) about
        the instrument, as well as button to edit the instrument.

        :return: NoneType
        """
        # Go ahead and iterate through all instruments that have been created so far and if any of those instruments
        # hasn't been added to the table , add it to the table
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
                current_instrument_btn.clicked.connect(self.make_open_instrument_edit(instrument))
                self.instruments_table.setCellWidget(rows, 2, current_instrument_btn)
                self.edit_button_dict[instrument] = current_instrument_btn
                self.station_instruments[instrument] = self.instruments[instrument]

                # Also bind a shortcut for opening that instrument coresponding to the number of the row that the
                # instrument is displayed in (Example: instrument in row 1 will have shortcut F1, row 2 -> F2, ....)
                key = "Key_F" + str(rows+1)
                key_class = getattr(Qt, key)

                add_shortcut = QShortcut(QtGui.QKeySequence(key_class), self)
                add_shortcut.activated.connect(self.make_open_instrument_edit(instrument))

    def update_loops_preview(self, edit=False):
        """
        This function is called from child class (SetupLoopsWidget) each time a new loop is created.
        Adds a loop to a loops_table widget which contains all loops as well as buttons to "Edit", "Run" and "Delete"
        a loop.

        Edit:
            opens "SetupLoopsWidget" with data from specified loop
        Run:
            runs the loop with current data (with plot)
        Delete:
            removes a loop from the table and from the self.loops dictionary, and also deletes action from self.actions
            that coresponds to this loop.

        :return: NoneType
        """
        # Iterate through all loops that have been created and added to self.loops dictionary, if any of those has not
        # been added to loops table (and shown loops dict) then add it to both so that it is visible in the window
        for name, loop in self.loops.items():
            if name not in self.shown_loops:
                rows = self.loops_table.rowCount()
                self.loops_table.insertRow(rows)

                # Model a string that will display loop values in the table.
                # Format: loop_name[lower_limit, upper_limit, num_of_steps, delay].action_parameter
                lower = str(loop.sweep_values[0])
                upper = str(loop.sweep_values[-1])
                steps = str(len(loop.sweep_values))
                delay = str(loop.delay)
                display_string = "{} [{}, {}, {}, {}].{}".format(name, lower, upper, steps, delay, str(loop.actions[0]))
                item = QTableWidgetItem(display_string)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.loops_table.setItem(rows, 0, item)
                current_loop_btn = QPushButton("Edit")
                current_loop_btn.resize(35, 20)
                current_loop_btn.clicked.connect(lambda checked, loop_name=name: self.setup_loops(loop_name))
                self.loops_table.setCellWidget(rows, 1, current_loop_btn)

                # Button within a table that runs a loop that is in the same table row as the button
                run_current_loop_btn = QPushButton("Run")
                run_current_loop_btn.resize(35, 20)
                run_current_loop_btn.clicked.connect(lambda checked, loop_name=name: self.run_specific_loop(loop_name))
                self.loops_table.setCellWidget(rows, 2, run_current_loop_btn)

                # Button within the table that removes a loop that is in the same row as the button
                delete_current_loop = QPushButton("Delete")
                delete_current_loop.resize(35, 20)
                delete_current_loop.clicked.connect(self.make_delete_loop(name, item))
                self.loops_table.setCellWidget(rows, 3, delete_current_loop)

                self.shown_loops.append(name)
                self.select_loop_cb.addItem(name, loop)

                # Create a shortcut for opening each loop. Loop in row1 opens with key combo: CTRL + F1, row2: CTRL+F2
                key_combo_string = "Ctrl+F"+str(rows+1)
                add_shortcut = QShortcut(QtGui.QKeySequence(key_combo_string), self)
                add_shortcut.activated.connect(lambda loop_name=name: self.setup_loops(loop_name))

            elif edit == name:
                for i in range(self.loops_table.rowCount()):
                    item = self.loops_table.item(i, 0)
                    if item.text()[:len(name)+1] == name + " ":
                        rows = i
                        break

                # if a loop is being edited, just update the values of the edited loop
                lower = str(loop.sweep_values[0])
                upper = str(loop.sweep_values[-1])
                steps = str(len(loop.sweep_values))
                delay = str(loop.delay)
                display_string = "{} [{}, {}, {}, {}].{}".format(name, lower, upper, steps, delay, str(loop.actions[0]))
                item = QTableWidgetItem(display_string)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.loops_table.setItem(rows, 0, item)
                self.loops_table.removeCellWidget(rows, 3)
                delete_current_loop = QPushButton("Delete")
                delete_current_loop.resize(35, 20)
                delete_current_loop.clicked.connect(self.make_delete_loop(name, item))
                self.loops_table.setCellWidget(rows, 3, delete_current_loop)

    def run_qcodes(self, with_plot=False):
        """
        Runs qcodes with specified instruments and parameters. Checks for errors in data prior to runing qcodes
        Adds all instruments to qc.Station and runs the last created loop (i think this is not good, but hey theres a
        button for each loop to run that specific loop)

        Loop is ran in a separate thread so that it does not block GUI thread (and the program)

        :param with_plot: if set to true, runs (and saves) live plot while measurement is running
        :return: NoneType
        """
        self.stop_loop_requested = False
        self.loop_started.emit()
        self.line_trace_count = 0

        # first create a station and add all instruments to it, to have the data available in the output files
        station = qc.Station()
        for name, instrument in self.instruments.items():
            station.add_component(instrument, name)

        # grab the last action added to the actions list. Set its data_set to None in case that loop has already been
        # ran. Create a new data set with the name and location provided by user input
        if len(self.actions):
            loop = self.actions[-1]
            loop.data_set = None

            # adjust save location of the file
            if self.save_location != "":
                loc_provider = qc.data.location.FormatLocation(
                    fmt=self.save_location + '/{date}/#{counter}_{name}_{time}')
                qc.data.data_set.DataSet.location_provider = loc_provider
            data = loop.get_data_set(name=self.output_file_name.text())

            # Check if the function was called with plot in background, if it was, create a new plot, delete backgroud
            # action of the loop (if a loop has been ran before with a background action [loop cannot have more then
            # 1 background action]), attach a new background action and run a loop by calling a worker to run it in a
            # separate thread
            if with_plot:
                # if you are running loop in a loop then create one more graph that will display 10 most recent line
                # traces
                if isinstance(loop.actions[0], ActiveLoop):
                    line_traces_plot = qc.QtPlot(fig_x_position=0.05, fig_y_position=0.4, window_title="Line traces")
                    self.live_plots.append(line_traces_plot)
                    loop.actions.append(Task(lambda: self.update_line_traces(line_traces_plot, data, parameter_name)))
                    loop.actions[0].progress_interval = None
                else:
                    if loop.progress_interval is None:
                        loop.progress_interval = 20
                parameter = get_plot_parameter(loop)
                plot = qc.QtPlot(fig_x_position=0.05, fig_y_position=0.4, window_title=self.output_file_name.text())
                self.live_plots.append(plot)
                parameter_name = str(parameter)
                plot.add(getattr(data, parameter_name))
                # loop.with_bg_task(plot.update, plot.save).run(use_threads=True)
                loop.bg_task = None
                worker = Worker(loop.with_bg_task(plot.update, plot.save).run, False)
            else:
                # loop.run(use_threads=True) -> this has something to do with multiple gets at the same time
                #                               i guess it would get them all at the same time instead of one by one

                # otherwise if plot was not requested, just run a loop (also in separate thread)
                worker = Worker(loop.run, False)
            self.workers.append(worker)

            # connect the signals of a worker
            worker.signals.result.connect(print_output)
            worker.signals.finished.connect(self.cleanup)
            worker.signals.progress.connect(progress_func)

            # start the worker
            del self.workers[:]
            # starting live mode of all opened instruments
            # commented cause it causes collision in the instrument when two different sources send commands to the
            # instrument. Sometimes this causes crashing of the loop.
            """for widget in self.active_isntruments:
                # only if that instrument has this parameter, then start its live mode
                if self.actions[-1].sweep_values.name in widget.textboxes.keys():
                    widget.toggle_live()"""
            self.disable_run_buttons()
            self.thread_pool.start(worker)

        # Just in case someone presses run with no loops created
        else:
            show_error_message("Oops !", "Looks like there is no loop to be ran !")

    def run_with_plot(self):
        """
        Call self.run_qcodes() with parameter with_plot set to True

        :return: NoneType
        """
        self.run_qcodes(with_plot=True)

    @pyqtSlot()
    def select_save_location(self):
        """
        Opens a QFileDialog for selecting a location on local machine, path to the selected location is set as a save
        location for results of the measurment

        :return: NoneType
        """
        self.save_location = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

    """""""""""""""""""""
    Helper functions
    """""""""""""""""""""
    @pyqtSlot()
    def exit(self):
        """
        Close the main window
        :return: NoneType
        """
        # Close all the instruments not to leave any hanging tails
        for name, instrument in self.instruments.items():
            print("Closing", instrument)
            instrument.close()
        # Close all other windows that are currently opened
        app = QtGui.QGuiApplication.instance()
        app.closeAllWindows()
        self.close()

    def closeEvent(self, a0: QtGui.QCloseEvent):
        self.exit()

    @pyqtSlot()
    def add_new_instrument(self, name):
        """
        Opens a new Widget (window) with text inputs for parameters of an instrument, creates new instrument(s)
        :return: NoneType
        """
        # AddInstrumentWidget need access to self.instruments dictionary in order to be able to add any newly created
        # instruments to it
        self.add_instrument = Widget(self.instruments, parent=self, default=name)
        self.add_instrument.submitted.connect(self.update_station_preview)
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
        self.setup_loops_widget = LoopsWidget(self.instruments, self.dividers, self.loops, self.actions, parent=self,
                                              loop_name=loop_name)
        self.setup_loops_widget.show()

    @pyqtSlot()
    def open_text_editor(self):
        """
        Open a simple text editor as a new widget (possible custom tool creation)

        :return: NoneType
        """
        msg = random[randint(1, len(random))]
        show_error_message("Do you need some motivation ?", msg)

    @pyqtSlot()
    def open_attach_divider(self):
        """
        Opens a new widget for setting up  dividers. Can attach a divider to any parameter of any instrument
        People are gonna add dividers to parameters that cannot have divider (like IDN) im sure of this.
        God help them.

        :return: NoneType
        """
        self.attach_divider_widget = DividerWidget(self.instruments, self.dividers, parent=self)
        self.attach_divider_widget.show()

    def stop_all_workers(self):
        """
        Reworked: Stops all instruments that are currently being live updated and returns them to static mode

        :return:
        """
        print(self.workers)
        print("Emmiting the signal to all workers")
        for worker in self.instrument_workers:
            worker.stop_requested = True
        for widget in self.active_isntruments:
            if widget.live:
                widget.toggle_live()
        self.stop_loop_requested = True
        self.enable_run_buttons()

    # This is a function factory (wow, i'm so cool, i made a function factory)
    def make_open_instrument_edit(self, instrument):
        """
        Hi, i am a function factory, and for each button you see next to an instrument i create a new function to edit
        that particular instrument. After creating that function i return it so it can be called with a click on the
        button.

        :param instrument: refers to a name of the instrument to be edited
        :return: newly created function to open "EditInstrumentWidget" with this particular instrument
        """
        def open_instrument_edit():
            """
            Open a new widget and pass it an instrument that can be edited through the newly opened widget

            :return: NoneType
            """
            if hasattr(self.instruments[instrument], "timeout"):
                self.instruments[instrument].set("timeout", 50)
            # Parameters:
            # self. instruments: widget needs access to all instruments to be able to edit them and add new ones
            # self.dividers: widget needs access to dividers to be able to display them if they are attached
            # self.active_instruments: list of instrument edit windows that are opened, to be able to remove self
            # from that list when closing the window
            # self.thread_pool: To be able to run functions in a shared thread pool (get_all, set_all)
            # parent: reference to this widget
            # instrument_name: name of the instrument that is being edited, to be able to fetch it from instruments
            # dictionary that is also being passed to this widget
            self.edit_instrument = EditInstrumentWidget(self.instruments, self.dividers, self.active_isntruments,
                                                        self.thread_pool, parent=self, instrument_name=instrument)
            # Add newly created window to a list of active windows
            self.active_isntruments.append(self.edit_instrument)
            self.edit_instrument.show()
        return open_instrument_edit

    def run_specific_loop(self, loop_name):
        """
        Place the action that coresponds to this loop to the last place in the actions queue so that its the one that
        gets ran by the run button, and then run it ... d'oh

        :param loop_name: name of the loop that is supposed to be ran
        :return: NoneType
        """

        # since name of the loop is a parameter of this function, get the loop from loops, find it in the actions list
        # put it in the last place of that list (remember, the last one is the one that get run), and then run it
        loop = self.loops[loop_name]
        loop_index = self.actions.index(loop)
        self.actions[loop_index], self.actions[-1] = self.actions[-1], self.actions[loop_index]
        self.run_with_plot()

    def make_delete_loop(self, loop_name, item):
        """
        Function factory, creates functions that delete each individual loop from tableWidget for loops

        :param loop_name: name of the loop (to be able to remove it from loops dictionary)
        :param item: use this item to find which row of the tabelWidget to delete
        :return: pointer to the newly created function
        """
        def delete_loop():
            """
            Remove a loop from loops_table widget
            :return: NoneType
            """
            self.loops_table.removeRow(self.loops_table.row(item))
            if loop_name in self.loops:
                if self.loops[loop_name] in self.actions:
                    self.actions.remove(self.loops[loop_name])
                del self.loops[loop_name]

        return delete_loop

    def check_stop_request(self):
        """
        This function is passed to a qcodes Task() to be checked on every measure point of the loop. Function checks if
        the class member stop_loop_requested is set to true, and if it is it raises an exception that stops the qcodes
        loop.

        :return:
        """
        if self.stop_loop_requested is True:
            self.enable_run_buttons()
            raise _QcodesBreak

    def disable_run_buttons(self):
        """
        This function is used to disable running other loops when one of the loops has started. Multiple loops running
        at the same time might try to send commands to the same instrument and cause an error.

        :return: NoneType
        """
        self.btn_run.setDisabled(True)

        for row_index in range(self.loops_table.rowCount()):
            run_button = self.loops_table.cellWidget(row_index, 2)
            run_button.setDisabled(True)
            delete_button = self.loops_table.cellWidget(row_index, 3)
            delete_button.setDisabled(True)
            edit_button = self.loops_table.cellWidget(row_index, 1)
            edit_button.setDisabled(True)

    def enable_run_buttons(self):
        """
        After a loop has finished enable running other loops.

        :return: NoneType
        """
        self.btn_run.setDisabled(False)
        for row_index in range(self.loops_table.rowCount()):
            run_button = self.loops_table.cellWidget(row_index, 2)
            run_button.setDisabled(False)
            delete_button = self.loops_table.cellWidget(row_index, 3)
            delete_button.setDisabled(False)
            edit_button = self.loops_table.cellWidget(row_index, 1)
            edit_button.setDisabled(False)

    def cleanup(self):
        """
        This function is called when a thread is finished to stop the workers and re enable run buttons.
        :return:
        """
        self.stop_all_workers()
        self.enable_run_buttons()
        self.loop_finished.emit()
        self.line_trace_count = 0
        self.live_plots = []

    def run_with_livedata(self):
        """
        ################################################################################################################
        LEGACY METHOD. Was used when i had no idea that each parameter hold the data of its last value so i dont need to
        get it everytime from the physical instrument, i can just get it from tha parameter object.
        ################################################################################################################

        This function appends a task to a loop. Task updates value of instruments parameter every iteration of the loop.
        After appending the task the loop gets started with plot option turned on.

        :return: NoneType
        """
        loop_name = self.select_loop_cb.currentText()
        loop = self.loops[loop_name]
        tsk = Task(self.update_opened_instruments)
        loop.actions.append(tsk)
        loop_index = self.actions.index(loop)
        self.actions[loop_index], self.actions[-1] = self.actions[-1], self.actions[loop_index]
        self.run_with_plot()

    def update_opened_instruments(self):
        """
        ################################################################################################################
        LEGACY METHOD. Was used when i had no idea that each parameter hold the data of its last value so i dont need to
        get it everytime from the physical instrument, i can just get it from tha parameter object.
        ################################################################################################################
        Function that updates the value of a parameter that is being swept if the EditWindow of that window is opened.

        :return: NoneType
        """
        for widget in self.active_isntruments:
            # only if that instrument has this parameter, then start its live mode
            name = self.actions[-1].sweep_values.name
            if name in widget.textboxes.keys():
                widget.update_parameters_data(name=name)

    def update_line_traces(self, plot, dataset, parameter_name):
        """
        Add 10 line traces to a graph, and then clear the graph and add 10 new line traces.

        :param plot: Instance of a graph that we want to add a line trace eto
        :param dataset: Dataset from which we extract the data
        :param parameter_name: Name of the parameter that is being plotted
        :return: NoneType
        """
        if self.line_trace_count % 10 == 0:
            plot.clear()
        plot.add(getattr(dataset, parameter_name)[self.line_trace_count])
        self.line_trace_count += 1

    def resize_for_loop(self, decrease=False):
        """
        Legacy method, not used anymore since switching to layouts

        Method that resizes the window when a loop is added/removed from it.

        :param decrease: If loop is being removed decreas will be set to True and window size will be decreased
        :return: NoneType
        """

        if decrease == False:
            if self.loops_table.rowCount() > 2:
                self.loops_table.resize(self.loops_table.width(), self.loops_table.height() + 30)
                self.resize(self.width(), self.height() + 30)
        else:
            if self.loops_table.rowCount() > 1:
                self.loops_table.resize(self.loops_table.width(), self.loops_table.height() - 30)
                self.resize(self.width(), self.height() - 30)

    def reopen_plot_windows(self):
        for plot in self.live_plots:
            plot.win.show()
            print(plot)



def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
