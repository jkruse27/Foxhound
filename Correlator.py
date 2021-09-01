import os.path
import pandas as pd
import numpy as np
import scipy as sp
import scipy.signal as sig

class Correlator():

    @staticmethod
    def correlate(x, y, margin):
        correlations = pd.DataFrame([Correlator.lagged_corr(x,y,lag) for lag in range(-1*int(x.size*margin),int(x.size*margin)+1)], columns=y.columns)
        delays = [correlations[col].abs().idxmax() for col in correlations]
        corrs = [round(correlations[col].iloc[delays[pos]],2) for pos, col in enumerate(correlations)]
        
        return corrs, delays

    @staticmethod
    def lagged_corr(x, y, lag):
        return (y.shift(lag)[x.index[0]:x.index[-1]]).corrwith(x)

    @staticmethod
    def find_delays(x, y):
        return y.apply(lambda k: sig.correlate(k,x,mode='valid')).apply(lambda k: k.abs().idxmax()-int(len(k/2))+1)

    @staticmethod 
    def find_correlation(self, x, y):
        return y.corrwith(x)

