"""
Functions to calculate and return metrics from REopt results

Metrics are separated into the following categories: 
-Financial : Monetary metrics such as LCC, NPV, and annual bill
-Home : Home performance metrics such as annual net load
-External : Utility and societal metrics such as emissions and grid peak contribution
-System performance : Metrics for each system (PV, Storage, HP, ERWH)

Metrics are categorized into zero-baseline and comparison. 
Zero-baseline are metrics which do not need a baseline to calculate. Examples
include annual building load and system performance.
Comparison metrics are an increase / decrease compared to a baseline or are
a rating compared to a baseline. Examples are NPV, load reduction, or HERS rating. 

Function `generate_metrics` returns an Excel spreadsheet of compiled metrics, while
`generate_timeseries` returns csv files of timeseries values for each scenario. 

"""
from pathlib import Path    
import os
import glob
import numpy as np
import pandas as pd
pd.set_option('mode.chained_assignment', None)
from analyze_results.extract_results import extract_results
from support.utils import not_none
HOURS = 8760
#%%
def cover_factor_metrics(results):
    """
    Return dictionary including cover factor demand and cover factor supply.
    
    Cover factor demand is generation consumed by building / building gross load.
    Cover factor supply is fraction of PV generation consumed onsite.
    """
    d = {}
    d["Home-cover_factor_demand"] = 1 - (results["load"]["annual_grid_purchases"]/sum(results["load"]["home_load"]))
    
    if results["PV"]["kw_capacity"] == 0:
        d["Home-cover_factor_supply"] = 0
    else:
        d["Home-cover_factor_supply"] = 1 - (results["PV"]["annual_exports"]/results["PV"]["annual_generation"]) 
    return d
#%%
def calculate_utility_metrics(results, grid_prices = []):
    if len(grid_prices) == 0:
        return {"External-grid_peak_contribution": None, "External-average_grid_cost_dollars_per_kwh": None}
    else:    
        d = {}
        net_load = results["load"]["net_load"]
        top_5_pct_num_hours = 438
        top_loads = np.mean(sorted(net_load, reverse=True)[:10])
    
        top_grid_periods = sorted(range(len(net_load)), key=lambda i: grid_prices[i], reverse=True)[:top_5_pct_num_hours]
        
        load_during_peak_periods = np.mean([net_load[p] for p in top_grid_periods])
        grid_peak_contribution = load_during_peak_periods / top_loads
        
        d["External-grid_peak_contribution"] = grid_peak_contribution
    
        
    
        d["External-average_grid_cost_dollars_per_kwh"] = sum([results["load"]["net_load"][h]*grid_prices[h]/1000 for h in range(HOURS)])/sum(results["load"]["home_load"])
        d["External-total_grid_cost_dollars"] = sum([results["load"]["net_load"][h]*grid_prices[h]/1000 for h in range(HOURS)])
        return d
#%%
    
def zero_baseline_metrics(results, grid_prices = []):
    """
    Return metrics which do not need a comparison to other results for baselining 
    
    Optional input of `grid_prices` vector to calculate wholesale grid metrics.
    
    """
    d = {}
    d["filename"] = results["metadata"]["filename"]
    d["Run Type-latitude"] = results["metadata"]["latitude"]
    d["Run Type-longitude"] = results["metadata"]["longitude"]
    
    d["PV-kw_capacity"] = results["PV"]["kw_capacity"]
    d["PV-annual_generation_kwh"] = results["PV"]["annual_generation"]
    d["PV-average_capacity_factor"] = results["PV"]["pv_average_capacity_factor"]
    d["PV-upfront_capital_cost"] = results["PV"]["upfront_capital_cost"]
    
    d["Storage-kw_capacity"] = results["Storage"]["kw_capacity"]
    d["Storage-kwh_capacity"] = results["Storage"]["kwh_capacity"]
    d["Storage-capacity_utilization_percent"] = 0
    if results["Storage"]["kwh_capacity"]:
        d["Storage-capacity_utilization_percent"] = (results["Storage"]["annual_generation"]+results["Storage"]["annual_load"]) / (results["Storage"]["kwh_capacity"]*HOURS) * 100
        
    d["Storage-upfront_capital_cost"]  = results["Storage"]["upfront_capital_cost"]
    
    
    d["HP-kw_capacity"] = results["FlexTechHP"]["kw_capacity"]
    d["HP-upfront_capital_cost"] = results["FlexTechHP"]["upfront_capital_cost"]
    
    d["ERWH-kw_capacity"] = results["FlexTechERWH"]["kw_capacity"]
    d["ERWH-upfront_capital_cost"] = results["FlexTechERWH"]["upfront_capital_cost"]
    
    d["ERWH-kw_capacity"] = results["FlexTechHPWH"]["kw_capacity"]
    d["ERWH-upfront_capital_cost"] = results["FlexTechHPWH"]["upfront_capital_cost"]
    
    d["Home-annual_comfort_penalty_dollars"] = sum(results["temperature"]["comfort_penalty"])
    
    d["Financial-lcc"] = results["financial"]["LCC"] 
    d["Financial-net_capital_costs"] = results["financial"]["net_capital_costs"]
    d["Financial-initial_capital_costs"] = results["financial"]["initial_capital_costs"]
    
    d["Home-annual_net_load"] = sum(results["load"]["net_load"]) 
    d["Home-annual_home_load"] = sum(results["load"]["home_load"]) 
    
    d["External-annual_grid_purchases_kwh"] = results["load"]["annual_grid_purchases"] 
    
    d["Financial-annual_bill"] = results["utility_bill"]["annual_bill"]
    
    #ChangesFromMcKnight: Changed assignment from total to year_one
    d["Financial-annual_energy_bill"] = results["utility_bill"]["annual_utility_energy_cost"]
    d["Financial-annual_demand_charges"] = results["utility_bill"]["annual_utility_demand_cost"]
    
    # d["External-annual_emissions_tons_CO2"] = results["emissions"]["annual_emissions_tons_CO2"]
    # d["External-avg_emissions_rate_lb_CO2_per_kwh"] = results["emissions"]["annual_emissions_lb_CO2"]/d["Home-annual_home_load"]
    
    d["Home-ra_battery_capacity"] = min(results["Storage"]["kw_capacity"], (results["Storage"]["kwh_capacity"]*0.936*0.8) / 4.0) #Discharge efficiency 0.936, min SOC 0.2, event duration = 4 
    d["Home-avg_resilience_hours"] = results["resilience"]["avg_resilience_no_notice"]
    
    d["LCC Breakdown-lcc"] = results["financial"]["LCC"] 
    d["LCC Breakdown-total_capex_and_replacement_cost"] = results["financial"]["net_capital_costs"]
    d["LCC Breakdown-total_om_cost"] = results["financial"]["total_om_cost"]
    # d["LCC Breakdown-total_fuel_cost"] = results["financial"]["total_fuel_cost"]
    d["LCC Breakdown-total_utility_energy_cost"] = results["utility_bill"]["total_utility_energy_cost"]
    d["LCC Breakdown-total_utility_demand_cost"] = results["utility_bill"]["total_utility_demand_cost"]
    d["LCC Breakdown-total_total_utility_fixed_cost"] = results["utility_bill"]["total_utility_fixed_cost"]
    d["LCC Breakdown-total_utility_min_cost_adder_cost"] = results["utility_bill"]["total_utility_min_cost_adder_cost"]
    d["LCC Breakdown-total_utility_coincident_peak_cost"] = results["utility_bill"]["total_utility_coincident_peak_cost"]
    d["LCC Breakdown-total_utility_coincident_peak_cost_bau"] = results["utility_bill"]["total_utility_coincident_peak_cost_bau"]
    d["LCC Breakdown-total_export_benefit"] = results["utility_bill"]["total_export_benefit"]
    #ChangesFromMcKnight: Added additional LCC components
    d["LCC Breakdown-total_production_incentive"] = -results["financial"]["total_production_incentive"]
    d["LCC Breakdown-total_ra_value"] = results["utility_bill"]["total_ra_value"]
    # d["LCC Breakdown-total_production_incentive_benefit"] = results["financial"]["total_production_incentive_benefit"]
    d["LCC Breakdown-total_climate_cost"] = results["emissions"]["total_climate_cost"]
    d["LCC Breakdown-total_health_cost "] = results["emissions"]["total_health_cost"]
    # d["LCC Breakdown-total_resource_adequacy_benefit"] = results["financial"]["total_resource_adequacy_benefit"]
    d["LCC Breakdown-wh_comfort_cost_total"] = results["comfort"]["total_wh_comfort_cost"]
    d["LCC Breakdown-total_hvac_comfort_cost"] = results["comfort"]["total_hvac_comfort_cost"]
    
    
    cf_metrics = cover_factor_metrics(results)
    for key in cf_metrics:
        d[key] = cf_metrics[key]
        
    utility_metrics = calculate_utility_metrics(results, grid_prices)
    for key in utility_metrics:
        d[key] = utility_metrics[key]
    
    return d
#%%
def comparison_metrics(results, baseline, baseline_type = "tech_baseline"):
    """Return metrics which compare REopt results to baseline results.
    
    Parameters
    ----------
    results : dict
        Dictionary of results from extract_results for upgraded system
    baseline : dict
        Dictionary of results from extract_results for baseline system
    baseline_type : str
        Signifies type of baseline for the comparison (such as techs or building upgrades)
        
    """
    d = {}
    d["Financial-additional_capex"] = results["financial"]["initial_capital_costs"] - baseline["financial"]["initial_capital_costs"]
    
    d["Financial-npv"] = baseline["financial"]["LCC"] - results["financial"]["LCC"]
    d["Financial-annual_bill_reduction"] = baseline["utility_bill"]["annual_bill"] - results["utility_bill"]["annual_bill"]
    #ChangesFromMcKnight: Changed assignment from total to year_one
    d["Financial-annual_energy_bill_reduction"] = baseline["utility_bill"]["annual_utility_energy_cost"] - results["utility_bill"]["annual_utility_energy_cost"]
    d["Financial-annual_export_benefits"] = baseline["utility_bill"]["total_export_benefit"] - results["utility_bill"]["total_export_benefit"]
    
    d["Home-load_reduction_kwh"] = sum(baseline["load"]["home_load"]) - sum(results["load"]["home_load"])
    d["External-grid_energy_reductions_kwh"] = baseline["load"]["annual_grid_purchases"] - results["load"]["annual_grid_purchases"]
    
    d["External-annual_emission_reductions_tons"] = baseline["emissions"]["annual_emissions_tons_CO2"] - results["emissions"]["annual_emissions_tons_CO2"]
    d["External-total_emission_reductions_tons"] = baseline["emissions"]["total_emissions_tons_CO2"] - results["emissions"]["total_emissions_tons_CO2"]

    d["Home-comfort_change_dollars"] = sum(baseline["temperature"]["comfort_penalty"]) - sum(results["temperature"]["comfort_penalty"])
    
    d["External-max_grid_purchase_change_kw"] = max(baseline["load"]["grid_purchases_kw"]) - max(results["load"]["grid_purchases_kw"])
    d["Home-change_in_avg_hourly_ra"] = results["ra"]["avg_hourly_ra_reduction"] - baseline["ra"]["avg_hourly_ra_reduction"]
    
    d["Home-increase_in_resilience_hours"] = results["resilience"]["avg_resilience_no_notice"] - baseline["resilience"]["avg_resilience_no_notice"]
    d["baseline_type"] = baseline_type
    return d
#%%
#
def get_reopt_metrics_single_case(results_folder, results_name, baseline_folder, baseline_name, baseline_type, grid_price_path = float("nan")):
    """
    Return dictionary of metrics for single result and single baseline
    
    Parameters
    ----------
    results_folder : str
        Path to results json files.
    results_name : str
        Name of REopt results json.
    baseline_folder : str
        Path to baseline json files.
    baseline_name : str
        Name of REopt baseline json.
    baseline_type : str
        String to identify baseline comparison type.
    grid_price_path : str, optional
        Input of path to grid price series.

    Returns
    -------
    d : dic
        Dictionary of both zero baseline and comparison metrics.

    """
    if not_none(grid_price_path):
        grid_prices = pd.read_csv(grid_price_path).iloc[:,0].tolist()
    else:
        grid_prices = []
    results = extract_results(results_folder, results_name)
    baseline = extract_results(baseline_folder, baseline_name)
    if baseline ["metadata"]["run_failed"] or results["metadata"]["run_failed"]:
        return None
    else:
        d = zero_baseline_metrics(results, grid_prices)
        cbm = comparison_metrics(results, baseline, baseline_type)
        for key in cbm:
            d[key] = cbm[key]
        return d
#%%
def get_timeseries_single_case(results_folder, results_name, timesereies_output_folder, output_file_name = ""):
    """
    Writes csv file of timeseries from REopt results

    Parameters
    ----------
    results_folder : str
        Path to results json files.
    results_name : str
        Name of REopt results json.
    timesereies_output_folder : str
        Path to output folder.
    output_file_name : str, optional
        Name of timeseries output. If "" then use `results_name`.

    """
    results = extract_results(results_folder, results_name)
    
    d = {}

    #ChangesFromMcKnight: Changed the reported timeseries to make plotting dispatch charts easier. These changes are just for convenience for McKnight runs, it's ok to reject these changes
    d["home_load"] = results["load"]["home_load"]
    d["grid_to_load"] = results["load"]["grid_to_load"]
    d["pv_to_load"] = results["load"]["pv_to_load"]
    d["storage_to_load"] = results["Storage"]["storage_to_load"]

    d["pv_to_storage"] = results["Storage"]["pv_to_storage"]
    d["grid_to_storage"] = results["Storage"]["grid_to_storage"]
    
    d["pv_exports"] = results["PV"]["hourly_exports"]
    #d["pv_generation"] = results["PV"]["hourly_generation"]
    
    d["storage_exports"] = results["Storage"]["hourly_exports"]
    #d["storage_discharge"] = results["Storage"]["hourly_generation"]
    #d["storage_charge"] = results["Storage"]["hourly_load"]
    d["storage_state_of_charge"] = results["Storage"]["state_of_charge"]
    #d["grid_purchases"] = results["load"]["grid_purchases_kw"]
    #d["net_load"] = results["load"]["net_load"]

    #ChangesFromMcKnight: Added timeseries for FlexTechAC, FlexTechHP, FlexTechERWH, FlexTechHPWH
    if results["FlexTechAC"]["annual_load"] > 0:
        d["ac_load"] = results["FlexTechAC"]["hourly_load"]
    if results["FlexTechHP"]["annual_load"] > 0:
        d["hp_load"] = results["FlexTechHP"]["hourly_load"]
    if results["FlexTechERWH"]["annual_load"] > 0:
        d["erwh_load"] = results["FlexTechERWH"]["hourly_load"]
    if results["FlexTechHPWH"]["annual_load"] > 0:
        d["hpwh_load"] = results["FlexTechHPWH"]["hourly_load"]
            
    #d["outdoor_temperature_F"] = results["temperature"]["outdoor_air_temp_degF"]
    
    #if results["temperature"]["temperatures_degree_C"][0] is None:
    #    d["indoor_temperature_F"] = [None]*HOURS
    #else:
    #    d["indoor_temperature_F"] = [32 + (9/5) * x for x in results["temperature"]["temperatures_degree_C"]]
    
    
    #d["comfort_penalty"] = results["temperature"]["comfort_penalty"]
    
    #d["energy_costs_per_kwh"] = results["utility_bill"]["energy_costs_per_kwh"]
    #d["demand_cost_per_kw"] = results["utility_bill"]["demand_charge_per_kw"]
    
    if output_file_name == "":
        output_file_name = results_name.replace(".json", "") + "_timeseries.csv"
    
    #TODO add timeseries for FlexTechAC, FlexTechHP, FlexTechERWH, FlexTechHPWH
    #ChangesFromMcKnight:TODO addressed above    
    df = pd.DataFrame(d)
    df.to_csv(os.path.join(timesereies_output_folder, output_file_name), index=False)  

#%%
#ChangesFromMcKnight: Cut and pasted this function from below to maintain call order
def generate_timeseries(reopt_results_folder, timeseries_output_folder):
    paths = [f for f in glob.iglob(os.path.join(reopt_results_folder, "**"), recursive=True) if os.path.isfile(f) and f.endswith(".json")]
    
    for path in paths:
        path_dir, file_name = os.path.split(path)
        relative_dir = os.path.relpath(path_dir, reopt_results_folder)
        output_folder = os.path.join(timeseries_output_folder, relative_dir)
        Path(output_folder).mkdir(parents=True, exist_ok=True)
        
        output_file_name = file_name.replace(".json", "_timeseries.csv")
        
        get_timeseries_single_case(path_dir, file_name, output_folder, output_file_name)
#%%
def generate_metrics(reopt_results_folder, inputs, metrics_folder, metrics_results_file_name, wholesale_price_folder = "./", by_building = False):
    """
    Write an Excel sheet of metrics, with rows for each results--baseline pair.

    Parameters
    ----------
    reopt_results_folder : str
        path to main folder of REopt results jsons (main folder can have subfolders).
    inputs : pandas dataframe
        Pandas DataFrame produces from loading Inputs.xlsx Generate Metrics sheet.
    metrics_folder : str
        Folder to save metrics results to.
    metrics_results_file_name : str
        Name of Metrics outputs file. Needs .xlsx extension
    wholesale_price_folder : str, optional
        Path to wholesale prices. Defaults to './'.

    """
    Path(metrics_folder).mkdir(parents=True, exist_ok=True)
    metrics_results_list = []
    for i in range(len(inputs)):
        if "baseline_type" in inputs and not_none(inputs["baseline_type"][i]):
            baseline_type = inputs["baseline_type"][i]
        else:
            baseline_type = ""
        if "wholesale_price_path" in inputs and not_none(inputs["wholesale_price_path"][i]):
            wholesale_price_path = os.path.join(wholesale_price_folder, inputs["wholesale_price_path"][i])
        else:
            wholesale_price_path = float("nan")
                
        if by_building:
            building_folders = os.listdir(reopt_results_folder)
            for building in building_folders:
                metrics_results_list.append(get_reopt_metrics_single_case(building, inputs["results_name"][i]+".json", building, inputs["baseline_name"][i]+".json", baseline_type, wholesale_price_path))
        
        else:
            if "results_folder" in inputs and not_none(inputs["results_folder"][i]):
                results_subfolder = os.path.join(reopt_results_folder, inputs["results_folder"][i])
            else:
                results_subfolder = reopt_results_folder
                
            if "baseline_folder" in inputs and not_none(inputs["baseline_folder"][i]):
                baseline_subfolder = os.path.join(reopt_results_folder, inputs["baseline_folder"][i])
            else:
                baseline_subfolder = reopt_results_folder

            metrics_results_list.append(get_reopt_metrics_single_case(results_subfolder, inputs["results_name"][i]+".json", baseline_subfolder, inputs["baseline_name"][i]+".json", baseline_type, wholesale_price_path))
        
    metrics = pd.DataFrame(list(filter(None, metrics_results_list)))
    filenames = metrics["filename"].tolist()
    metrics.drop("filename", axis = 1, inplace = True) 
    baseline_type = metrics["baseline_type"].tolist()
    metrics.drop("baseline_type", axis = 1, inplace = True) 
    
    sheet = [name.split("-")[0] for name in metrics]
    unique_sheets = list(set(sheet))
    
    d = {}
    for b in unique_sheets:
        columns = [x for i, x in enumerate(metrics) if sheet[i] == b]
        df = metrics[columns]
        df.columns = [col.split("-")[1] for col in columns]
        df.insert(loc=0, column='filenames', value= filenames)
        df.insert(loc=1, column='baseline_type', value= baseline_type)
        d[b] = df
    ##
    with pd.ExcelWriter(os.path.join(metrics_folder, metrics_results_file_name)) as writer:
        for sheet_name in ["Run Type", "Financial", "LCC Breakdown", "Home", "External", "PV", "Storage", "HP", "ERWH"]:
            d[sheet_name].to_excel(writer, sheet_name = sheet_name, index = False)
    #ChangesFromMcKnight: Added function call
    timeseries_output_folder = os.path.join(metrics_folder, "TimeSeries")
    generate_timeseries(reopt_results_folder, timeseries_output_folder)

