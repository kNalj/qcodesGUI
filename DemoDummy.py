from qcodes.instrument.base import Instrument
from qcodes.instrument.parameter import Parameter
from qcodes.utils.validators import Numbers
from random import randint


class DummyInstrument(Instrument):

    def __init__(self, name='dummy', gates=['dac1', 'dac2', 'dac3'], **kwargs):

        """
        Random measurement demonstration dummy

        Args:
            name (string): name for the instrument
            gates (list): list of names that is used to create parameters for
                            the instrument
        """
        super().__init__(name, **kwargs)

        # make gates
        for _, g in enumerate(gates):
            self.add_parameter(g,
                               parameter_class=Parameter,
                               initial_value=0,
                               label='Gate {}'.format(g),
                               unit="V",
                               vals=Numbers(-800, 400),
                               get_cmd=lambda: randint(0, 100), set_cmd=None)
