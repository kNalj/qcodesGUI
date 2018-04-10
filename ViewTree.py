from PyQt5.QtWidgets import  QApplication, QTreeWidget, QTreeWidgetItem, QShortcut
from PyQt5 import QtGui
from PyQt5.QtCore import Qt


class ViewTree(QTreeWidget):
    def __init__(self, value):
        super().__init__()
        self.setWindowTitle("Loop details")
        self.setWindowIcon(QtGui.QIcon("img/osciloscope_icon.png"))

        close_shortcut = QShortcut(QtGui.QKeySequence(Qt.Key_Escape), self)
        close_shortcut.activated.connect(self.close)

        def fill_item(item, value):
            def new_item(parent, text, val=None):
                child = QTreeWidgetItem([text])
                fill_item(child, val)
                parent.addChild(child)
                child.setExpanded(True)
            if value is None: return
            elif isinstance(value, dict):
                for key, val in sorted(value.items()):
                    new_item(item, str(key), val)
            elif isinstance(value, (list, tuple)):
                for val in value:
                    text = (str(val) if not isinstance(val, (dict, list, tuple))
                            else '[%s]' % type(val).__name__)
                    new_item(item, text, val)
            else:
                new_item(item, str(value))

        fill_item(self.invisibleRootItem(), value)


if __name__ == '__main__':
    app = QApplication([])
    window = ViewTree({'key1': 'value1', 'key3': [1, 2, 3, {1: 3, 7: 9}]})
    window.show()
    app.exec_()
