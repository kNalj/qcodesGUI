"""
This file is used to set instrument names and addresses and save them as default names/addresses for a type of instrument

This file should be different for each computer

Guidelines: Open NI MAX / NI VISA interface

Find connected instruments

For each recognized instrument add a line to the instrument data dictionary

EXAMPLE:

    instrument_data = {"IVVI": ["dac", "ASRL5::INSTR"],
                        "Agilent": ["dmm", "ASRL6::INSTR"],
                        "Some_instrument": ["Some_instruments_name", "Some_instruments_address"]
                        }
"""

# this particular data is for the computer in the lab closest to the exit of the lab
instrument_data = {
"IVVI": ["dac", "ASRL5::INSTR"],
"Agilent_34400A":  ["dmm", "USB0::0x2A8D::0x0101::MY54505177::INSTR"],
"Agilent_34450A": ["dmm", "USB0::0x2A8D::0xB318::MY58020037::INSTR"]
}
