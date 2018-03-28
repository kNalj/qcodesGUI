from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QLabel
import sys

from Helpers import *

class LoopsWidget(QWidget):

    def __init__(self, instruments, parent=None):
        """
        Constructor for AddInstrumentWidget window

        :param instruments: Dictionary shared with parent (MainWindow) to be able to add instruments to instruments
        dictionary in the MainWindow
        :param parent: specify object that created this widget
        """
        super(LoopsWidget, self).__init__()
        self.instruments = instruments
        self.parent = parent
        self.init_ui()
        self.show()

    def init_ui(self):
        self.setGeometry(256, 256, 360, 400)
        self.setWindowTitle("Setup loops")
        self.setWindowIcon(QtGui.QIcon("osciloscope_icon.png"))

        labels = ["Lower limit", "Upper limit", "Num", "Step"]
        first_location = [40, 80]

        label = QLabel("Parameters", self)
        label.move(25, 25)

        for i in range(len(labels)):
            label = QLabel(labels[i], self)
            label.move(first_location[0] + i * 75, first_location[1] - 20)

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LoopsWidget([])
    sys.exit(app.exec_())
