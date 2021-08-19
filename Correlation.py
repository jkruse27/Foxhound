import os.path
import pandas as pd
import numpy as np
import scipy as sp
import scipy.signal as sig
from datetime import *

class Correlations():

    def __init__(self, filename, date_name='datetime'):
        self.dataset = pd.read_csv(filename)
        self.dataset[date_name] = pd.to_datetime(self.dataset[date_name], format="%d.%m.%y %H:%M")
        self.dataset.set_index(date_name, inplace=True)

    def set_dataset(self,filename):
        self.dataset = pd.read_csv(filename)

    def get_columns(self, regex='.*'):
        return self.dataset.filter(regex=regex).columns

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
        corrs = [correlations[col].iloc[delays[pos]] for pos, col in enumerate(correlations)]
        
        delays = [delay-int(x.size*margin) for delay in delays]

        return delays, corrs, y.columns

    def lagged_corr(self, x, y, lag):
        return (y.shift(lag)[x.index[0]:x.index[-1]]).corrwith(x)

    def get_fs(self, names):
        return [(self.dataset[col].index[-1]-self.dataset[col].index[0])/self.dataset[col].size
                for col in names]

    def find_delays(self, x, y):
        return y.apply(lambda k: sig.correlate(k,x,mode='valid')).apply(lambda k: k.abs().idxmax()-int(len(k/2))+1)

    def to_date(self, delays, names):
        return [str(fs*d) for d, fs in zip(delays,self.get_fs(names))]

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

