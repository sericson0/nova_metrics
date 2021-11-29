import requests
import json
import time
from timeit import default_timer as timer
#import matplotlib.pyplot as plt
#import matplotlib.gridspec as gridspec


def poller(url, poll_interval=10):
    """
    Function for polling the REopt API results URL until status is not "Optimizing..."
    :param url: results url to poll
    :param poll_interval: seconds
    :return: dictionary response (once status is not "Optimizing...")
    """
    start = timer()
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
            time.sleep(10)
            resp = requests.get(url=url, verify=False)
            resp_dict = json.loads(resp.text)
            break
        else:
            time.sleep(poll_interval)
            
    end = timer()
    print('API call took', (end - start)/60, 'minutes')
    
    return resp_dict

def reo_optimize(post):
    API_KEY = 'EMXhDJ1wZrilRcOmFMHNIOASzWog8RLtJIPr22ep'
    root_url = 'https://developer.nrel.gov/api/reopt'
    post_url = root_url + '/v1/job/?api_key=' + API_KEY
    results_url = root_url + '/v1/job/<run_uuid>/results/?api_key=' + API_KEY

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

def reo_optimize_chpstaging(post):
    API_KEY = 'EMXhDJ1wZrilRcOmFMHNIOASzWog8RLtJIPr22ep'
    root_url = 'https://chpbeta-reopt-stage-api.its.nrel.gov'
    post_url = root_url + '/v1/job/?format=json&api_key=' + API_KEY
    results_url = root_url + '/v1/job/<run_uuid>/results/?api_key=' + API_KEY

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

def reo_inputs():
    root_url = 'http://localhost:8000'
    post_url = root_url + '/v1/help'
    
    resp = requests.post(url=post_url)

    if not resp.ok:
        print("Status code {}. {}".format(resp.status_code, resp.content))
    else:
        print("Response OK from {}.".format(post_url))
        run_id_dict = json.loads(resp.text)

        return run_id_dict
    
def reo_optimize_localhost(post):
    API_KEY = 'EMXhDJ1wZrilRcOmFMHNIOASzWog8RLtJIPr22ep'
    root_url = 'http://localhost:8000'
    post_url = root_url + '/v1/job/?format=json&api_key=' + API_KEY
    results_url = root_url + '/v1/job/<run_uuid>/results/?api_key=' + API_KEY

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

def reo_optimize_NickResource(post):
    API_KEY = 'EMXhDJ1wZrilRcOmFMHNIOASzWog8RLtJIPr22ep'
    root_url = 'http://10.60.70.53/v1'
    post_url = root_url + '/v1/job/?format=json' #&api_key=' + API_KEY
    results_url = root_url + '/v1/job/<run_uuid>/results' #/?api_key=' + API_KEY

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
            
def reo_optimize_development(post):
    API_KEY = 'EMXhDJ1wZrilRcOmFMHNIOASzWog8RLtJIPr22ep'
    root_url = 'https://reopt-dev-api1.nrel.gov'
    post_url = root_url + '/v1/job/?format=json&api_key=' + API_KEY
    results_url = root_url + '/v1/job/<run_uuid>/results/?api_key=' + API_KEY

    resp = requests.post(url=post_url, json=post, verify=False)

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

def results_plots(results_dict):
    
    bar_data = dict()
    bar_stor_data = dict()
    for name, results in results_dict.items():

        # Initilize figure layout and assign axes
        fig = plt.figure(figsize=(21,5), constrained_layout=True)
        gs = gridspec.GridSpec(ncols=16, nrows=1, figure=fig)
        H2_stack = fig.add_subplot(gs[:,1:3])
        H2_stack.set_ylim(0, 275)

        H2_storage_stack = fig.add_subplot(gs[:,0])
        H2_storage_stack.set_ylim(0, 50)

        loadAx = fig.add_subplot(gs[0,3:])
        loadAx.set_title(name, fontsize=16)

        # Plot base and total loads
        plotrange = 24*7
        bar_data[name] = dict()
        bar_stor_data[name] = dict()


        utility_load = results['outputs']['Scenario']['Site']['ElectricTariff']['year_one_to_load_series_kw']
        PV_load = results['outputs']['Scenario']['Site']['PV']['year_one_to_load_series_kw']
        BESS_load = results['outputs']['Scenario']['Site']['Storage']['year_one_to_load_series_kw']

        load = results['outputs']['Scenario']['Site']['LoadProfile']['year_one_electric_load_series_kw']
        loadAx.stackplot(range(plotrange),[utility_load[:plotrange], BESS_load[:plotrange], PV_load[:plotrange]], 
                         labels = ['Utility', 'BESS', 'Solar PV'],
                         colors = ['tab:blue', 'maroon', 'tab:orange'])
        loadAx.legend(loc='upper left')

        pv_size = results['outputs']['Scenario']['Site']['PV']['size_kw']
        batt_kw = results['outputs']['Scenario']['Site']['Storage']['size_kw']
        batt_kwh = results['outputs']['Scenario']['Site']['Storage']['size_kwh']

        bar_names = ['Solar PV', 'Battery']
        vals = [pv_size, batt_kw]
        for bar_name, val in zip(bar_names, vals):
            bar_data[name][bar_name] = val

        H2_stack.tick_params(axis='x', labelrotation = 30)
        H2_stack.set_ylabel('Power (kW)')
        H2_stack.bar(*zip(*bar_data[name].items()), color=['maroon', 'tab:orange'])

        bar_names = ['Battery']
        vals = [batt_kwh]
        for bar_name, val in zip(bar_names, vals):
            bar_stor_data[name][bar_name] = val

        H2_storage_stack.tick_params(axis='x', labelrotation = 30)
        H2_storage_stack.set_ylabel('Energy (kWh)')
        H2_storage_stack.bar(*zip(*bar_stor_data[name].items()), color=['black'])

        plt.show()
