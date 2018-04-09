import qcodes as qc
import importlib
from PyQt5.QtWidgets import QTreeWidgetItem, QTreeWidget
import itertools
from instrument_imports import *
from Helpers import *
from qcodes.instrument.ip import IPInstrument
from qcodes.instrument.visa import VisaInstrument

from qcodes.instrument_drivers.QuTech.IVVI import IVVI

from qcodes.tests.instrument_mocks import DummyInstrument

# dummy = DummyInstrument("amen", gates=["g1", "g2"])
# dummy2 = DummyInstrument("haleluja", gates=["g1", "g2"])

#print(dummy.get("g1"))
#dummy.set("g1", 200.675365534576436)
#print(dummy.get("g1"))
#print(dummy.parameters.items())

#lp = qc.Loop(dummy.parameters["g1"].sweep(0, 1, num=10), 0).each(dummy2.parameters["g2"])
# print(lp.snapshot_base()["sweep_values"]["parameter"]["full_name"])

#for action in lp.snapshot_base()["actions"]:
    # print(action["full_name"])
#    pass

#lp1 = qc.Loop(dummy.parameters["g1"].sweep(0, 1, num=10), 0).each(lp)
#module_name = "qcodes.loops"
#module = importlib.import_module(module_name)
#mclass = getattr(module, "ActiveLoop")
# print(isinstance(lp1, mclass))

# print(lp1)


test_ivvi = IVVI("ivvi", "ASRL4::INSTR", reset=True)