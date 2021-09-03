import os.path
import pandas as pd
import numpy as np
import scipy as sp
import scipy.signal as sig

class Correlator():

    @staticmethod
    def correlate(x, y, margin):
        y = Correlator.interpolate(y,x.index,margin)
        correlations = pd.DataFrame([Correlator.lagged_corr(x,y,lag) for lag in range(-1*int(x.size*margin),int(x.size*margin)+1)], columns=y.columns)
        delays = [correlations[col].abs().idxmax() for col in correlations]
        corrs = [round(correlations[col].iloc[delays[pos]],2) for pos, col in enumerate(correlations)]
        
        return corrs, delays
    
    '''
    @staticmethod
    def correlate(x, y, margin):
        y = Correlator.interpolate(y,x.index,margin)
        delays = y.apply(lambda k: abs(sig.correlate(k, x, mode='valid'))).idxmax()-int(margin*x.size)
        
        new_y = [((y[col]).shift(delays.loc[col], fill_value=0))[x.index.min():x.index.max()] for col in y.columns]

        print(new_y)

        correlations = pd.DataFrame([Correlator.lagged_corr(x,y,lag) for lag in range(-1*int(x.size*margin),int(x.size*margin)+1)], columns=y.columns)
        delays = [correlations[col].abs().idxmax() for col in correlations]
        corrs = [round(correlations[col].iloc[delays[pos]],2) for pos, col in enumerate(correlations)]
        
        return corrs, delays
    '''

    @staticmethod
    def lagged_corr(x, y, lag):
        return (y.shift(lag)[x.index[0]:x.index[-1]]).corrwith(x)

    @staticmethod
    def find_delays(x, y):
        return y.apply(lambda k: sig.correlate(k,x,mode='valid')).apply(lambda k: k.abs().idxmax()-int(len(k/2))+1)

    @staticmethod 
    def find_correlation(self, x, y):
        return y.corrwith(x)

    @staticmethod
    def interpolate(x, idx, margin):
        fs = pd.infer_freq(idx)
        T  = int(len(idx)*margin)
        prev = pd.date_range(end=idx.min(),freq=fs, periods=T).union(idx)
        post = pd.date_range(start=idx.max(),freq=fs, periods=T).union(prev)

        new_x = x.reindex(x.index.union(post))
        return new_x.interpolate(method='linear').loc[post]
