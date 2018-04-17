from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QLabel, QComboBox, QDesktopWidget, QShortcut
from PyQt5.QtCore import Qt

import sys
import importlib

from Helpers import *
import qcodes as qc
from qcodes.instrument_drivers.devices import VoltageDivider
""""
That inner delay thing is probably hidden somewhere in file: qcodes/instrument/parameter.py between lines 474 and 596
"""


class LoopsWidget(QWidget):

    def __init__(self, instruments, loops, actions, parent=None, loop_name=""):
        """
        Constructor for AddInstrumentWidget window

        :param instruments: Dictionary shared with parent (MainWindow) to be able to add instruments to instruments
        dictionary in the MainWindow
        :param loops: shared with main window, dict of all created loops
        :param actions: list of loops that can be ran in order of creation
        :param parent: specify object that created this widget
        :param loop_name: If passed, opens the window with data field filed by that particular loops data
        """
        super(LoopsWidget, self).__init__()

        self.instruments = instruments
        self.loops = loops
        self.actions = actions
        self.parent = parent
        self.name = loop_name
        if self.name != "":
            self.loop = self.loops[self.name]
        self.init_ui()
        self.show()

    """""""""""""""""""""
    User interface
    """""""""""""""""""""
    def init_ui(self):
        """
        Initializes user interface for LoopsWidget class

        :return: NoneType
        """
        # set starting position of window relative to the size of the screen
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        self.setGeometry(int(0.05*width) + 620, int(0.05*height), 360, 340)
        self.setMinimumSize(360, 340)
        self.setWindowTitle("Setup loops")
        self.setWindowIcon(QtGui.QIcon("img/osciloscope_icon.png"))

        # label above input fields and tooltips to be shown on mouseover
        labels = ["Lower limit", "Upper limit", "Steps", "Delay"]
        tooltips = ["Start from this value",
                    "Sweep to this value",
                    "Number of steps to be measured from lower limit to upper limit",
                    "Wait this many seconds between each step"]
        first_location = [40, 80]

        label = QLabel("Parameters", self)
        label.move(25, 25)

        for i in range(len(labels)):
            label = QLabel(labels[i], self)
            label.move(first_location[0] + i * 75, first_location[1] - 20)
            label.setToolTip(tooltips[i])

        self.textbox_lower_limit = QLineEdit(self)
        self.textbox_lower_limit.move(first_location[0], first_location[1])
        self.textbox_lower_limit.resize(45, 20)
        self.textbox_upper_limit = QLineEdit(self)
        self.textbox_upper_limit.move(115, 80)
        self.textbox_upper_limit.resize(45, 20)
        # number of steps
        self.textbox_num = QLineEdit(self)
        self.textbox_num.setText("1")
        self.textbox_num.move(190, 80)
        self.textbox_num.resize(45, 20)
        # this is actualy a delay (NOT STEPS !)
        self.textbox_step = QLineEdit(self)
        self.textbox_step.setText("0")
        self.textbox_step.move(265, 80)
        self.textbox_step.resize(45, 20)
        # comboboxes for selecting sweep parameter instrument. First you select the instrument that you want to sweep
        # After selecting instrument the other combobox is populated by parameters of that instrument
        label = QLabel("Sweep parameter:", self)
        label.move(25, 120)
        self.sweep_parameter_instrument_cb = QComboBox(self)
        self.sweep_parameter_instrument_cb.resize(80, 30)
        self.sweep_parameter_instrument_cb.move(45, 140)
        self.sweep_parameter_instrument_cb.setToolTip("Please select instrument to sweep from")
        for name, instrument in self.instruments.items():
            display_member = name
            value_member = instrument
            self.sweep_parameter_instrument_cb.addItem(display_member, value_member)
        self.sweep_parameter_instrument_cb.currentIndexChanged.connect(self.update_sweep_instrument_parameters)
        # combobox for selecting parameter
        self.sweep_parameter_cb = QComboBox(self)
        self.sweep_parameter_cb.resize(80, 30)
        self.sweep_parameter_cb.move(135, 140)
        self.sweep_parameter_cb.setToolTip("Please select parameter to sweep")
        self.update_sweep_instrument_parameters()
        # Add divider to sweep parameter
        label = QLabel("Divider", self)
        label.move(240, 120)
        label.setToolTip("Add division/amplification to the instrument being swept")
        self.sweep_parameter_divider = QLineEdit("1", self)
        self.sweep_parameter_divider.move(240, 140)
        self.sweep_parameter_divider.resize(30, 30)

        label = QLabel("Loop action parameter:", self)
        label.move(25, 200)
        # same logic as sweep parameter (see line 88)
        self.action_parameter_instrument_cb = QComboBox(self)
        self.action_parameter_instrument_cb.resize(80, 30)
        self.action_parameter_instrument_cb.move(45, 220)
        for name, instrument in self.instruments.items():
            display_member = name
            value_member = instrument
            self.action_parameter_instrument_cb.addItem(display_member, value_member)
        self.action_parameter_instrument_cb.currentIndexChanged.connect(self.update_action_instrument_parameters)
        # combobox for selecting parameter
        self.action_parameter_cb = QComboBox(self)
        self.action_parameter_cb.resize(80, 30)
        self.action_parameter_cb.move(135, 220)
        self.update_action_instrument_parameters()
        # add loops to combobox (loop can also be an action of another loop)
        for name, loop in self.loops.items():
            display_member_string = "[" + name + "]"
            data_member = loop
            self.action_parameter_instrument_cb.addItem(display_member_string, data_member)
        # divider for action parameter
        label = QLabel("Divider", self)
        label.move(240, 200)
        label.setToolTip("Add division/amplification to the instrument")
        self.action_parameter_divider = QLineEdit("1", self)
        self.action_parameter_divider.move(240, 220)
        self.action_parameter_divider.resize(30, 30)
        # Creates a loop from user input data
        self.add_loop_btn = QPushButton("Create loop", self)
        self.add_loop_btn.move(45, 270)
        self.add_loop_btn.resize(260, 40)
        self.add_loop_btn.setToolTip("Create a loop with chosen parameters")
        self.add_loop_btn.clicked.connect(self.create_loop)

        # if the loop name has been passed to the widget, fill the fields with required data (obtained from the loop)
        if self.name != "":
            self.fill_loop_data()
        # shortcuts for certain actions
        close_shortcut = QShortcut(QtGui.QKeySequence(Qt.Key_Escape), self)
        close_shortcut.activated.connect(self.close)

    """""""""""""""""""""
    Data manipulation
    """""""""""""""""""""
    def create_loop(self):
        """
        Creates a new loop from data inputed by user. Adds newly created loop to "loops" dictionary in MainWindow.
        Creates action to be executed upon runing qcodes and adds it to "actions" list in MainWindow

        :return: NoneType
        """
        # Try to fetch user input data and cast it to floats
        # If it fails, throw an exception
        # Otherwise, create a loop, add it to the shared dict
        try:
            lower = float(self.textbox_lower_limit.text())
            upper = float(self.textbox_upper_limit.text())
            num = float(self.textbox_num.text())
            delay = float(self.textbox_step.text())
            sweep_division = float(self.sweep_parameter_divider.text())
            action_division = float(self.action_parameter_divider.text())
        except Exception as e:
            warning_string = "Errm, looks like something went wrong ! \nHINT: Measurement parameters not set. \n"\
                             + str(e)
            show_error_message("Warning", warning_string)
        else:
            if sweep_division != 1 and action_division != 1:
                sweep_divider = VoltageDivider(self.sweep_parameter_cb.currentData(), sweep_division)
                action_divider = VoltageDivider(self.action_parameter_cb.currentData(), action_division)
                lp = qc.Loop(sweep_divider.sweep(lower, upper, num=num), delay, progress_interval=20).each(
                    action_divider)
            elif sweep_division != 1:
                sweep_divider = VoltageDivider(self.sweep_parameter_cb.currentData(), sweep_division)
                print("A sweep divider was added")
                lp = qc.Loop(sweep_divider.sweep(lower, upper, num=num), delay, progress_interval=20).each(
                    self.action_parameter_cb.currentData())
            elif action_division != 1:
                action_divider = VoltageDivider(self.action_parameter_cb.currentData(), action_division)
                print("An action divider was added")
                lp = qc.Loop(self.sweep_parameter_cb.currentData().sweep(lower, upper, num=num), delay,
                             progress_interval=20).each(action_divider)
            else:
                lp = qc.Loop(self.sweep_parameter_cb.currentData().sweep(lower, upper, num=num), delay,
                             progress_interval=20).each(self.action_parameter_cb.currentData())

            name = "loop" + str(len(self.actions)+1)
            self.loops[name] = lp
            self.actions.append(lp)
            self.parent.update_loops_preview()
            # self.close()

    def update_sweep_instrument_parameters(self):
        """
        Replaces data in parameters combo box. Fetch all parameters of an instrument selected in a instrument combo box
        and display them as options in parameters combo box

        :return: NoneType
        """
        if len(self.instruments):
            self.sweep_parameter_cb.clear()
            instrument = self.sweep_parameter_instrument_cb.currentData()
            for parameter in instrument.parameters:
                if parameter != "IDN":
                    display_member_string = parameter
                    data_member = instrument.parameters[parameter]
                    self.sweep_parameter_cb.addItem(display_member_string, data_member)

    def update_action_instrument_parameters(self):
        """
        Replaces data in parameters combo box. Fetch all parameters of an instrument selected in a instrument combo box
        and display them as options in parameters combo box

        :return: NoneType
        """
        if len(self.instruments):
            self.action_parameter_cb.clear()
            action = self.action_parameter_instrument_cb.currentData()

            module_name = "qcodes.loops"
            module = importlib.import_module(module_name)
            loop_class = getattr(module, "ActiveLoop")

            if isinstance(action, loop_class):
                display_member_string = self.action_parameter_instrument_cb.currentText()
                data_member = self.action_parameter_instrument_cb.currentData()
                self.action_parameter_cb.addItem(display_member_string, data_member)
            else:
                for parameter in action.parameters:
                    if parameter != "IDN":
                        display_member_string = parameter
                        data_member = action.parameters[parameter]
                        self.action_parameter_cb.addItem(display_member_string, data_member)

    def fill_loop_data(self):
        """
        If this window is created with a loop passed to it then get all data from the loop and fill the fields in
        the window with that data. Enables editing previously created loops.

        :return: NoneType
        """
        self.textbox_lower_limit.setText(str(self.loop.sweep_values[0]))
        self.textbox_upper_limit.setText(str(self.loop.sweep_values[-1]))
        self.textbox_num.setText(str(len(self.loop.sweep_values)))
        self.textbox_step.setText(str(self.loop.delay))

        # if action is a loop, display it as a loop
        # else display selected instrument and parameter
        action = self.loop.actions[0]
        module_name = "qcodes.loops"
        module = importlib.import_module(module_name)
        loop_class = getattr(module, "ActiveLoop")
        if isinstance(action, loop_class):
            action_parameter_instrument_name = self.loop.actions[0]
            index = self.action_parameter_instrument_cb.findData(action_parameter_instrument_name)
            self.action_parameter_instrument_cb.setCurrentIndex(index)
        else:
            action_parameter_instrument_name = self.loop.actions[0]._instrument.name
            index = self.action_parameter_instrument_cb.findText(action_parameter_instrument_name)
            self.action_parameter_instrument_cb.setCurrentIndex(index)
            action_parameter_name = self.loop.actions[0].name
            index = self.action_parameter_cb.findText(action_parameter_name)
            self.action_parameter_cb.setCurrentIndex(index)

        # do the same thing for sweep parameter
        sweep_parameter_instrument_name = self.loop.sweep_values.parameter._instrument.name
        index = self.sweep_parameter_instrument_cb.findText(sweep_parameter_instrument_name)
        self.sweep_parameter_instrument_cb.setCurrentIndex(index)
        sweep_parameter_name = self.loop.sweep_values.parameter.name
        index = self.sweep_parameter_cb.findText(sweep_parameter_name)
        self.sweep_parameter_cb.setCurrentIndex(index)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LoopsWidget([])
    sys.exit(app.exec_())
