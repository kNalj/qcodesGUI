import qcodes as qc
from qcodes.tests.instrument_mocks import DummyInstrument
        
#dmm = DummyInstrument('dmm', gates=['v1', 'v2'])
#dac = DummyInstrument('dac', gates=['ch1', 'ch2'])

names = ["dmm","dac"]
instruments = {"dmm" : DummyInstrument('dmm', gates=['v1', 'v2']), "dac" : DummyInstrument('dac', gates=['ch1', 'ch2'])}


    

"""uncomment the line below to have acces to extra data (states of the instruments)
creates additional dict entry with data about all instruments used"""
station = qc.Station()
for key, value in instruments.items():
    print(key, value)
    station.add_component(value, key)

parameter_name = "v1"
measure_parameter = instruments[names[0]].parameters[parameter_name]

sweep_parameter_name = "ch1"
sweep_parameter  = instruments[names[1]].parameters[sweep_parameter_name]

#look into this dmm.v1 (how the hell is this v1 created, some dynamic magical monstrosity)
lp = qc.Loop(sweep_parameter.sweep(0, 10, 10), 0).each(measure_parameter)

#data = lp.run('data/dataset')
"""print(station.components)
print(instruments[names[0]].parameters)
print(instruments[names[1]].parameters)"""

print(type(instruments["dmm"]))

c2 = instruments["dmm"].__class__
new2 = c2()
print(type(new2))