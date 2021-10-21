import asyncio
import aiohttp
import operator
import pandas as pd
from datetime import datetime, timedelta
import requests
import ast

"""
Module that encapsulates PV requests to the Archiver
"""

PVS_URL = 'http://10.0.38.42/mgmt/bpl/getAllPVs'
ARCHIVE_URL = 'http://10.0.38.42/retrieval/data/getData.json'

def correct_datetime(x):
    """ Turn Dataframes Index to DatetimeIndex

    Parameters
    ----------
    x : `pandas.DataFrame`
        DataFrame with index corresponding to strings of datetimes
    Returns
    -------
    `pandas.DataFrame`
        DataFrame with the new DatetimeIndex
    """
    x.index = pd.to_datetime(x.index, format="%d.%m.%y %H:%M")
    return x

def get_names(regex=None, limit=100):
    """ Get all pv names from Archiver that correspond to the given regex

    Parameters
    ----------
    regex : `str`, optional
        Regex that will be used. Default: None, which matches all pvs (in the order of millions)
    limit : `int`, optional
        Maximum number of names to get (the larger the number, the longer it takes)
    Returns
    -------
    `List[str]`
        List containing all the names
    """
    if(regex == None):
        params = {'limit': limit}
    else:
        params = {'limit': limit, 'regex':regex}

    response = requests.get(PVS_URL, params=params, verify=False)

    return ast.literal_eval(response.text)

async def fetch(session, pv, time_from, time_to, is_optimized, mean_minutes):

    if is_optimized:
        pv_query = f'mean_{int(60*mean_minutes)}({pv})'
    else:
        pv_query = pv

    query = {'pv': pv_query}
    if(time_from != None):
        query['from'] = time_from
    if(time_to!=None):
        query['to'] = time_to

    response_as_json = {}
    async with session.get(ARCHIVE_URL, params=query) as response:
        try:
            response_as_json = await response.json()
        except aiohttp.client_exceptions.ContentTypeError:
            print(f'Failed to retrieve data from PV {pv}.')
            response_as_json = None
        return response_as_json


async def retrieve_data(pvs, time_from, time_to, isOptimized=False, mean_minutes=0):
    async with aiohttp.ClientSession() as session:
        data = await asyncio.gather(*[fetch(session, pv, time_from, time_to, isOptimized, mean_minutes) for pv in pvs])
        return data


async def fetch_data(pv_list, timespam):
    optimize = True
    mean_minutes = 3
    res = await retrieve_data(pv_list, timespam['init'], timespam['end'], optimize, mean_minutes)
    try:
        # cleaning response
        res_mapped = list(map(lambda x: x[0]['data'], res))
    except TypeError:
        log.append_stdout('Incorrect PV(s) name(s) or bad timespam. Fetching failed.\n')
        return

    values = [list(map(lambda x: x['val'], pv_data)) for pv_data in res_mapped]
    ts = [list(map(lambda x: datetime.fromtimestamp(x['secs']).strftime("%d.%m.%y %H:%M"), pv_data)) for pv_data in res_mapped]
    # creating pandas dataframe object
    series = []
    for val, pv, t in zip(values, pv_list, ts):
        d = {}
        d['datetime'] = t
        d[pv] = val
        s = pd.DataFrame(d)
        s.reset_index(drop=True, inplace=True)
        s = s.set_index('datetime')
        series.append(s)
    data = pd.concat(series,axis=1)
    data = data.fillna(method='ffill', axis=1)
    data = data.fillna(0)

    # indexing by datetime
    #data.reset_index(drop=True, inplace=True)
    #data = data.set_index('datetime')
    
    return data

async def call_fetch(pv_list, dt_init, dt_end):
    """ Get PVs time series

    Parameters
    ----------
    pv_list : `List[str]`
        List with the name of all PVs to request
    dt_init : aware `Datetime.datetime`
        Date and time indicating where to begin the timeseries
    dt_end : aware `Datetime.datetime`
        Date and time indicating where to end the timeseries
    Returns
    -------
    `pandas.DataFrame`
        DataFrame where the columns correspond to each PV name in pv_list and the index is a Index with the date as a `str`
    """
    try:

        timespan={'init': None, 'end':None}

        if(dt_init != None):
            timespan['init'] = (dt_init - dt_init.utcoffset()).replace(tzinfo=None).isoformat(timespec='milliseconds')+'Z'
        if(dt_end != None):
            timespan['end'] = (dt_end - dt_end.utcoffset()).replace(tzinfo=None).isoformat(timespec='milliseconds')+'Z'

    except:
        print('Erro com os tempos!')
        return

    data = await asyncio.create_task(fetch_data(pv_list, timespan))
    return correct_datetime(data)
