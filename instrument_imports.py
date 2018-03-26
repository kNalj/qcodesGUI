"""from qcodes.instrument_drivers.Advantech.PCIE_1751 import *
from qcodes.instrument_drivers.agilent import *
from qcodes.instrument_drivers.AlazarTech import *
from qcodes.instrument_drivers.american_magnetics import *
from qcodes.instrument_drivers.Harvard import *
from qcodes.instrument_drivers.HP import *
from qcodes.instrument_drivers.ithaco import *
from qcodes.instrument_drivers.Keysight import *
from qcodes.instrument_drivers.Lakeshore import *
from qcodes.instrument_drivers.Minicircuits import *
from qcodes.instrument_drivers.oxford import *
from qcodes.instrument_drivers.QDev import *
from qcodes.instrument_drivers.QuTech import *
from qcodes.instrument_drivers.rigol import *
from qcodes.instrument_drivers.rohde_schwarz import *
from qcodes.instrument_drivers.signal_hound import *
from qcodes.instrument_drivers.Spectrum import *
from qcodes.instrument_drivers.stanford_research import *
from qcodes.instrument_drivers.tektronix import *
from qcodes.instrument_drivers.weinschel import *
from qcodes.instrument_drivers.yokogawa import *
from qcodes.instrument_drivers.ZI import *"""

from qcodes.instrument.base import Instrument

import os
import inspect
import importlib
import qcodes as qc

def get_subfolders(path, instrument_brands_only=False):
    """
    Helper function to find all folders within folder specified by "path"

    :param path: path to folder to scrap subfolders from
    :return: list[] of subfolders from specified path
    """
    if instrument_brands_only:
        return [f.name for f in os.scandir(path) if f.is_dir() and f.name[0] != "_"]
    return [f.name for f in os.scandir(path) if f.is_dir() and f.name[0]]
# ones that throw errors correct and add to this dict then use the value stored in dict, for others just go with default
correct_names = {"PCIE_1751": "Advantech_PCIE_1751", "E8267C": "E8267"}

def get_files_in_folder(path, instrument_drivers_only=False):
    """
    Helper function to find all files within folder specified by path

    :param path: path to folder to scrap files from
    :param instrument_drivers_only: if True, apply set of rules that filter only instrument driver files
    :return: list[] of files from specified path
    """
    if instrument_drivers_only:
        return[f.name for f in os.scandir(path) if f.is_file() and f.name[0].upper() == f.name[0] and f.name[0] != "_"]
    return[f.name for f in os.scandir(path) if f.is_file()]

path = os.path.dirname(inspect.getfile(qc)) + "\\instrument_drivers"
brands = get_subfolders(path, True)
for brand in brands:
    models = get_files_in_folder(path + "\\" + brand, True)
    for model in models:
        if model[0:-3] not in ["M3201A", "M3300A", "M4i", "ZIUHFLI", "Keithley_2600_channels", "AWGFileParser"]:
            module_name = "qcodes.instrument_drivers." + brand + "." + model[:-3]
            module = importlib.import_module(module_name)
            my_class = 0
            if model not in correct_names.keys():
                print("Not in CN")
                try:
                    my_class = getattr(module, model[:-3])
                except Exception as e:
                    print(str(e))
                finally:
                    print(my_class)
            else:
                print("In CN")
                try:
                    my_class = getattr(module, correct_names[model])
                except Exception as e:
                    print(str(e))
                finally:
                    print(my_class)