import os.path
import pandas as pd
import numpy as np
import scipy as sp
import scipy.signal as sig
import pytz
import asyncio
import correlator as corr
import causations
from datetime import *
import epics_requests as req


class Dataset():
    """
    Class for data retrieval and correlation/causation finding.

    Attributes
    ----------
    EPICS : `bool`
        Flag to indicate whether it is using EPICS or a local csv
    dataset : `pandas.DataFrame`
        Dataset being used when using local csv
    loop : `asyncio.loop`
        Loop for async requests
    last_searches : `dict`
        Dictionary with regex and PV names pairs for all regex already searched
    last_dataset_metadata : `dict`
        Dictionary containing the dates and PVs that were last requested
    last_dataset : `pandas.DataFrame`
        DataFrame with the last requested time series
    """

    def __init__(self, filename=None, date_name='datetime'):
        """ Instantiates Dataset object

        Parameters
        ----------
        filename : `str`, optional
            Name of the csv file containing the Dataset.
            Default: None, which uses EPICS instead
        date_name : `str`, optional
            Name of the column of the csv containing the datetime index.
            Default: 'datetime'.
        Returns
        -------
        Dataset
            Returns Dataset instance
        """
        if filename is None:
            self.EPICS = True
            self.last_dataset = None

        else:
            self.EPICS = False
            self.last_dataset = pd.read_csv(filename)
            self.last_dataset[date_name] = pd.to_datetime(
                self.last_dataset[date_name], format="%d.%m.%y %H:%M")
            self.last_dataset.set_index(date_name, inplace=True)

        self.loop = asyncio.get_event_loop()
        self.last_searches = {}
        self.last_dataset_metadata = {'start': None, 'end': None, 'name': None}

    def number_of_vars(self, regex):
        """ Gets number of elements that match the regex in Archiver

        Parameters
        ----------
        regex : `str`
            Java regex for the PVs being considered
        Returns
        -------
        int
            Number of PVs matching the regex
        Notes
        -----
        If the same expression has already been searched, reuses the old result
        , else it makes another request
        """
        if regex not in self.last_searches:
            self.last_searches[regex] = len(
                req.get_names(regex=regex, limit=-1))

        return self.last_searches[regex]

    def get_EPICS_pv(self, name, start_time=None, end_time=None):
        """ Gets DataFrame with the PVs requested

        Parameters
        ----------
        name : `List[str]`
            List with PV names to be requested
        Returns
        -------
        `pandas.DataFrame`
            DataFrame where each column is one PVs timeseries
        Notes
        -----
        If the same names have already been requested, reuses the old result,
        else it makes another request
        """
        new_metadata = {'start': start_time, 'end': end_time, 'name': name}
        if self.last_dataset_metadata != new_metadata:
            self.last_dataset = self.loop.run_until_complete(
                req.call_fetch(name, start_time, end_time))
            self.last_dataset_metadata = new_metadata
            self.last_dataset.index = self.last_dataset.index.tz_localize(pytz.timezone('America/Sao_Paulo')) 

        return self.last_dataset[name][start_time:end_time]

    def update_pv_names(self, regex=None, limit=100):
        """Updates column names from EPICS"""
        self.last_dataset = pd.DataFrame(
            columns=req.get_names(regex=regex, limit=limit))

    def set_dataset(self, filename):
        """Reloads dataset"""
        self.last_dataset = pd.read_csv(filename)

    def get_columns(self, regex='.*'):
        """ Gets PV names in opened dataset (for csv datasets only) according to regex

        Parameters
        ----------
        regex : `str`
            Java regex to match
        Returns
        -------
        `List[str]`
            List containing the names
        """
        return self.last_dataset.filter(regex=regex).columns

    def correlate(self, x_label, begin=None, end=None, margin=0.2, method='Pearson'):
        """ Computes the maximum correlation and delay between x_label and
        each PV in the csv

        Parameters
        ----------
        x_label : `str`
            Name of the main PV
        begin : `Datetime.datetime`, optional
            Beginning date. Default: None (uses ARCHIVER's default)
        end : `Datetime.datetime`, optional
            End date. Default: None (uses ARCHIVER's default)
        margin : `float`, optional
            Percentage of time to consider before and after the defined
            interval. Default: 0.2 (20%)
        method : `str`, optional
            Method to be used. Default: pearson (other options are spearman,
            kendall and robust)
        Returns
        -------
        `(List[float],List[int],List[str])`
            Lists containing the correlation coefficients (rounded to 2
            decimals), delays in samples and PV names
        """
        if begin is None:
            begin = self.last_dataset.index[0]
        if end is None:
            end = self.last_dataset.index[-1]

        delta_t = end-begin

        x_signal = self.last_dataset[x_label][begin:end]
        y_signal = self.last_dataset.drop(x_label, axis=1)[
            begin-margin*delta_t:end+margin*delta_t]
        y_signal = corr.interpolate(y_signal, x_signal.index, margin)

        corrs, delays = corr.correlate(x_signal,
                                       y_signal,
                                       margin,
                                       method.lower())

        return delays, corrs, y_signal.columns

    def correlate_EPICS(self, x_label, regex, begin=None, end=None, margin=0.2, method='Pearson'):
        """ Computes the maximum correlation and delay between x_label and each
        PV matching regex

        Parameters
        ----------
        x_label : `str`
            Name of the main PV
        regex : `str`
            Java regex to match
        begin : `Datetime.datetime`, optional
            Beginning date. Default: None (uses ARCHIVER's default)
        end : `Datetime.datetime`, optional
            End date. Default: None (uses ARCHIVER's default)
        margin : `float`, optional
            Percentage of time to consider before and after the defined
            interval. Default: 0.2 (20%)
        method : `str`, optional
            Method to be used. Default: pearson (other options are
            spearman, kendall and robust)
        Returns
        -------
        `(List[float],List[int],List[str])`
            Lists containing the correlation coefficients (rounded to 2
            decimals), delays in samples and PV names
        """
        pvs = req.get_names(regex=regex, limit=-1)
        delta_t = end-begin
        data = self.get_EPICS_pv(
            list(dict.fromkeys(pvs+[x_label])),
            begin-margin*delta_t,
            end+margin*delta_t)
        x_signal = data[x_label].loc[begin:end]
        y_signal = data.drop(x_label, axis=1)

        corrs, delays = corr.correlate(x_signal,
                                       y_signal,
                                       margin,
                                       method.lower())

        return delays, corrs, y_signal.columns

    def causation(self, x_label, begin=None, end=None, margin=0.2, **opt):
        """ Finds causation graph between x_lab and the PVs in the dataset with
        TCDF [1]__

        Parameters
        ----------
        x_label : `str`
            Name of the main PV
        begin : `Datetime.datetime`, optional
            Beginning date. Default: None (uses ARCHIVER's default)
        end : `Datetime.datetime`, optional
            End date. Default: None (uses ARCHIVER's default)
        margin : `float`, optional
            Percentage of time to consider before and after the defined
            interval. Default: 0.2 (20%)
        **opt : optional
            Options for the optimizer, depth, kernel size, significance,
            stride, log interval, training rate and number of epochs.
            Default: ('Adam',1,4,0.8,4,500,0.01,1000)

        Returns
        -------
        `(List[int],List[str])`
            Lists containing delays in samples and PV names
        See Also
        --------
        Causation.get_causation : performs TCDF

        References
        ----------
            .. [1] Nauta, M.; Bucur, D.; Seifert, C. Causal Discovery with
            Attention-Based Convolutional Neural Networks. Mach. Learn. Knowl.
            Extr. 2019, 1, 312-340. https://doi.org/10.3390/make1010019
        """
        if begin is None:
            begin = self.last_dataset.index[0]
        if end is None:
            end = self.last_dataset.index[-1]

        delta_t = end-begin

        x_signal = self.last_dataset[x_label][begin:end]
        y_signal = self.last_dataset.drop(x_label, axis=1)[
            begin-margin*delta_t:end+margin*delta_t]

        y_signal = corr.interpolate(y_signal, x_signal.index, margin)

        causes = causations.Causations(kernel_size=opt.get('kernel_size', 4),
                                       levels=opt.get('levels', 1),
                                       epochs=opt.get('epochs', 1000),
                                       learningrate=opt.get(
                                           'learningrate', 0.01),
                                       optimizer=opt.get('optimizer', 'Adam'),
                                       dilation=opt.get('dilation', 4),
                                       loginterval=opt.get('loginterval'),
                                       seed=opt.get('seed', 111),
                                       cuda=opt.get('cuda', False),
                                       significance=opt.get('significance',
                                                            0.8))
        return causes.get_causation(pd.concat([x_signal, y_signal],
                                              axis=1).fillna(0))

    def causation_EPICS(self, x_label, regex, begin=None, end=None, margin=0.2, **opt):
        """ Finds causation graph between x_lab and the PVs in the dataset with
        TCDF [2]__

        Parameters
        ----------
        x_label : `str`
            Name of the main PV
        regex : `str`
            Java regex to match for other PVs
        begin : `Datetime.datetime`, optional
            Beginning date. Default: None (uses ARCHIVER's default)
        end : `Datetime.datetime`, optional
            End date. Default: None (uses ARCHIVER's default)
        margin : `float`, optional
            Percentage of time to consider before and after the defined
            interval. Default: 0.2 (20%)
        options : `tuple(str,int,int,float,int,int,float,int)`, optional
            Options for the optimizer, depth, kernel size, significance,
            stride, log interval, training rate and number of epochs.
            Default: ('Adam',1,4,0.8,4,500,0.01,1000)
        Returns
        -------
        `(List[int],List[str])`
            Lists containing delays in samples and PV names
        See Also
        --------
        Causation.get_causation : performs TCDF

        References
        ----------
           .. [2] Nauta, M.; Bucur, D.; Seifert, C. Causal Discovery with
           Attention-Based Convolutional Neural Networks. Mach. Learn. Knowl.
           Extr. 2019, 1, 312-340. https://doi.org/10.3390/make1010019
        """
        pvs = req.get_names(regex=regex, limit=-1)
        delta_t = end-begin
        data = self.get_EPICS_pv(list(dict.fromkeys(pvs+[x_label])),
                                 begin-margin*delta_t,
                                 end+margin*delta_t)
        x_signal = data[x_label].loc[begin:end]
        y_signal = data.drop(x_label, axis=1)
        y_signal = corr.interpolate(y_signal, x_signal.index, 0)

        causes = causations.Causations(kernel_size=opt.get('kernel_size', 4),
                                       levels=opt.get('levels', 1),
                                       epochs=opt.get('epochs', 1000),
                                       learningrate=opt.get(
                                           'learningrate', 0.01),
                                       optimizer=opt.get('optimizer', 'Adam'),
                                       dilation=opt.get('dilation', 4),
                                       loginterval=opt.get('loginterval'),
                                       seed=opt.get('seed', 111),
                                       cuda=opt.get('cuda', False),
                                       significance=opt.get('significance',
                                                            0.8))
        return causes.get_causation(y_signal)

    def get_fs(self, names):
        """ Finds the sample rate of the time series being names

        Parameters
        ----------
        names : `List[str]`
            Name of the time series being considered
        Returns
        -------
        `List[Datetime.Timedelta]`
            List with Timedeltas corresponding to the sampling rate for each
            name in names
        """
        return [(self.last_dataset[col].index[-1]-self.last_dataset[col].index[0])/self.last_dataset[col].size
                for col in names]

    def to_date(self, delays, names):
        """ Converts delays from samples to times

        Parameters
        ----------
        delays : `List[int]`
            Delays in samples
        names : `List[str]`
            Name of the time series being considered
        Returns
        -------
        `List[Datetime.Timedelta]`
            List with Timedeltas corresponding to the delays for each name in
            names
        """
        return [str(round((fs*d).days*24+(fs*d).seconds/3600, 3))+"h"
                for d, fs in zip(delays, self.get_fs(names))]

    def shift(self, x, delays):
        """Shifts signal by delays"""
        for col in x:
            x[col] = x[col].shift(delays.loc[col], fill_value=0)
        return x

    def get_series(self, series_name, begin=None, end=None):
        """Get series from dataset"""
        if begin is None:
            begin = self.last_dataset.index[0]
        if end is None:
            end = self.last_dataset.index[-1]

        series = self.last_dataset[series_name]

        return series.loc[(series.index >= begin) & (series.index <= end)]
