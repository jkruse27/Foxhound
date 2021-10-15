# Test time difference from performing or not FFT in each of the time series when requesting them


import sys
from scipy.fft import *

sys.path.insert(1, '../')

from Dataset import *
from datetime import *
import time
import pytz

#dataset = Dataset('../TestData/Dados.csv')
dataset = Dataset()
begin_date = datetime.strptime('2021-09-1 12:00',"%Y-%m-%d %H:%M").replace(tzinfo=pytz.timezone('America/Sao_Paulo'))
end_date = datetime.strptime('2021-09-14 12:00',"%Y-%m-%d %H:%M").replace(tzinfo=pytz.timezone('America/Sao_Paulo'))
regex = '.*HLS.*'
pvs = dataset.epics_req.get_names(regex=regex, limit=-1)
l = 10
m = 0
print('No FFT')
with open('Results/test_no_fft.txt','w') as f:
    for i in range(l):
        print(i)
        start = time.time()
        res = dataset.get_EPICS_pv(pvs,begin_date,end_date)
        end = time.time()
        f.write('Tempo {v}: {t}s\n'.format(v=i, t=end-start))
        m += end-start
    f.write('---------------------------\n')
    f.write('Tempo Médio: {t}s\n\n\n'.format(t=m/l))

'''
print('FFT during request')

with open('Results/test_fft.txt','w') as f:
    for i in range(l):
        print(i)
        start = time.time()
        res = dataset2.get_EPICS_pv(names,begin_date,end_date)
        end = time.time()
        f.write('Tempo {v}: {t}s\n'.format(v=i, t=end-start))
        m += end-start
    f.write('---------------------------\n')
    f.write('Tempo Médio: {t}s\n\n\n'.format(t=m/l))
'''

m=0
print('FFT Afterwards')
with open('Results/test_fft.txt','w') as f:
    for i in range(l):
        print(i)
        start = time.time()
        res = dataset.get_EPICS_pv(pvs,begin_date,end_date)
        #res = res.reset_index()
        #print(res.columns)
        #res = res.drop('datetime', axis=1)
        res = res.apply(lambda x: rfft(x.to_numpy()))
        end = time.time()
        f.write('Tempo {v}: {t}s\n'.format(v=i, t=end-start))
        m += end-start
    f.write('---------------------------\n')
    f.write('Tempo Médio: {t}s\n\n\n'.format(t=m/l))
