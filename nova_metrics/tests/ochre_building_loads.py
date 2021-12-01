#!/usr/bin/env python
# coding: utf-8
import os 
import pandas as pd
os.chdir(os.path.dirname(__file__))
from nova_metrics.inputs.create_reopt_posts import create_reopt_posts
from nova_metrics.run_programs.run_reopt import run_reopt, reo_optimize
from nova_metrics.analyze_results.generate_metrics import generate_metrics, generate_timeseries
#%%
main_folder = "./ochre_building_loads"
inputs_file_name = "Inputs.xlsx"
inputs_file = os.path.join(main_folder, inputs_file_name)


filepaths = pd.read_excel(inputs_file, sheet_name = "File Paths")
filepaths= dict(zip(filepaths.path_type, filepaths.path_name))

api_keys = pd.read_excel(inputs_file, sheet_name = "API Keys")
api_keys = dict(zip(api_keys.key_name, api_keys.key_val))
#%%
create_reopt_posts(main_folder, inputs_file_name, filepaths["default_values_file"], filepaths["reopt_posts"], add_pv_prod_factor = True,
                   solar_profile_folder = filepaths["solar_profile_folder"], pv_watts_api_key = api_keys["pv_watts"], ochre_output_main_folder = filepaths["ochre_outputs"])

run_reopt(filepaths["reopt_posts"], filepaths["reopt_results"], api_keys["reopt"], reo_optimize)


metrics_inputs = pd.read_excel(inputs_file, sheet_name = "Generate Metrics")
generate_metrics(filepaths["reopt_results"], metrics_inputs, filepaths["metrics_folder"], "Metrics.xlsx", filepaths["wholesale_price_folder"])

generate_timeseries(filepaths["reopt_results"], os.path.join(filepaths["metrics_folder"], "Timeseries"))

