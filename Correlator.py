import os.path
import pandas as pd
import numpy as np
import scipy as sp
import scipy.signal as sig
import scipy.interpolate as inter

class Correlator():
    '''
    @staticmethod
    def correlate(x, y, margin):
        y = Correlator.interpolate(y,x.index,margin)
        correlations = pd.DataFrame([Correlator.lagged_corr(x,y,lag) for lag in range(-1*int(x.size*margin),int(x.size*margin)+1)], columns=y.columns)
        delays = [correlations[col].abs().idxmax() for col in correlations]
        corrs = [round(correlations[col].iloc[delays[pos]],2) for pos, col in enumerate(correlations)]
        delays = [delay-int(x.size*margin) for delay in delays]
        
        return corrs, delays
    '''

    @staticmethod
    def correlate(x, y, margin, method='pearson'):
        y = Correlator.interpolate(y,x.index,margin)
        beg, end = (x.index.min(), x.index.max())

        b = 1.5
        c = 4
        q1 = 1.540793
        q2 = 0.8622731

        z = lambda x: (x-x.mean())/np.std(x, ddof=1)
        g = lambda x: x if abs(x) <= b else q1*np.tanh(q2*(c-abs(x)))*np.sign(x) if abs(x) <= c else 0

        if(method == 'robust'):
            method='pearson'
            x = pd.Series(z(sig.detrend(x)), index=x.index, name=x.name)
            x = x.apply(g)
            y = y.apply(lambda s: z(sig.detrend(s))).applymap(g)

        N = int(x.size*margin)

        l = int(np.log2(N))
        b = 4
        log_lags = np.array([int(2**i+(j*2**i/b)) for i in range(2,l+1) for j in range(4) if 2**i+(j*2**i/b) < N])
        log_lags = list(-1*log_lags)[::-1]+[-3,-2,-1,0,1,2,3]+list(log_lags)

        new_lags = list(range(-1*max(log_lags),max(log_lags)+1))
        vals = pd.DataFrame([Correlator.lagged_corr(x,y,lag,method) for lag in log_lags])
        vals = vals.apply(lambda s: inter.make_interp_spline(log_lags, abs(s),k=3)(new_lags))
        peaks = vals.apply(lambda s: pd.Series([new_lags[i] for i in sig.find_peaks(s)[0]]+[new_lags[max(range(len(s)), key=s.__getitem__)]]).drop_duplicates())

        peak_corr = pd.DataFrame(np.array([[x.corr((y[col].shift(int(peak)))[beg:end], method=method) if not pd.isna(peak) else 0 for peak in peaks[col]] for col in peaks]).transpose(), columns=y.columns) 

        dela = [peak_corr[col].abs().idxmax() for col in peak_corr]
        delays = [int(peaks[col].iloc[dela[pos]]) for pos, col in enumerate(peak_corr)]
        corrs = [round(peak_corr[col].iloc[dela[pos]],2) for pos, col in enumerate(peak_corr)]
        
        return corrs, delays

    @staticmethod
    def lagged_corr(x, y, lag, method='pearson'):
        if(method in ['pearson', 'kendall', 'spearman']):
            return (y.shift(lag)[x.index[0]:x.index[-1]]).corrwith(x, method=method)
        else:
            return None

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
