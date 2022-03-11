import os
import tarfile
import subprocess
import yaml
import time
import shutil
from buildstockbatch.localdocker import LocalDockerBatch
from pathlib import Path
#%%

def update_temp_output_folder(yaml_path, temp_folder_name = "temp_folder"):
    with open(yaml_path) as f:
        doc = yaml.safe_load(f)
        doc['output_directory'] = temp_folder_name
    with open(yaml_path, 'w') as f:
        yaml.safe_dump(doc, f, sort_keys = False)

def run_resstock(main_folder, yaml_name, resstock_outputs_folder, temp_folder_name = "temp_folder", 
                 simulations_job = "simulations_job0.tar.gz", root_folder = "up00/", save_files = ("in.xml", "schedules.csv"), n_workers = 1):
    t1 = time.time()
    Path(os.path.join(main_folder, temp_folder_name)).mkdir(parents=True, exist_ok=True)
    yaml_path = os.path.join(main_folder, yaml_name)
    update_temp_output_folder(yaml_path, temp_folder_name)
    print("Calling Buildstockbatch")
    call_buildstock_batch(yaml_path, run_type = "buildstock_docker")
    print("Extracting Buildstockbatch outputs")
    
    Path(os.path.join(main_folder, resstock_outputs_folder)).mkdir(parents=True, exist_ok=True)
    extract_bsb_outputs(main_folder, resstock_outputs_folder, temp_folder_name, simulations_job, root_folder, save_files)
    print(f"Time to run ResStock was: {time.time() - t1}")
    
# def call_buildstock_batch(yaml_path, run_type = "buildstock_docker"):
#     runvals = [run_type, yaml_path]
#     subprocess.run(runvals)


def call_buildstock_batch(yaml_path, run_type = "buildstock_docker"):
    docker_buildstock_batch(yaml_path)

def docker_buildstock_batch(yaml_path):    
    batch = LocalDockerBatch(yaml_path)
    batch.run_batch(measures_only = True, n_jobs = n_workers)
    # batch.process_results()    #For if measures only doesnt work

def members(tf, root_folder, save_files):
    root_folder = "up00/"
    l = len(root_folder)
    for member in tf.getmembers():
        if member.path.startswith(root_folder) and member.path.endswith(save_files):
            member.path = member.path[l:].replace("run/", "")
            yield member


def extract_bsb_outputs(main_folder, resstock_outputs_folder, temp_outputs_folder = "temp_folder", simulations_job = "simulations_job0.tar.gz",
                        root_folder = "up00/", save_files = ("in.xml", "schedules.csv", "results_annual.csv")):
    filename = os.path.join(main_folder, temp_outputs_folder, "simulation_output", simulations_job)
    with tarfile.open(filename, "r:gz") as tar:
        tar.extractall(os.path.join(main_folder, resstock_outputs_folder), members=members(tar, root_folder, save_files))
    shutil.rmtree(os.path.join(main_folder, temp_outputs_folder))





# yaml_name = "resstock_inputs.yml"
# main_folder = "C:/Users/sean/Desktop/test ResStock"  
# resstock_outputs_folder = "Resstock Outputs"
# run_resstock(main_folder, yaml_name, resstock_outputs_folder)  
# extract_bsb_outputs(main_folder, resstock_outputs_folder)    
  
    


# help(buildstockbatch)



# import docker
# try:
#     docker_client = docker.DockerClient.from_env()
#     docker_client.ping()
# except:  # noqa: E722 (allow bare except in this case because error can be a weird non-class Windows API error)
#     print('The docker server did not respond, make sure Docker Desktop is started then retry.')
