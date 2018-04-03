from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QLabel, QComboBox, QToolTip
import sys
import importlib

from Helpers import *
import qcodes as qc
from qcodes.instrument_drivers.devices import VoltageDivider


class LoopsWidget(QWidget):

    def __init__(self, instruments, loops, actions, parent=None):
        """
        Constructor for AddInstrumentWidget window

        :param instruments: Dictionary shared with parent (MainWindow) to be able to add instruments to instruments
        dictionary in the MainWindow
        :param parent: specify object that created this widget
        """
        super(LoopsWidget, self).__init__()

        self.instruments = instruments
        self.loops = loops
        self.actions = actions
        self.parent = parent
        self.init_ui()
        self.show()

    def init_ui(self):
        """
        Initializes user interface for LoopsWidget class

        :return:
        """
        self.setGeometry(256, 256, 360, 340)
        self.setMinimumSize(360, 340)
        self.setWindowTitle("Setup loops")
        self.setWindowIcon(QtGui.QIcon("osciloscope_icon.png"))

        labels = ["Lower limit", "Upper limit", "Steps", "Delay"]
        tooltips = ["Self explainatory",
                    "Self explainatory",
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

        self.textbox_num = QLineEdit(self)
        self.textbox_num.move(190, 80)
        self.textbox_num.resize(45, 20)

        self.textbox_step = QLineEdit(self)
        self.textbox_step.move(265, 80)
        self.textbox_step.resize(45, 20)

        label = QLabel("Sweep parameter:", self)
        label.move(25, 120)
        self.sweep_parameter_instrument_cb = QComboBox(self)
        self.sweep_parameter_instrument_cb.resize(80, 30)
        self.sweep_parameter_instrument_cb.move(45, 140)
        for name, instrument in self.instruments.items():
            display_member = name
            value_member = instrument
            self.sweep_parameter_instrument_cb.addItem(display_member, value_member)
            self.sweep_parameter_instrument_cb.currentIndexChanged.connect(self.update_sweep_instrument_parameters)

        self.sweep_parameter_cb = QComboBox(self)
        self.sweep_parameter_cb.resize(80, 30)
        self.sweep_parameter_cb.move(135, 140)
        for instrument in self.instruments:
            self.update_sweep_instrument_parameters()
            break

        label = QLabel("Divider", self)
        label.move(240, 120)
        self.sweep_parameter_divider = QLineEdit("1", self)
        self.sweep_parameter_divider.move(240, 140)
        self.sweep_parameter_divider.resize(30, 30)

        self.add_sweep_parameter_btn = QPushButton("Add", self)
        self.add_sweep_parameter_btn.resize(60, 30)
        self.add_sweep_parameter_btn.move(290, 140)
        self.add_sweep_parameter_btn.clicked.connect(self.add_sweep_parameter)

        label = QLabel("Loop action parameter:", self)
        label.move(25, 200)

        self.action_parameter_instrument_cb = QComboBox(self)
        self.action_parameter_instrument_cb.resize(80, 30)
        self.action_parameter_instrument_cb.move(45, 220)
        for name, instrument in self.instruments.items():
            display_member = name
            value_member = instrument
            self.action_parameter_instrument_cb.addItem(display_member, value_member)
            self.action_parameter_instrument_cb.currentIndexChanged.connect(self.update_action_instrument_parameters)

        self.action_parameter_cb = QComboBox(self)
        self.action_parameter_cb.resize(80, 30)
        self.action_parameter_cb.move(135, 220)
        for instrument in self.instruments:
            self.update_action_instrument_parameters()
            break
        for name, loop in self.loops.items():
            display_member_string = "[" + name + "]"
            data_member = loop
            self.action_parameter_instrument_cb.addItem(display_member_string, data_member)

        label = QLabel("Divider", self)
        label.move(240, 200)
        self.action_parameter_divider = QLineEdit("1", self)
        self.action_parameter_divider.move(240, 220)
        self.action_parameter_divider.resize(30, 30)

        self.add_action_parameter_btn = QPushButton("Add", self)
        self.add_action_parameter_btn.resize(60, 30)
        self.add_action_parameter_btn.move(290, 220)
        self.add_action_parameter_btn.clicked.connect(self.add_action_parameter)


        self.add_loop_btn = QPushButton("Create loop", self)
        self.add_loop_btn.move(45, 270)
        self.add_loop_btn.resize(260, 40)
        self.add_loop_btn.clicked.connect(self.create_loop)

    def create_loop(self):
        """
        Creates a new loop from data inputed by user. Adds newly created loop to "loops" dictionary in MainWindow.
        Creates action to be executed upon runing qcodes and adds it to "actions" list in MainWindow
        :return:
        """

        try:
            self.lower = float(self.textbox_lower_limit.text())
            self.upper = float(self.textbox_upper_limit.text())
            self.num = float(self.textbox_num.text())
            self.step = float(self.textbox_step.text())
            sweep_division = float(self.sweep_parameter_divider.text())
            action_division = float(self.action_parameter_divider.text())

            lp = qc.Loop(self.sweep_parameter_cb.currentData().sweep(self.lower, self.upper, num=self.num), self.step).each(self.action_parameter_cb.currentData())
        except Exception as e:
            warning_string = "Errm, looks like something went wrong ! \nHINT: Measurement parameters not set. \n"\
                             + str(e)
            show_error_message("Warning", warning_string)
        else:
            if sweep_division != 1:
                sweep_divider = VoltageDivider(self.sweep_parameter_cb.currentData(), sweep_division)
                print(sweep_divider)
                print("A sweep divider was added")
            if action_division != 1:
                action_divider = VoltageDivider(self.action_parameter_cb.currentData(), action_division)
                print(action_divider)
                print("An action divider was added")
            name = "loop" + str(len(self.actions)+1)
            self.loops[name] = lp
            self.actions.append(lp)
            self.parent.update_loops_preview()
            self.close()

    def add_sweep_parameter(self):
        pass

    def add_action_parameter(self):
        pass

    def update_sweep_instrument_parameters(self):
        self.sweep_parameter_cb.clear()
        instrument = self.sweep_parameter_instrument_cb.currentData()
        for parameter in instrument.parameters:
            if parameter != "IDN":
                display_member_string = parameter
                data_member = instrument.parameters[parameter]
                self.sweep_parameter_cb.addItem(display_member_string, data_member)

    def update_action_instrument_parameters(self):
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LoopsWidget([])
    sys.exit(app.exec_())
