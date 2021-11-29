import os
from shutil import copytree
import pathlib


def run_resstock(main_folder, inputs):
    pathlib.Path(os.path.join(main_folder, "OCHRE Inputs")).mkdir(parents=True, exist_ok=True)
    for location in inputs["Locations"]:
        if not os.path.exists(os.path.join(os.path.join(main_folder, "OCHRE Inputs", location))):
            print(location)
            pathlib.Path(os.path.join(main_folder, "OCHRE Inputs", location)).mkdir(parents=True, exist_ok=True)
            ###
            copytree(os.path.join("../Testing Runs/OCHRE Inputs/New York/Baseline"),  os.path.join(main_folder, "OCHRE Inputs", location, "Baseline"))
            copytree(os.path.join("../Testing Runs/OCHRE Inputs/New York/Better"),  os.path.join(main_folder, "OCHRE Inputs", location, "Better"))




# path = "C:/resstock/project_testing/testing_baseline/simulation_output/simulations_job0.tar.gz"
# # def extract_resstock_results(resstock_output_folder, ochre_input_folder):
# import os    
# import tarfile
# from pathlib import Path



# tar_files = [member for member in tar.getmembers() ]


# #%%
# tar = tarfile.open(path, "r:gz")
# for member in tar:
#     if ("in.xml" in member.name) or ("schedules" in member.name):
#         building_name = member.name.split("/")[1]
#         building_folder = os.path.join(resstock_output_folder, building_name)
#         Path(building_folder).mkdir(parents=True, exist_ok=True)
#         member.name = os.path.basename(member.name)
#         tar.extract(member, building_folder)
        
      

#%%
