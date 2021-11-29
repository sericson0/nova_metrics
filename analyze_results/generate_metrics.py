# import os 
# os.chdir(os.path.dirname(__file__))
from pathlib import Path    
import os
import glob
import numpy as np
import pandas as pd
pd.set_option('mode.chained_assignment', None)
import openpyxl
from nova_metrics.analyze_results.extract_results import extract_results
HOURS = 8760
#%%
def cover_factor_metrics(results):
    #Cover factor demand is fraction of demand covered by renewable energy
    #Cover factor supply is fraction of PV generation consumed onsite
    d = {}
    d["Home-cover_factor_demand"] = 1 - (results["load"]["annual_grid_purchases"]/sum(results["load"]["home_load"]))
    
    if results["PV"]["kw_capacity"] == 0:
        d["Home-cover_factor_supply"] = 0
    else:
        d["Home-cover_factor_supply"] = 1 - (results["PV"]["annual_exports"]/results["PV"]["annual_generation"]) 
    return d
#%%
def calculate_utility_metrics(results, grid_prices = []):
    #Add grid prices to return wholesale grid utility metrics
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
    
        #Cover Factor Demand is Generation Consumed by building / Building Gross load
    
        d["External-average_grid_cost_dollars_per_kwh"] = sum([results["load"]["net_load"][h]*grid_prices[h]/1000 for h in range(HOURS)])/sum(results["load"]["home_load"])
        return d
#%%
    
def zero_baseline_metrics(results, grid_prices = []):
    #Zero baseline metrics are all values which do not need a comparison to other results for baselining 
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
    
    d["Home-annual_comfort_penalty"] = sum(results["temperature"]["comfort_penalty"])
    
    d["Financial-lcc"] = results["financial"]["LCC"] 
    d["Financial-net_capital_costs"] = results["financial"]["net_capital_costs"]
    d["Financial-initial_capital_costs"] = results["financial"]["initial_capital_costs"]
    
    d["Home-annual_net_load"] = sum(results["load"]["net_load"]) 
    d["Home-annual_home_load"] = sum(results["load"]["home_load"]) 
    
    d["External-annual_grid_purchases_kwh"] = results["load"]["annual_grid_purchases"] 
    
    d["Financial-annual_bill"] = results["utility_bill"]["annual_bill"]
    d["Financial-annual_energy_bill"] = results["utility_bill"]["energy"]
    d["Financial-annual_demand_charges"] = results["utility_bill"]["demand_charges"]
    
    d["External-annual_emissions_lb_CO2"] = results["emissions"]["annual_emissions_lb_CO2"]
    d["External-avg_emissions_rate_lb_CO2_per_kwh"] = results["emissions"]["annual_emissions_lb_CO2"]/d["Home-annual_home_load"]
    
    d["Home-ra_battery_capacity"] = min(results["Storage"]["kw_capacity"], (results["Storage"]["kwh_capacity"]*0.936*0.8) / 4.0) #Discharge efficiency 0.936, min SOC 0.2, event duration = 4 
    d["Home-avg_resilience_hours"] = results["resilience"]["avg_resilience_no_notice"]
    
    cf_metrics = cover_factor_metrics(results)
    for key in cf_metrics:
        d[key] = cf_metrics[key]
        
    utility_metrics = calculate_utility_metrics(results, grid_prices)
    for key in utility_metrics:
        d[key] = utility_metrics[key]
    
    return d
#%%
def comparison_metrics(results, baseline, baseline_type = "tech_baseline"):
    #Returns variety of metrics. Inputs include
    #results from extract_results
    #baseline results from baseline run extract results
    #baseline_type: is tag to mark type of baseline. tech_baseline is same building but different technologies. building_baseline is same tech but different buildings
    d = {}
    #TODO Check what initial vs net capital costs are
    d["Financial-additional_capex"] = results["financial"]["initial_capital_costs"] - baseline["financial"]["initial_capital_costs"]
    
    d["Financial-npv"] = baseline["financial"]["LCC"] - results["financial"]["LCC"]
    d["Financial-annual_bill_reduction"] = baseline["utility_bill"]["annual_bill"] - results["utility_bill"]["annual_bill"]
    d["Financial-annual_energy_bill_reduction"] = baseline["utility_bill"]["energy"] - results["utility_bill"]["energy"]
    d["Financial-annual_export_benefits"] = baseline["utility_bill"]["export_benefits"] - results["utility_bill"]["export_benefits"]
    
    d["Home-load_reduction_kwh"] = sum(baseline["load"]["home_load"]) - sum(results["load"]["home_load"])
    d["External-grid_energy_reductions_kwh"] = baseline["load"]["annual_grid_purchases"] - results["load"]["annual_grid_purchases"]
    
    d["External-emission_reductions"] = baseline["emissions"]["annual_emissions_lb_CO2"] - results["emissions"]["annual_emissions_lb_CO2"]
    
    d["Home-comfort_change"] = sum(baseline["temperature"]["comfort_penalty"]) - sum(results["temperature"]["comfort_penalty"])
    
    d["External-max_grid_purchase_change_kw"] = max(baseline["load"]["grid_purchases_kw"]) - max(results["load"]["grid_purchases_kw"])
    d["Home-change_in_avg_hourly_ra"] = results["ra"]["avg_hourly_ra_reduction"] - baseline["ra"]["avg_hourly_ra_reduction"]
    
    d["Home-increase_in_resilience_hours"] = results["resilience"]["avg_resilience_no_notice"] - baseline["resilience"]["avg_resilience_no_notice"]
    d["baseline_type"] = baseline_type
    return d
#%%
#Creates metrics for single result and single baseline
def get_reopt_metrics_single_case(results_folder, results_name, baseline_folder, baseline_name, baseline_type, grid_price_path):
    if grid_price_path != grid_price_path:
        grid_prices = []
    else:
        grid_prices = pd.read_csv(grid_price_path).iloc[:,0].tolist()
    # print(results_name, baseline_name)
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
    # if grid_price_path != grid_price_path:
    #     grid_prices = []
    # else:
    #     grid_prices = pd.read_csv(grid_price_path)[0].tolist()
        
    results = extract_results(results_folder, results_name)
    d = {}
    d["pv_exports"] = results["PV"]["hourly_exports"]
    d["pv_generation"] = results["PV"]["hourly_generation"]
    
    d["storage_exports"] = results["Storage"]["hourly_exports"]
    d["storage_discharge"] = results["Storage"]["hourly_generation"]
    d["storage_charge"] = results["Storage"]["hourly_load"]
    d["storage_state_of_charge"] = results["Storage"]["state_of_charge"]
    d["home_load"] = results["load"]["home_load"]
    d["grid_purchases"] = results["load"]["grid_purchases_kw"]
    d["net_load"] = results["load"]["net_load"]
    
    d["outdoor_temperature_F"] = results["temperature"]["outdoor_air_temp_degF"]
    
    if results["temperature"]["temperatures_degree_C"][0] is None:
        d["indoor_temperature_F"] = [None]*HOURS
    else:
        d["indoor_temperature_F"] = [32 + (9/5) * x for x in results["temperature"]["temperatures_degree_C"]]
    
    
    d["comfort_penalty"] = results["temperature"]["comfort_penalty"]
    
    d["energy_costs_per_kwh"] = results["utility_bill"]["energy_costs_per_kwh"]
    d["emand_cost_per_kw"] = results["utility_bill"]["demand_charge_per_kw"]
    
    # if len(grid_prices) > 0:
    #     d["wholesale_grid_prices"] = grid_prices
    
    if output_file_name == "":
        output_file_name = results_name.replace(".json", "") + "_timeseries.csv"
    
    #TODO add timeseries for FlexTechAC, FlexTechHP, FlexTechERWH, FlexTechHPWH    
    df = pd.DataFrame(d)
    df.to_csv(os.path.join(timesereies_output_folder, output_file_name), index=False)  
#%%
def generate_metrics(reopt_results_folder, inputs, metrics_folder, metrics_results_file_name, wholesale_price_folder):
    Path(metrics_folder).mkdir(parents=True, exist_ok=True)
    # inputs = pd.read_excel(input_excel_file_path, sheet_name='Generate Metrics')
    # inputs = pd.read_csv(input_csv_file_path)
    
    metrics = pd.DataFrame(list(filter(None, [get_reopt_metrics_single_case(os.path.join(reopt_results_folder, inputs["results_folder"][i]), inputs["results_name"][i]+".json", 
                                                                            os.path.join(reopt_results_folder, inputs["baseline_folder"][i]), inputs["baseline_name"][i]+".json", 
                                                                            inputs["baseline_type"][i], os.path.join(wholesale_price_folder, inputs["wholesale_price_path"][i])) for i in range(len(inputs))])))
    filenames = metrics["filename"].tolist()
    metrics.drop("filename", axis = 1, inplace = True) 
    baseline_type = metrics["baseline_type"].tolist()
    metrics.drop("baseline_type", axis = 1, inplace = True) 
    
    sheet = [name.split("-")[0] for name in metrics]
    unique_sheets = list(set(sheet))
    # col_name = [name.split("-")[1] for name in metrics]
    
    # metrics.columns = col_name
    
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
        # for sheet_name, df_vals in d.items():
        for sheet_name in ["Run Type", "Financial", "Home", "External", "PV", "Storage", "HP", "ERWH"]:
            d[sheet_name].to_excel(writer, sheet_name = sheet_name, index = False)
#%%
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
# main_folder = "../../../Metrics at Home/Example Format"

# vt_wholesale_prices = pd.read_csv(os.path.join(main_folder, "VT Hourly Prices.csv"))
# vt_price_vector = vt_wholesale_prices["RT_LMP"].tolist()


# inputs = pd.read_csv(os.path.join(main_folder, "Input values.csv"))
# create_reopt_results(main_folder, os.path.join(main_folder, "Input values.csv"), os.path.join(main_folder, "Metrics Results.csv"), grid_prices = vt_price_vector)
# a = pd.read("../../Metrics at Home/Example Building")

# # main_folder = "../../../Metrics at Home/Example Format"

# generate_timeseries(os.path.join(main_folder, "REopt Outputs"), os.path.join(main_folder, "Timeseries Outputs"), grid_prices = vt_price_vector)

