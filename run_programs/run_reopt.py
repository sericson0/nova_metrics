# API_KEY = 'eb14ACcUKmGtJT8WeB4kuJayhFNhWTSxpLTonqZ7'
# import os
# os.chdir(os.path.dirname(__file__))
#%%
import urllib3
urllib3.disable_warnings()
import requests
import json
import time
import os 
from pathlib import Path

from nova_metrics.support.utils import *
from nova_metrics.support.logger import log
#%%
def reo_optimize(post, api_key):
    # API_KEY = 'yOODa4jmZy1q3Wd6lkQcne6izi3nq2YSIIlCQkOg'
    root_url = 'https://developer.nrel.gov/api/reopt'
    post_url = root_url + '/v1/job/?api_key=' + api_key
    results_url = root_url + '/v1/job/<run_uuid>/results/?api_key=' + api_key

    resp = requests.post(url=post_url, json=post)

    if not resp.ok:
        print("Status code {}. {}".format(resp.status_code, resp.content))
    else:
        print("Response OK from {}.".format(post_url))
        run_id_dict = json.loads(resp.text)

        try:
            run_id = run_id_dict['run_uuid']
        except KeyError:
            msg = "Response from {} did not contain run_uuid.".format(post_url)

        return poller(url=results_url.replace('<run_uuid>', run_id))

#%%

def poller(url, poll_interval=5):
    """
    Function for polling the REopt API results URL until status is not "Optimizing..."
    :param url: results url to poll
    :param poll_interval: seconds
    :return: dictionary response (once status is not "Optimizing...")
    """

    key_error_count = 0
    key_error_threshold = 3
    status = "Optimizing..."
    log.info("Polling {} for results with interval of {}s...".format(url, poll_interval))
    while True:

        resp = requests.get(url=url, verify=False)
        resp_dict = json.loads(resp.content)

        try:
            status = resp_dict['outputs']['Scenario']['status']
        except KeyError:
            key_error_count += 1
            log.info('KeyError count: {}'.format(key_error_count))
            if key_error_count > key_error_threshold:
                log.info('Breaking polling loop due to KeyError count threshold of {} exceeded.'
                         .format(key_error_threshold))
                break

        if status != "Optimizing...":
            break
        else:
            time.sleep(poll_interval)

    return resp_dict
#%%


def run_reopt(post_folder, results_folder, api_key, reopt_optimize_fun = reo_optimize):
    # Path(os.path.join(main_folder, "REopt Results")).mkdir(parents=True, exist_ok=True) 
    #Something magical happens here
    file_paths = list(Path(post_folder).rglob("*.json"))
    path_list = [path.relative_to(post_folder) for path in file_paths]  
    
    for path in path_list:
        directory, post_name = os.path.split(path)
        
        post_dir = os.path.join(post_folder, directory)
        results_dir = os.path.join(results_folder, directory)
        results_file = os.path.join(results_folder, directory, post_name)
        
        Path(results_dir).mkdir(parents=True, exist_ok=True)

        if not os.path.isfile(results_file):
            print("Running REopt for", post_name)
            post = load_post(post_dir, post_name)
            reopt_results = reo_optimize(post, api_key)
            save_post(reopt_results, results_dir, post_name)
            
#%%
# main_folder = "../Testing Runs"
# path = os.path.join(main_folder, "Posts", "New York", "Baseline", "Flat-Rate")
# post = load_post(path, "New York-Baseline-Flat-Rate-fixed_PV_6kW_NEM.json")

# A = reo_optimize(post, API_KEY)
# run_reopt(main_folder, reo_optimize, API_KEY)
# reopt_results = reo_optimize(post, API_KEY)

# save_post(retail_store_results, "../Setup For Batch Runs", "test.json")


