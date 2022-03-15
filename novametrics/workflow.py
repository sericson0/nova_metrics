#%%
#Update these values
import os 
import sys
# os.chdir(os.path.dirname(__file__))

# sys.path.insert(1, "../")
import pandas as pd
import argparse
from novametrics.inputs.create_reopt_posts import create_reopt_posts
from novametrics.run_programs.run_reopt import run_reopt
from novametrics.run_programs.run_ochre import run_ochre
from novametrics.run_programs.run_resstock import run_resstock
from novametrics.analyze_results.generate_metrics import generate_metrics, generate_timeseries
#%%
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('main_folder', nargs='?', default=".", help =  "File path to main folder for inputs and results.")
    parser.add_argument("-b", "--buildstock", action="store_true", help = "Query ResStock and run building simulations.")
    parser.add_argument("-o", "--ochre", action="store_true", help = "Run OCHRE simulations.")
    parser.add_argument("-p", "--posts", action="store_true", help = "Generate REopt posts.")
    parser.add_argument("-r", "--reopt", action="store_true", help = "Run REopt for each generated post")
    parser.add_argument("-m", "--metrics", action="store_true", help = "Generate metrics.")
    parser.add_argument("-a", "--all", action="store_true", help = "Run full workflow.")
    parser.add_argument("-k", "--keep_runs", action="store_false", help = "Does not overwrite runs. Defaults to overwriting.")
    parser.add_argument("-i", "--inputs_file_path", default = "Inputs.xlsx", help = "Optionally specify path to input xlsx file (relative to main folder).")
    parser.add_argument("-g", "--by_building", action = "store_true", help = "If specified then runs REopt post and metrics for each building type")
    parser.add_argument("-s", "--start", type=int, nargs='?', default=1, help = "If specified then sets subfolder to begin running REopt")
    parser.add_argument("--n_workers", type=int, nargs='?', default=2, help = "Number of workers to run in parallel for buildstockbatcho")
    args = parser.parse_args()

    main_folder = args.main_folder
    if not os.path.isabs(main_folder):
        main_folder = os.path.join(os.getcwd(), main_folder)
    inputs_file_name = args.inputs_file_path
    
    inputs = pd.read_excel(os.path.join(main_folder, inputs_file_name), None)

    

    filepaths = inputs["File Paths"]
    filepaths= dict(zip(filepaths.path_type, filepaths.path_name))


    api_keys = inputs["API Keys"]
    api_keys = dict(zip(api_keys.key_name, api_keys.key_val))
    
    #%%
    if "resstock_output_main_folder" not in filepaths:
            filepaths["resstock_output_main_folder"] = "ResStock"
            
    if args.all or args.buildstock:
        print("Running buildstockbatch to query ResStock")
        if "resstock_yaml" in filepaths:
            run_resstock(main_folder, filepaths["resstock_yaml"], filepaths["resstock_output_main_folder"], temp_folder_name = "temp_folder", 
                            simulations_job = "simulations_job0.tar.gz", root_folder = "up00/", save_files = ("in.xml", "schedules.csv"), n_workers = args.n_workers)
        elif os.path.exists("resstock.yml"):
            print("No resstock yaml file specified. Defaulting to resstock.yml in main folder")
           
            run_resstock(main_folder, "resstock.yml", filepaths["resstock_output_main_folder"], temp_folder_name = "temp_folder", 
                        simulations_job = "simulations_job0.tar.gz", root_folder = "up00/", save_files = ("in.xml", "schedules.csv"), n_workers = args.n_workers)
        else:
            raise Exception("Could not fine resstock.yml file. Please specify name in the Inputs File Paths tab or add a file named resstock.yml to the main folder.")
    
    #Run by building if all 
    if args.all:
        args.by_building = True

    #Set OCHRE values
    if "OCHRE" in inputs:
        ochre_controls = inputs["OCHRE"]
        ochre_controls = dict(zip(ochre_controls.ochre_type, ochre_controls.ochre_value))
    else:
        ochre_controls = {}

    if "ochre_inputs_main_folder" in filepaths:
        ochre_controls["ochre_inputs_main_folder"] = filepaths["ochre_inputs_main_folder"]
    elif "resstock_outputs_main_folder" in filepaths:
        ochre_controls["ochre_inputs_main_folder"] = filepaths["resstock_outputs_main_folder"]
        
    if "ochre_outputs_main_folder" in filepaths:
        ochre_controls["ochre_outputs_main_folder"] = filepaths["ochre_outputs_main_folder"]
    
    if args.all or args.ochre:
        print("Running OCHRE")
        run_ochre(ochre_controls)
    
    if args.posts or args.all:
        print("Creating REopt posts.")
        create_reopt_posts(main_folder, inputs_file_name, filepaths["default_values_file"], filepaths["reopt_posts"], by_building = args.by_building, add_pv_prod_factor = True,
                       solar_profile_folder = filepaths["solar_profile_folder"], pv_watts_api_key = api_keys["pv_watts"], ochre_controls = ochre_controls)
        
    if args.reopt or args.all:
        if "reopt_root_url" in filepaths:
            root_url = filepaths["reopt_root_url"]
        else:
            root_url = 'https://developer.nrel.gov/api/reopt'
        run_reopt(filepaths["reopt_posts"], filepaths["reopt_results"], api_keys["reopt"], start_folder = args.start, root_url = root_url, overwrite = args.keep_runs)

    if args.metrics or args.all:
        metrics_inputs = inputs["Generate Metrics"]
        if "wholesale_price_folder" in filepaths:
            wholesale_price_path = filepaths["wholesale_price_folder"]
        else:
            wholesale_price_path = "./"
    
        generate_metrics(filepaths["reopt_results"], metrics_inputs, filepaths["metrics_folder"], "Metrics.xlsx", wholesale_price_path, by_building = args.by_building)
        generate_timeseries(filepaths["reopt_results"], os.path.join(filepaths["metrics_folder"], "Timeseries"))

    
    
if __name__ == "__main__":
    main()



