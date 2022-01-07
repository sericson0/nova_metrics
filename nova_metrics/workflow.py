#%%
#Update these values
import os 
import sys
# os.chdir(os.path.dirname(__file__))
sys.path.insert(1, "../")
import pandas as pd
import argparse
from nova_metrics.inputs.create_reopt_posts import create_reopt_posts
from nova_metrics.run_programs.run_reopt import run_reopt
from nova_metrics.analyze_results.generate_metrics import generate_metrics, generate_timeseries
#%%
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("main_folder", help = "File path to main folder for inputs and results.")
    parser.add_argument("-p", "--posts", action="store_true", help = "Generate REopt posts.")
    parser.add_argument("-r", "--reopt", action="store_true", help = "Run REopt for each generated post")
    parser.add_argument("-m", "--metrics", action="store_true", help = "Generate metrics.")
    parser.add_argument("-a", "--all", action="store_true", help = "Run full workflow.")
    parser.add_argument("-k", "--keep_runs", action="store_false", help = "Does not overwrite runs. Defaults to overwriting.")
    parser.add_argument("-i", "--inputs_file_path", default = "Inputs.xlsx", help = "Optionally specify path to input xlsx file (relative to main folder).")
    
    args = parser.parse_args()
    
    #TODO check if changing directory is necessary
    os.chdir(args.main_folder)
    main_folder = "./"
    
    inputs_file_name = args.inputs_file_path
    inputs_file = os.path.join(main_folder, inputs_file_name)


    filepaths = pd.read_excel(inputs_file, sheet_name = "File Paths")
    filepaths= dict(zip(filepaths.path_type, filepaths.path_name))

    api_keys = pd.read_excel(inputs_file, sheet_name = "API Keys")
    api_keys = dict(zip(api_keys.key_name, api_keys.key_val))
    #%%
    if args.posts or args.all:
        if "ochre_output_main_folder" in filepaths:
            ochre_out_folder = filepaths["ochre_output_main_folder"]
        else:
            ochre_out_folder = ""
        create_reopt_posts(main_folder, inputs_file_name, filepaths["default_values_file"], filepaths["reopt_posts"], add_pv_prod_factor = True,
                       solar_profile_folder = filepaths["solar_profile_folder"], pv_watts_api_key = api_keys["pv_watts"], ochre_output_main_folder = ochre_out_folder)
        
    if args.reopt or args.all:
        if "reopt_root_url" in api_keys:
            root_url = api_keys["reopt_root_url"]
            print(root_url)
        else:
            root_url = 'https://developer.nrel.gov/api/reopt'
        run_reopt(filepaths["reopt_posts"], filepaths["reopt_results"], api_keys["reopt"], root_url = root_url, overwrite = args.keep_runs)

    if args.metrics or args.all:
        metrics_inputs = pd.read_excel(inputs_file, sheet_name = "Generate Metrics")
        if "wholesale_price_folder" in filepaths:
            wholesale_price_path = filepaths["wholesale_price_folder"]
        else:
            wholesale_price_path = "./"
    
        generate_metrics(filepaths["reopt_results"], metrics_inputs, filepaths["metrics_folder"], "Metrics.xlsx", wholesale_price_path)
        generate_timeseries(filepaths["reopt_results"], os.path.join(filepaths["metrics_folder"], "Timeseries"))

    
    
if __name__ == "__main__":
    main()



