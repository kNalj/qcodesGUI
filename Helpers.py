from PyQt5.QtWidgets import QMessageBox
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