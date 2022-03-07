import urllib3
urllib3.disable_warnings()
import requests
import json
import time
import os 
from pathlib import Path

from novametrics.support.utils import load_post, save_post
#%%
def reo_optimize(post, API_KEY, root_url='https://developer.nrel.gov/api/reopt', poll_interval=10):
    """
    Function for polling the REopt API results URL until status is not "Optimizing..."
    :post: the API reo /job endpoint POST which define the Scenario with user inputs
    :param API_KEY: API key for accessing API on NREL's production server
    :param root_url: location of the API to poll; use 'http://localhost:8000' for localhost, not 0.0.0.0.8000
    :param poll_interval: seconds
    :return: dictionary response (once status is not "Optimizing...")
    """
    
    post_url = root_url + '/v1/job/?api_key=' + API_KEY
    results_url = root_url + '/v1/job/<run_uuid>/results/?api_key=' + API_KEY
    
    resp = requests.post(url=post_url, json=post)

    if not resp.ok:
        # print("Status code {}. {}".format(resp.status_code, resp.content))
        print("Status code {}.".format(resp.status_code))
    else:
        print("Response OK from {}.".format(post_url))
        run_id_dict = json.loads(resp.text)

        try:
            run_id = run_id_dict['run_uuid']
        except KeyError:
            msg = "Response from {} did not contain run_uuid.".format(post_url)

        return poller(url=results_url.replace('<run_uuid>', run_id), poll_interval=poll_interval)

#%%

def poller(url, poll_interval):
    """
    Function for polling the REopt API results URL until status is not "Optimizing..."
    :param url: results url to poll
    :param poll_interval: seconds
    :return: dictionary response (once status is not "Optimizing...")
    """
    key_error_count = 0
    key_error_threshold = 4
    status = "Optimizing..."
    print("Polling {} for results with interval of {}s...".format(url, poll_interval))
    while True:

        resp = requests.get(url=url, verify=False)
        resp_dict = json.loads(resp.text)

        try:
            status = resp_dict['outputs']['Scenario']['status']
        except KeyError:
            key_error_count += 1
            print('KeyError count: {}'.format(key_error_count))
            if key_error_count > key_error_threshold:
                print('Breaking polling loop due to KeyError count threshold of {} exceeded.'.format(key_error_threshold))
                break

        if status != "Optimizing...":
            time.sleep(poll_interval)
            resp = requests.get(url=url, verify=False)
            resp_dict = json.loads(resp.text)
            break
        else:
            # Add extra sleep time for slower-responding localhost calls
            # even while results are expected to be in response after status != "Optimizing..."
            time.sleep(poll_interval)

    return resp_dict
#%%


def run_reopt(post_folder, results_folder, api_key, start_folder = 1, root_url = 'https://developer.nrel.gov/api/reopt', overwrite = True, poll_interval = 10):
    """
    Runs REopt posts in `post_folder` and saves results to `results_folder`
    
    Results saved in same subfolder structure as inputs.
    Change `root_url` to 'http://localhost:8000' for localhost

    Parameters
    ----------
    post_folder : str
        Path to main folder for REopt posts. 
    results_folder : str
        Path to main folder for REopt results outputs.
    api_key : str
        API key for accessing API on NREL's production server.
    root_url: str 
        Location of the API to poll; use 'http://localhost:8000' for localhost.
    poll_interval: int
        Seconds between poll query
    """
    subfolders = next(os.walk(post_folder))[1]
    if len(subfolders) == 0:
        folder_list = [post_folder]
    else:
        folder_list = [os.path.join(post_folder, x) for x in subfolders]
    for building_folder in folder_list[(start_folder-1):len(folder_list)]:
        print("_"*60)
        print(f"Running Reopt for {building_folder}")
        file_paths = list(Path(building_folder).rglob("*.json"))
        path_list = [path.relative_to(post_folder) for path in file_paths]  
        
        for path in path_list:
            directory, post_name = os.path.split(path)
            
            post_dir = os.path.join(post_folder, directory)
            results_dir = os.path.join(results_folder, directory)
            results_file = os.path.join(results_folder, directory, post_name)
            
            Path(results_dir).mkdir(parents=True, exist_ok=True)
    
            if (not os.path.isfile(results_file)) or overwrite:
                print("Running REopt for", post_dir, "-", post_name)
                post = load_post(post_dir, post_name)
                reopt_results = reo_optimize(post, api_key, root_url=root_url, poll_interval=poll_interval)
                save_post(reopt_results, results_dir, post_name)
