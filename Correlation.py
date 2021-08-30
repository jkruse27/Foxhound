import os.path
import pandas as pd
import numpy as np
import scipy as sp
import scipy.signal as sig
from datetime import *
from EPICS_Requests import *

class Correlations():

    def __init__(self, filename=None, date_name='datetime'):
        if(filename == None):
            self.EPICS = True
            self.epics_req = EPICS_Requests()

        else:
            self.EPICS = False
            self.dataset = pd.read_csv(filename)
            self.dataset[date_name] = pd.to_datetime(self.dataset[date_name], format="%d.%m.%y %H:%M")
            self.dataset.set_index(date_name, inplace=True)

        self.is_name_done = False
        self.is_pvs_done = False

    def get_names_ready(self):
        if(self.is_name_done):
            self.is_name_done = False
            return True
        else:
            return False

    def number_of_vars(self, regex):
        return len(self.epics_req.get_names(regex=regex, limit=-1))

    def get_EPICS_pv(self, name, start_time=None, end_time=None):
        return self.correct_datetime(self.epics_req.get_pv(name,start_time,end_time))

    def update_pv_names(self, regex=None, limit=100):
        self.dataset = pd.DataFrame(columns=self.epics_req.get_names(regex=regex, limit=limit))
        self.is_name_done = True

    def set_dataset(self,filename):
        self.dataset = pd.read_csv(filename)

    def get_columns(self, regex='.*'):
        return self.dataset.filter(regex=regex).columns

    def correct_datetime(self, x):
        x.index = pd.to_datetime(x.index, format="%d.%m.%y %H:%M")
        return x


    def correlate_EPICS(self, x_label, regex, begin=None, end=None, margin=0.2):
        x = self.get_EPICS_pv([x_label], begin, end)

        dt = end-begin
        
        pvs = self.epics_req.get_names(regex=regex, limit=-1)
        y = self.get_EPICS_pv(pvs, begin-margin*dt, end+margin*dt)

        self.dataset = y

        correlations = pd.DataFrame([self.lagged_corr(x,y,lag) for lag in range(-1*int(x.size*margin),int(x.size*margin)+1)], columns=y.columns)
        delays = [correlations[col].abs().idxmax() for col in correlations]
        corrs = [round(correlations[col].iloc[delays[pos]],2) for pos, col in enumerate(correlations)]
        
        delays = [delay-int(x.size*margin) for delay in delays]

        return delays, corrs, y.columns

    def correlate(self, x_label, begin=None, end=None, margin=0.2):
        if(begin==None):
            begin = self.dataset.index[0]
        if(end==None):
            end = self.dataset.index[-1]

        dt = end-begin
        
        x = self.dataset[x_label][begin:end]
        y = self.dataset.drop(x_label,axis=1)[begin-margin*dt:end+margin*dt]

        correlations = pd.DataFrame([self.lagged_corr(x,y,lag) for lag in range(-1*int(x.size*margin),int(x.size*margin)+1)], columns=y.columns)
        delays = [correlations[col].abs().idxmax() for col in correlations]
        corrs = [round(correlations[col].iloc[delays[pos]],2) for pos, col in enumerate(correlations)]
        
        delays = [delay-int(x.size*margin) for delay in delays]

        return delays, corrs, y.columns

    def lagged_corr(self, x, y, lag):
        return (y.shift(lag)[x.index[0]:x.index[-1]]).corrwith(x[x.columns[0]])

    def get_fs(self, names):
        return [(self.dataset[col].index[-1]-self.dataset[col].index[0])/self.dataset[col].size
                for col in names]

    def find_delays(self, x, y):
        return y.apply(lambda k: sig.correlate(k,x,mode='valid')).apply(lambda k: k.abs().idxmax()-int(len(k/2))+1)

    def to_date(self, delays, names):
        return [str(round((fs*d).days*24+(fs*d).seconds/3600,3))+"h" for d, fs in zip(delays,self.get_fs(names))]

    def find_correlation(self, x, y):
        return y.corrwith(x)

    def shift(self, x, delays):
        for col in x:
            x[col] = x[col].shift(delays.loc[col], fill_value=0)
        return x

    def get_series(self, series_name, begin=None, end=None):

        if(begin==None):
            begin = self.dataset.index[0]
        if(end==None):
            end = self.dataset.index[-1]

        series = self.dataset[series_name]

        return series.loc[(series.index>=begin) & (series.index<=end)]

