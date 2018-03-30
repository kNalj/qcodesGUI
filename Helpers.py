from PyQt5.QtWidgets import QMessageBox, QTreeWidget, QTreeWidgetItem
from PyQt5 import QtGui

import os


def show_error_message(title, message):
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


def get_subfolders(path, instrument_brands_only=False):
    """
    Helper function to find all folders within folder specified by "path"

    :param path: path to folder to scrap subfolders from
    :param instrument_brands_only: if set to True, applies set of rules to filter isntrument brands
            when not set, this function can be used to get all subfolders in a specified folder
    :return: list[] of subfolders from specified path
    """
    if instrument_brands_only:
        return [f.name for f in os.scandir(path) if f.is_dir() and f.name[0] != "_"]
    return [f.name for f in os.scandir(path) if f.is_dir() and f.name[0]]


def get_files_in_folder(path, instrument_drivers_only=False):
    """
    Helper function to find all files within folder specified by path

    :param path: path to folder to scrap files from
    :param instrument_drivers_only: if True, apply set of rules that filter only instrument driver files
    :return: list[] of files from specified path
    """
    if instrument_drivers_only:
        return [f.name for f in os.scandir(path) if f.is_file() and f.name[0].upper() == f.name[0] and f.name[0] != "_"]
    return [f.name for f in os.scandir(path) if f.is_file()]


class ViewTree(QTreeWidget):
    """
    Widget that displays content of a dictionary (including sub dicts, lists, etc.)
    """
    def __init__(self, value):
        super().__init__()
        self.setWindowTitle("Loop details")
        self.setWindowIcon(QtGui.QIcon("osciloscope_icon.png"))

        def fill_item(item, value):
            def new_item(parent, text, val=None):
                child = QTreeWidgetItem([text])
                fill_item(child, val)
                parent.addChild(child)
                child.setExpanded(True)
            if value is None:
                return
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
