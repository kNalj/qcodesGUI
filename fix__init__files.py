import qcodes as qc
import os
import inspect


def load_imports(path):
    known_problems = ["M3201A", "M3300A", "M4i", "ZIUHFLI"]
    # some instrument driver created problems and were not importable, those driver were excluded from importing
    # comment line 8 of this file to get errors explaining those problems
    print(path)
    files = os.listdir(path)
    print(files)
    imps = []

    for i in range(len(files)):
        name = files[i].split('.')
        if len(name) > 1:
            if name[1] == 'py' and name[0] != '__init__' and name[0] != 'add_instruments_to___init___script' and name[:3] != "py_" and name[0] == name[0].upper():
                name = name[0]
                if name not in known_problems:
                    imps.append(name)
        else:
            if name[0][:2] != "__":
                print("Working on " + name[0] + " folder")
                load_imports(path + "\\" + name[0])

    file = open(path + "\\" + '__init__.py', 'w')

    toWrite = '__all__ = '+str(imps)
    print(toWrite)

    file.write(toWrite)
    file.close()


path = os.path.dirname(inspect.getfile(qc)) + "\\instrument_drivers"
print(path)

load_imports(path)
