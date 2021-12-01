import matplotlib as plt
import numpy as np

#***NOTE*** This code is in development and is not yet functioning
#%%
def plot_temperatures(temperatures1, temperatures2, title1='OCHRE hot water outlet temperature', 
                      title2='REopt hot water tank temperature', ylabel='Temperature [Celsius]',
                      xlabel='Timestep', n_timestep=8760):

    x_axis = np.linspace(1,n_timestep,n_timestep)
    fig, ax = plt.subplots()
    plt.subplot(2,1,1)
    plt.plot(x_axis, temperatures1)
    plt.title(title1)
    plt.ylabel(ylabel)
    plt.grid(True)
    
    plt.subplot(2,1,2)
    plt.plot(x_axis, temperatures2)
    plt.plot([1, 8760], [23.3, 23.3], c='b')
    plt.plot([1, 8760], [25, 25], c='r')
    plt.title(title2)
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    plt.grid(True)

    plt.tight_layout()
    plt.show()        
    
    
def plot_energy_comparison(plt1_series, plt2_series, plt1_series_labels=['OCHRE', 'REopt'], plt2_series_labels=['OCHRE', 'REopt'],
                           title1='Delivered', title2='Consumption', ylabel='Monthly Energy Use [kWh]', xlabel='Month', n_timesteps=12):

    x_axis = np.linspace(1,n_timesteps,n_timesteps)
    fig, ax = plt.subplots()
    plt.subplot(2,1,1)
    for idx, series in enumerate(plt1_series):
        plt.plot(x_axis, series, label=plt1_series_labels[idx])
    plt.title(title1)
    plt.legend()
    plt.ylabel(ylabel)

    plt.subplot(2,1,2)
    for idx, series in enumerate(plt2_series):
        plt.plot(x_axis, series, label=plt2_series_labels[idx])
        
    plt.title(title2)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend()
    plt.tight_layout()
    plt.show()
    
    
def plot_timeseries(x_axis, plt_series, titles=None, plt_series_labels=None, ylabel='Monthly Energy Use [kWh]', 
                    xlabel='Month', x=8, y=8, drawlines=False, xlim=None, savefig_path=None):

    n_subplots = len(plt_series)
    fig, ax = plt.subplots(figsize=(x, y))
#    x_axis = pd.date_range("1/1/2019 00:00", periods=8760, freq="1H") #np.linspace(1, n_timesteps, n_timesteps)
    for i, series in enumerate(plt_series):
        plt.subplot(n_subplots,1,i+1)
        for j, vals in enumerate(series):
            if plt_series_labels is not None:
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