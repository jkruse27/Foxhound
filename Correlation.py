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

    def correlate(self, x_label, y_labels):
        x = self.dataset[x_label]
        y = self.dataset[y_labels]

        delays = self.find_delays(x,y) 
        corrs = self.find_correlation(x,self.shift(y,delays))

        return delays, corrs

    def find_delays(self, x, y):
        return y.apply(lambda k: sig.correlate(k,x)).idxmax().apply(lambda k: x.size-k-1)

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

