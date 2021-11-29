import pandas as pd
import numpy as np
from math import floor

def simulate_outage(init_time_step, batt_kwh, batt_kw, batt_roundtrip_efficiency, batt_soc_kwh, crit_load, n_timesteps):
    for i in range(n_timesteps):
        t = (init_time_step + i) % n_timesteps  # for wrapping around end of year
        load_kw = crit_load[t]

        if load_kw < 0:  # load is met
            if batt_soc_kwh < batt_kwh:  # charge battery if there's room in the battery
                batt_soc_kwh += min( 
                    batt_kwh - batt_soc_kwh,     # room available
                    batt_kw  * batt_roundtrip_efficiency,  # inverter capacity
                    -load_kw  * batt_roundtrip_efficiency,  # excess energy
                )
        else:  # check if we can meet load with generator then storage
            if min(batt_kw, batt_soc_kwh) >= load_kw:  # battery can carry balance
                # prevent battery charge from going negative
                batt_soc_kwh = max(0, batt_soc_kwh - load_kw)
                load_kw = 0


        if round(load_kw, 5) > 0:  # failed to meet load in this time step
            return float(i) 

    return n_timesteps   # met the critical load for all time steps

def simulate_outages(batt_kwh=0, batt_kw=0, pv_kw_ac_hourly=0, init_soc=0, critical_loads_kw=[], batt_roundtrip_efficiency=0.829):

    n_timesteps = len(critical_loads_kw)
    r = [0] * n_timesteps

    if batt_kw == 0 or batt_kwh == 0:
        init_soc = [0] * n_timesteps  # default is None
        if ((pv_kw_ac_hourly in [None, []]) or (sum(pv_kw_ac_hourly) == 0)):
            return {"resilience_by_timestep": r,
                    "resilience_hours_min": 0,
                    "resilience_hours_max": 0,
                    "resilience_hours_avg": 0,
                    "outage_durations": [],
                    "probs_of_surviving": [],
                    "probs_of_surviving_by_month": [[0] for _ in range(12)],
                    "probs_of_surviving_by_hour_of_the_day": [[0] for _ in range(24)],
                    }

    if pv_kw_ac_hourly in [None, []]:
        pv_kw_ac_hourly = [0] * n_timesteps
    load_minus_der = [ld - pv for (pv, ld) in zip(pv_kw_ac_hourly, critical_loads_kw)]
    '''
    Simulation starts here
    '''
    for time_step in range(n_timesteps):
        r[time_step] = simulate_outage(
            init_time_step=time_step,
            batt_kwh=batt_kwh,
            batt_kw=batt_kw,
            batt_roundtrip_efficiency=batt_roundtrip_efficiency,
            batt_soc_kwh=init_soc[time_step] * batt_kwh,
            crit_load=load_minus_der,
            n_timesteps=n_timesteps
        )
    results = process_results(r, n_timesteps)
    return results


def process_results(r, n_timesteps):

    r_min = min(r)
    r_max = max(r)
    r_avg = round((float(sum(r)) / float(len(r))), 2)

    # Create a time series of 8760*n_steps_per_hour elements starting on 1/1/2017
    time = pd.date_range('1/1/2017', periods=8760, freq='{}min'.format(60))
    r_series = pd.Series(r, index=time)

    r_group_month = r_series.groupby(r_series.index.month)
    r_group_hour = r_series.groupby(r_series.index.hour)

    x_vals = list(range(1, int(floor(r_max)+1)))
    y_vals = list()
    y_vals_group_month = list()
    y_vals_group_hour = list()

    for hrs in x_vals:
        y_vals.append(round(float(sum([1 if h >= hrs else 0 for h in r])) / float(n_timesteps), 4))

    if len(x_vals) > 0:
        width = 0
        for k, v in r_group_month:
            tmp = list()
            max_hr = int(v.max()) + 1
            for hrs in range(max_hr):
                tmp.append(round(float(sum([1 if h >= hrs else 0 for h in v])) / float(len(v)), 4))
            y_vals_group_month.append(tmp)
            if max_hr > width:
                width = max_hr

        # PostgreSQL requires that the arrays are rectangular
        for i, v in enumerate(y_vals_group_month):
            y_vals_group_month[i] = v + [0] * (width - len(v))

        width = 0
        for k, v in r_group_hour:
            tmp = list()
            max_hr = int(v.max()) + 1
            for hrs in range(max_hr):
                tmp.append(round(float(sum([1 if h >= hrs else 0 for h in v])) / float(len(v)), 4))
            y_vals_group_hour.append(tmp)
            if max_hr > width:
                width = max_hr

        # PostgreSQL requires that the arrays are rectangular
        for i, v in enumerate(y_vals_group_hour):
            y_vals_group_hour[i] = v + [0] * (width - len(v))

    return {"resilience_by_timestep": r,
            "resilience_hours_min": r_min,
            "resilience_hours_max": r_max,
            "resilience_hours_avg": r_avg,
            "outage_durations": x_vals,
            "probs_of_surviving": y_vals,
            "probs_of_surviving_by_month": y_vals_group_month,
            "probs_of_surviving_by_hour_of_the_day": y_vals_group_hour,
            }