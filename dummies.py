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

"""dummy = DummyInstrument("amen", gates=["g1", "g2"])
dummy2 = DummyInstrument("haleluja", gates=["g1", "g2"])

lp = qc.Loop(dummy.parameters["g1"].sweep(0, 1, num=10), 0).each(dummy2.parameters["g2"])
print(lp.snapshot_base()["sweep_values"]["parameter"]["full_name"])

""""""for action in lp.snapshot_base()["actions"]:
    print(action["full_name"])""""""

lp1 = qc.Loop(dummy.parameters["g1"].sweep(0, 1, num=10), 0).each(lp)
module_name = "qcodes.loops"
module = importlib.import_module(module_name)
mclass = getattr(module, "ActiveLoop")
print(isinstance(lp1, mclass))
module_name = "qcodes.instrument.base"
module = importlib.import_module(module_name)
mclass = getattr(module, "Instrument")
print(isinstance(dummy, mclass))"""

from PyQt5.QtWidgets import  QApplication, QTreeWidget, QTreeWidgetItem

class ViewTree(QTreeWidget):
    def __init__(self, value):
        super().__init__()
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
    window = ViewTree({ 'key1': 'value1', 'key3': [1,2,3, { 1: 3, 7 : 9}]})
    window.show()
    app.exec_()