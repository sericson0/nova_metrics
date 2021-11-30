import os
from shutil import copytree
import pathlib


def run_resstock(main_folder, inputs):
    pass
    #Will update once ResStock OCHRE connection is updated

    # pathlib.Path(os.path.join(main_folder, "OCHRE Inputs")).mkdir(parents=True, exist_ok=True)
    # for location in inputs["Locations"]:
    #     if not os.path.exists(os.path.join(os.path.join(main_folder, "OCHRE Inputs", location))):
    #         print(location)
    #         pathlib.Path(os.path.join(main_folder, "OCHRE Inputs", location)).mkdir(parents=True, exist_ok=True)
    #         ###
    #         copytree(os.path.join("../Testing Runs/OCHRE Inputs/New York/Baseline"),  os.path.join(main_folder, "OCHRE Inputs", location, "Baseline"))
    #         copytree(os.path.join("../Testing Runs/OCHRE Inputs/New York/Better"),  os.path.join(main_folder, "OCHRE Inputs", location, "Better"))



