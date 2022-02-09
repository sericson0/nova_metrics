import os
import json
import pickle
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd 
from datetime import datetime
import math
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter

def load_post(path, filename):
    # Load a json into a python dictionary
    with open(os.path.join(path, filename), 'r') as fp:
        post = json.load(fp)
    return post


def save_post(post, path, filename):
    with open(os.path.join(path, filename), 'w') as fp:
        json.dump(post, fp)


def save_api_results(api_response, path, filename):
    with open(os.path.join(path, filename + '.pickle'), 'wb') as handle:
        pickle.dump(api_response, handle, protocol=pickle.HIGHEST_PROTOCOL)
      
    
def load_api_results(path, filename):
    with open(os.path.join(path, filename + '.pickle'), 'rb') as handle:
        api_response = pickle.load(handle)
    return api_response


def get_relevant_fields(post, year=2019):
    ts=pd.date_range('1/1/'+str(year)+' 00:00', periods=8760, freq="1H")
    df = pd.DataFrame(index=ts)
    df['misc_load']=post['outputs']['Scenario']['Site']['LoadProfile']['year_one_electric_load_series_kw']
    df['pv_generation']=post['outputs']['Scenario']['Site']['PV']['year_one_power_production_series_kw']
    df['pv_to_load']=post['outputs']['Scenario']['Site']['PV']['year_one_to_load_series_kw']
    df['pv_to_batt']=post['outputs']['Scenario']['Site']['PV']['year_one_to_battery_series_kw']
    df['grid_to_load']=post['outputs']['Scenario']['Site']['ElectricTariff']['year_one_to_load_series_kw']
    df['grid_to_batt']=post['outputs']['Scenario']['Site']['ElectricTariff']['year_one_to_battery_series_kw']
    df['batt_to_load']=post['outputs']['Scenario']['Site']['Storage']['year_one_to_load_series_kw']
    df['batt_to_grid']=post['outputs']['Scenario']['Site']['Storage']['year_one_to_grid_series_kw']
    df['ac_consumption']=post['outputs']['Scenario']['Site']['FlexTechAC']['year_one_power_consumption_series_kw']
    df['hp_consumption']=post['outputs']['Scenario']['Site']['FlexTechHP']['year_one_power_consumption_series_kw']
    
    hpwh = post['outputs']['Scenario']['Site']['FlexTechHPWH']['year_one_power_consumption_series_kw']
    erwh = post['outputs']['Scenario']['Site']['FlexTechERWH']['year_one_power_consumption_series_kw']
    
    df['dhw_consumption']=[i[0]+i[1] for i in zip(hpwh, erwh)]
    df['indoor_temperature']=post['outputs']['Scenario']['Site']['RC']['temperatures_degree_C']
    df['full_load']=df['misc_load']+df['ac_consumption']+df['hp_consumption']+df['dhw_consumption']
    return df


def plot_stacked_area(x_axis, stacked_series, stacked_series_labels, line_series=None, line_series_labels=None, line_styles=None, 
                      line_colors=None, line_series_ax2=None, line_series_ax2_labels=None, title=None, xlim=None, x=10, y=4):
    
    fig, ax1 = plt.subplots(figsize=(x, y))
    ax1.stackplot(x_axis, stacked_series, labels=stacked_series_labels)

    if line_series is not None:
        for idx, val in enumerate(line_series):
            if line_styles is None:
                ax1.plot(x_axis, val, label=line_series_labels[idx], linewidth=1.5)
            elif line_colors is None:
                ax1.plot(x_axis, val, line_styles[idx], label=line_series_labels[idx], linewidth=1.5)
            else:
                ax1.plot(x_axis, val, line_styles[idx], label=line_series_labels[idx], linewidth=1.5, color=line_colors[idx])

    box = ax1.get_position()
    ax1.set_position([box.x0, box.y0, box.width * 0.75, box.height])
    ax1.legend(loc='center left', bbox_to_anchor=(1.08, 0.8))
    
    if line_series_ax2 is not None:     
        ax2 = ax1.twinx()
        for idx, val in enumerate(line_series_ax2):
            ax2.plot(x_axis, val, '--', label=line_series_ax2_labels[idx])
        ax2.set_position([box.x0, box.y0, box.width * 0.75, box.height])  
        ax2.legend(loc='center left', bbox_to_anchor=(1.08, 0.1))

    if xlim is not None:
        plt.xlim(xlim)

    ax1.set_xlabel('Time')
    ax1.set_ylabel('Power [kW]')
    ax1.set_title('{}'.format(title))
    ax1.grid(False)  # ax1.grid(True) 

    # Define the date format
    date_form = DateFormatter("%m-%d")
    ax1.xaxis.set_major_formatter(date_form)

    plt.show()
    

def plot_avg_daily_profile(lots, sonnen_data, single_reopt, key='battery', rows=3,cols=2,x=9,y=10):
    
    fig, axes = plt.subplots(rows,cols,figsize=(x,y))
    
    single_reopt = single_reopt.values.reshape(int(8760/24),24).T
    y2 = np.mean(single_reopt, axis=1)
    sd2 = np.std(single_reopt, axis=1)
    cis2 = (y2 - sd2, y2 + sd2)
    
    for idx, lot in enumerate(lots):
        single_batt_sonnen = sonnen_data[[key+'_'+str(lot)]].values.reshape(int(4416/24),24).T

        x=range(24)
        y1 = np.mean(single_batt_sonnen, axis=1)
        sd1 = np.std(single_batt_sonnen, axis=1)
        cis1 = (y1 - sd1, y1 + sd1)

        if len(lots) == 1:
            axes.fill_between(x,cis1[0],cis1[1],alpha=0.2)
            axes.fill_between(x,cis2[0],cis2[1],alpha=0.2)
            axes.plot(x,y1, label='Sonnen')
            axes.plot(x,y2, label='REopt')
            axes.set_title(key+'_'+str(lot))
            axes.set_xlabel('Time')
            axes.set_ylabel('Power [kW]')
            axes.margins(x=0, y=0)
            axes.legend()
            axes.axvspan(15, 20, facecolor='red', alpha=0.05)  
            axes.grid()
        else:
            if idx < 3:
                i = idx
                j = 0
            else:
                i = idx - 3
                j = 1
                
            axes[i, j].fill_between(x,cis1[0],cis1[1],alpha=0.2)
            axes[i, j].fill_between(x,cis2[0],cis2[1],alpha=0.2)
            axes[i, j].plot(x,y1, label='Sonnen')
            axes[i, j].plot(x,y2, label='REopt')
            axes[i, j].set_title(key+'_'+str(lot))
            axes[i, j].set_xlabel('Time')
            axes[i, j].set_ylabel('Power [kW]')
            axes[i, j].margins(x=0, y=0)
            axes[i, j].legend()
            axes[i, j].axvspan(15, 20, facecolor='red', alpha=0.05)  
            axes[i, j].grid()
            
    plt.tight_layout()
    
    
def plot_timeseries(x_axis, plt_series, titles=None, plt_series_labels=None, ylabel='Monthly Energy Use [kWh]', 
                    xlabel='Month', x=8, y=8, drawlines=False, xlim=None, savefig_path=None):

    n_subplots = len(plt_series)
    fig, ax = plt.subplots(figsize=(x, y))
        
#    x_axis = pd.date_range("1/1/2019 00:00", periods=8760, freq="1H") #np.linspace(1, n_timesteps, n_timesteps)
    for i, series in enumerate(plt_series):
        plt.subplot(n_subplots,1,i+1)
        for j, vals in enumerate(series):
            if plt_series_labels is not None:
                print(i)
                print(j)
                print(plt_series_labels[i][j])
                plt.plot(x_axis, vals, label=plt_series_labels[i][j])
                
            else:
                plt.plot(x_axis, vals)
                if i == 2 and drawlines == True:
                    plt.plot(x_axis, [23.3]*len(x_axis), c='b')
                    plt.plot(x_axis, [25]*len(x_axis), c='r')
        if xlim is not None:
            plt.xlim(xlim)
        if titles is not None:
            plt.title(titles[i])
        if plt_series_labels is not None:
            plt.legend()
        plt.ylabel(ylabel)
        plt.grid(True)
        
            
#    if xticklabels is not None:
#        ax.set_xticklabels(xticklabels)

    plt.xlabel(xlabel)
    plt.tight_layout()
    plt.show()
    
    if savefig_path is not None:
        plt.savefig(savefig_path)
        

def calc_capex_with_replacement(discount_rate, analysis_period, asset_life, asset_cost):
    n_replacements = math.ceil(analysis_period / asset_life) - 1
    
    replacement_years = []
    replacement_cost = []
    for i in range(n_replacements): 
        replacement_year = asset_life * (i + 1)    
        replacement_years.append(replacement_year)
        replacement_cost.append(asset_cost * (1+discount_rate)**(-1*replacement_year))
    
    salvage_value = 0 
    if analysis_period % asset_life != 0:
        salvage_years = asset_life - (analysis_period - max(replacement_years))
        salvage_value = (salvage_years/asset_life) * asset_cost * ((1 + discount_rate)**(-1*analysis_period))
        
    capital_cost = asset_cost + sum(replacement_cost) - salvage_value
    return capital_cost
        
        
def get_escalated_npv(cost, cost_escalation_rate, discount_rate, analysis_period):
    esc = []
    esc.append(0)
    esc.append(cost*(1+cost_escalation_rate))
    for i in range(analysis_period-1):
        esc.append(esc[i+1]*(1+cost_escalation_rate))
        
    return np.npv(discount_rate, esc)        