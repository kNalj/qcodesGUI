from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QLabel, QComboBox, QDesktopWidget, QShortcut, \
    QGridLayout, QVBoxLayout, QHBoxLayout, QSizePolicy, QFrame
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThreadPool
from PyQt5.QtCore import Qt

import sys
from Helpers import *

from qcodes.actions import Task
from qcodes.loops import ActiveLoop
from qcodes.instrument.base import Instrument
from qcodes.instrument_drivers.devices import VoltageDivider

class MultiSweep(QWidget):

    submitted = pyqtSignal()

    def __init__(self, instruments, dividers, loops, actions, parent=None, loop_name=""):

        super(MultiSweep, self).__init__()

        self.instruments = instruments
        self.dividers = dividers
        self.loops = loops
        self.actions = actions
        self.parent = parent
        # self.parent.loop_started.connect(self.disable_changes)
        # self.parent.loop_finished.connect(self.enable_changes)
        self.name = loop_name

        self.sweep_params_data = {}
        self.action_params_data = {}

        if self.name != "":
            self.loop = self.loops[self.name]
        self.init_ui()
        self.show()

    """""""""""""""""""""
    User interface
    """""""""""""""""""""
    def init_ui(self):

        # set starting position of window relative to the size of the screen
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        self.width = 400
        self.height = 340
        self.setGeometry(int(0.05 * width) + 620, int(0.05 * height), self.width, self.height)
        self.setMinimumSize(400, 340)

        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)

        steps_label = QLabel("Steps")
        self.steps = QLineEdit()
        step_size_label = QLabel("Step size")
        self.step_size = QLineEdit()
        delay_label = QLabel("Delay")
        self.delay = QLineEdit()
        self.layout().addWidget(steps_label, 0, 0, 1, 1)
        self.layout().addWidget(self.steps, 1, 0, 1, 3)
        self.layout().addWidget(step_size_label, 0, 3, 1, 1)
        self.layout().addWidget(self.step_size, 1, 3, 1, 3)
        self.layout().addWidget(delay_label, 0, 6, 1, 1)
        self.layout().addWidget(self.delay, 1, 6, 1, 3)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.layout().addWidget(line, 2, 0, 1, 9)

        self.sweep_label = QLabel("Sweep parameters: ")
        self.layout().addWidget(self.sweep_label, 3, 0, 1, 9)

        self.v_layout_sweep_parameters = QVBoxLayout()
        main_sweep_parameter_grid_layout = QGridLayout()
        self.v_layout_sweep_parameters.addLayout(main_sweep_parameter_grid_layout)
        self.layout().addLayout(self.v_layout_sweep_parameters, 4, 0, 1, 9)

        self.add_sweep_parameter_btn = QPushButton("Add")
        self.add_sweep_parameter_btn.clicked.connect(lambda: self.add_sweep_param())
        self.add_sweep_parameter_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        main_sweep_parameter_grid_layout.addWidget(self.add_sweep_parameter_btn, 0, 0, 2, 1)
        self.swap_btn = QPushButton("↕")
        self.swap_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        main_sweep_parameter_grid_layout.addWidget(self.swap_btn, 0, 1, 2, 1)
        start_label = QLabel("Start")
        main_sweep_parameter_grid_layout.addWidget(start_label, 0, 2, 1, 1)
        self.start_line_edit = QLineEdit("")
        main_sweep_parameter_grid_layout.addWidget(self.start_line_edit, 0, 3, 1, 2)
        end_label = QLabel("End")
        main_sweep_parameter_grid_layout.addWidget(end_label, 1, 2, 1, 1)
        self.end_line_edit = QLineEdit("")
        main_sweep_parameter_grid_layout.addWidget(self.end_line_edit, 1, 3, 1, 2)
        instrument_cb_label = QLabel("Instr")
        main_sweep_parameter_grid_layout.addWidget(instrument_cb_label, 0, 5, 1, 1)
        self.sweep_instrument_combobox = QComboBox()
        main_sweep_parameter_grid_layout.addWidget(self.sweep_instrument_combobox, 0, 6, 1, 2)
        self.sweep_instrument_combobox.currentIndexChanged.connect(lambda: self.update_parameters(
            self.sweep_instrument_combobox, self.sweep_parameter_combobox))
        param_cb_label = QLabel("Param")
        main_sweep_parameter_grid_layout.addWidget(param_cb_label, 1, 5, 1, 1)
        self.sweep_parameter_combobox = QComboBox()
        main_sweep_parameter_grid_layout.addWidget(self.sweep_parameter_combobox, 1, 6, 1, 2)
        self.sweep_division = QLineEdit("")
        self.sweep_division.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        main_sweep_parameter_grid_layout.addWidget(self.sweep_division, 0, 8, 2, 1)
        self.sweep_parameter_combobox.currentIndexChanged.connect(lambda: self.update_division(
            self.sweep_parameter_combobox, self.sweep_division))

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.layout().addWidget(line, 5, 0, 1, 9)

        self.actions_params_label = QLabel("Action parameters: ")
        self.layout().addWidget(self.actions_params_label, 6, 0, 1, 9)

        self.v_layout_action_parameters = QVBoxLayout()
        main_action_parameter_grid_layout = QGridLayout()
        self.v_layout_action_parameters.addLayout(main_action_parameter_grid_layout)
        self.layout().addLayout(self.v_layout_action_parameters, 7, 0, 1, 9)

        self.add_action_param_btn = QPushButton("Add")
        self.add_action_param_btn.clicked.connect(self.add_action_param)
        main_action_parameter_grid_layout.addWidget(self.add_action_param_btn, 1, 0, 1, 1)
        instrument_label = QLabel("Instrument")
        main_action_parameter_grid_layout.addWidget(instrument_label, 0, 1, 1, 3)
        self.action_instrument_combobox = QComboBox()
        main_action_parameter_grid_layout.addWidget(self.action_instrument_combobox, 1, 1, 1, 3)
        self.action_instrument_combobox.currentIndexChanged.connect(lambda: self.update_parameters(
            self.action_instrument_combobox, self.action_parameter_combobox))
        parameter_label = QLabel("Parameter")
        main_action_parameter_grid_layout.addWidget(parameter_label, 0, 4, 1, 3)
        self.action_parameter_combobox = QComboBox()
        main_action_parameter_grid_layout.addWidget(self.action_parameter_combobox, 1, 4, 1, 3)
        division_label = QLabel("Division")
        main_action_parameter_grid_layout.addWidget(division_label, 0, 7, 1, 3)
        self.action_parameter_divider = QLineEdit("")
        main_action_parameter_grid_layout.addWidget(self.action_parameter_divider, 1, 7, 1, 3)
        self.action_parameter_combobox.currentIndexChanged.connect(lambda: self.update_division(
            self.action_parameter_combobox, self.action_parameter_divider))

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.layout().addWidget(line, 8, 0, 1, 9)

        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.create_loop)
        self.layout().addWidget(self.ok_btn, 9, 0, 1, 9)

        self.swap_btn.clicked.connect(lambda: self.swap_value(self.start_line_edit, self.end_line_edit))
        self.fill_data(self.sweep_instrument_combobox)
        self.fill_data(self.action_instrument_combobox)

    def add_sweep_param(self, data=None):

        self.height += 52
        self.resize(self.width, self.height)

        sweep_param_array = []
        index = str(len(self.sweep_params_data))
        sweep_param_name = "sweep_param_" + index

        new_param_grid_layout = QGridLayout()
        remove_sweep_parameter_btn = QPushButton("Remove")
        remove_sweep_parameter_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        new_param_grid_layout.addWidget(remove_sweep_parameter_btn, 0, 0, 2, 1)
        swap_btn = QPushButton("↕")
        swap_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        new_param_grid_layout.addWidget(swap_btn, 0, 1, 2, 1)
        start_label = QLabel("Start")
        new_param_grid_layout.addWidget(start_label, 0, 2, 1, 1)
        start_line_edit = QLineEdit("")
        sweep_param_array.append(start_line_edit)
        new_param_grid_layout.addWidget(start_line_edit, 0, 3, 1, 2)
        end_label = QLabel("End")
        new_param_grid_layout.addWidget(end_label, 1, 2, 1, 1)
        end_line_edit = QLineEdit("")
        sweep_param_array.append(end_line_edit)
        new_param_grid_layout.addWidget(end_line_edit, 1, 3, 1, 2)
        instrument_cb_label = QLabel("Instr")
        new_param_grid_layout.addWidget(instrument_cb_label, 0, 5, 1, 1)
        sweep_instrument_combobox = QComboBox()
        sweep_param_array.append(sweep_instrument_combobox)
        new_param_grid_layout.addWidget(sweep_instrument_combobox, 0, 6, 1, 2)
        param_cb_label = QLabel("Param")
        new_param_grid_layout.addWidget(param_cb_label, 1, 5, 1, 1)
        sweep_parameter_combobox = QComboBox()
        sweep_param_array.append(sweep_parameter_combobox)
        new_param_grid_layout.addWidget(sweep_parameter_combobox, 1, 6, 1, 2)
        sweep_division = QLineEdit("")
        sweep_division.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        new_param_grid_layout.addWidget(sweep_division, 0, 8, 2, 1)

        sweep_instrument_combobox.currentIndexChanged.connect(
            lambda: self.update_parameters(sweep_instrument_combobox, sweep_parameter_combobox))
        sweep_parameter_combobox.currentIndexChanged.connect(
            lambda: self.update_division(sweep_parameter_combobox, sweep_division))
        self.fill_data(sweep_instrument_combobox)

        if data is not None:
            instrument_index = sweep_instrument_combobox.findData(data["instrument_name"])
            sweep_instrument_combobox.setCurrentIndex(instrument_index)
            parameter_index = sweep_parameter_combobox.findData(data["parameter_name"])
            sweep_parameter_combobox.setCurrentIndex(parameter_index)

        remove_sweep_parameter_btn.clicked.connect(lambda: self.remove_elements([
            new_param_grid_layout,
            remove_sweep_parameter_btn,
            swap_btn,
            start_label,
            start_line_edit,
            end_label,
            end_line_edit,
            instrument_cb_label,
            sweep_instrument_combobox,
            param_cb_label,
            sweep_parameter_combobox,
            sweep_division
        ], height_change=-52))
        swap_btn.clicked.connect(lambda: self.swap_value(start_line_edit, end_line_edit))

        self.v_layout_sweep_parameters.addLayout(new_param_grid_layout)

    def add_action_param(self):

        self.height += 29
        self.resize(self.width, self.height)

        new_param_grid_layout = QGridLayout()
        new_param_delete_btn = QPushButton("Remove")
        new_param_instrument_combobox = QComboBox()
        new_param_parameter_combobox = QComboBox()
        new_param_division = QLineEdit("")

        new_param_grid_layout.addWidget(new_param_delete_btn, 0, 0, 1, 1)
        new_param_grid_layout.addWidget(new_param_instrument_combobox, 0, 1, 1, 3)
        new_param_grid_layout.addWidget(new_param_parameter_combobox, 0, 4, 1, 3)
        new_param_grid_layout.addWidget(new_param_division, 0, 7, 1, 3)

        new_param_instrument_combobox.currentIndexChanged.connect(
            lambda: self.update_parameters(new_param_instrument_combobox, new_param_parameter_combobox))
        new_param_parameter_combobox.currentIndexChanged.connect(
            lambda: self.update_division(new_param_parameter_combobox, new_param_division))

        self.fill_data(new_param_instrument_combobox)

        new_param_delete_btn.clicked.connect(lambda: self.remove_elements([
            new_param_delete_btn,
            new_param_division,
            new_param_parameter_combobox,
            new_param_instrument_combobox
        ], height_change=-29))

        self.v_layout_action_parameters.addLayout(new_param_grid_layout)

    def remove_elements(self, elements, height_change=0):

        for element in elements:
            element.deleteLater()

        self.height += height_change
        self.resize(self.width, self.height)

    def swap_value(self, first, second):

        second_text = first.text()
        first_text = second.text()
        first.setText(first_text)
        second.setText(second_text)

    """""""""""""""""""""
    Data manipulation
    """""""""""""""""""""
    def fill_data(self, combobox):
        """
        Fill combo boxes with existing instruments, loops, ...

        :return:
        """
        for name, instrument in self.instruments.items():
            display_member = name
            value_member = instrument
            combobox.addItem(display_member, value_member)

    def update_parameters(self, instr_combobox, param_combobox):
        instrument = instr_combobox.currentData()
        cb = param_combobox
        cb.clear()

        params = instrument.parameters
        for parameter in params:
            if parameter != "IDN" and str(instrument.parameters[parameter]) not in self.dividers:
                display_member_string = parameter
                data_member = instrument.parameters[parameter]
                cb.addItem(display_member_string, data_member)
            if str(instrument.parameters[parameter]) in self.dividers:
                name = str(instrument.parameters[parameter])
                display_member_string = self.dividers[name].name
                data_member = instrument.parameters[parameter]
                cb.addItem(display_member_string, data_member)

    def update_division(self, param_combobox, division_lineedit):
        param = param_combobox.currentData()
        line_edit = division_lineedit

        if param is not None:
            if param.full_name in self.dividers:
                division = self.dividers[param.full_name].division_value
            else:
                division = 1
            line_edit.setText(str(division))

    def create_loop(self):

        task = Task(self.parent.check_stop_request)

        self.submitted.emit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MultiSweep([], [], [], [])
    sys.exit(app.exec_())
