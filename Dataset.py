import os.path
import pandas as pd
import numpy as np
import scipy as sp
import scipy.signal as sig
import asyncio
from Correlator import *
from datetime import *
from EPICS_Requests import *

class Dataset():

    def __init__(self, filename=None, date_name='datetime'):
        if(filename == None):
            self.EPICS = True
            self.epics_req = EPICS_Requests()

        else:
            self.EPICS = False
            self.dataset = pd.read_csv(filename)
            self.dataset[date_name] = pd.to_datetime(self.dataset[date_name], format="%d.%m.%y %H:%M")
            self.dataset.set_index(date_name, inplace=True)

        self.loop = asyncio.get_event_loop()

    def number_of_vars(self, regex):
        return len(self.epics_req.get_names(regex=regex, limit=-1))

    def get_EPICS_pv(self, name, start_time=None, end_time=None):
        return self.correct_datetime(self.loop.run_until_complete(self.epics_req.call_fetch(name,start_time,end_time)))

    def update_pv_names(self, regex=None, limit=100):
        self.dataset = pd.DataFrame(columns=self.epics_req.get_names(regex=regex, limit=limit))

    def set_dataset(self,filename):
        self.dataset = pd.read_csv(filename)

    def get_columns(self, regex='.*'):
        return self.dataset.filter(regex=regex).columns

    def correct_datetime(self, x):
        x.index = pd.to_datetime(x.index, format="%d.%m.%y %H:%M")
        return x

    def correlate_EPICS(self, x_label, regex, begin=None, end=None, margin=0.2, method='Pearson'):
        x = self.get_EPICS_pv([x_label], begin, end)
        x = x[x.columns[0]]

        dt = end-begin
        
        pvs = self.epics_req.get_names(regex=regex, limit=-1)
        y = self.get_EPICS_pv(pvs, begin-margin*dt, end+margin*dt)

        self.dataset = y

        corrs, delays = Correlator.correlate(x,y,margin, method.lower())
        
        #delays = [delay-int(x.size*margin) for delay in delays]

        return delays, corrs, y.columns

    def correlate(self, x_label, begin=None, end=None, margin=0.2, method='Pearson'):
        if(begin==None):
            begin = self.dataset.index[0]
        if(end==None):
            end = self.dataset.index[-1]

        dt = end-begin
        
        x = self.dataset[x_label][begin:end]
        y = self.dataset.drop(x_label,axis=1)[begin-margin*dt:end+margin*dt]

        corrs, delays = Correlator.correlate(x,y,margin, method.lower())
        #delays = [delay-int(x.size*margin) for delay in delays]

        return delays, corrs, y.columns

    def get_fs(self, names):
        return [(self.dataset[col].index[-1]-self.dataset[col].index[0])/self.dataset[col].size
                for col in names]

    def to_date(self, delays, names):
        return [str(round((fs*d).days*24+(fs*d).seconds/3600,3))+"h" for d, fs in zip(delays,self.get_fs(names))]

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

