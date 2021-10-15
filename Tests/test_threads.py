import sys

sys.path.insert(1, '../')

from Dataset import *
from datetime import *
import time
import pytz

#dataset = Dataset('../TestData/Dados.csv')
dataset = Dataset()
begin_date = datetime.strptime('2021-09-1 12:00',"%Y-%m-%d %H:%M")
end_date = datetime.strptime('2021-09-7 12:00',"%Y-%m-%d %H:%M")
main_var = 'LNLS:MARE:UP'
regex = '.*HLS.*'

l = 10
'''
print('Not Threaded')
with open('Results/test_not_threaded.txt','w') as f:
    for regex in ['.*HLS.*', '.*HLS.*Level-Mon.*']:
        m = 0
        print('Regex: {m}'.format(m=regex))
        f.write('Regex: {m}\n\n'.format(m=regex))
        for i in range(l):
            print(i)
            start = time.time()

            delays, corrs, names = dataset.test_threads(main_var,'no_thread',begin_date,end_date,0.4,regex=regex)

            end = time.time()
            f.write('Tempo {v}: {t}s\n'.format(v=i, t=end-start))
            m += end-start
        f.write('Correlações: {c}\n'.format(c=" ".join([str(i) for i in corrs])))
        f.write('Delays: {c}\n'.format(c=" ".join([str(i) for i in delays])))
        f.write('---------------------------\n')
        f.write('Tempo Médio: {t}s\n\n\n'.format(t=m/l))
'''
print('Threaded')
with open('Results/test_threaded.txt','w') as f:
    for regex in ['.*HLS.*', '.*HLS.*Level-Mon.*']:
        print('Regex: {m}'.format(m=regex))
        f.write('Regex: {m}\n\n'.format(m=regex))
        for n_threads in [2, 4, 8]:
            m = 0
            print('Number of Threads: {th}'.format(th=n_threads))
            f.write('Number of Threads: {m}\n\n'.format(m=n_threads))

            for i in range(l):
                print(i)
                start = time.time()

                delays, corrs, names = dataset.test_threads(main_var,'thread',begin_date,end_date,0.4,regex=regex, n_threads=n_threads)

                end = time.time()
                f.write('Tempo {v}: {t}s\n'.format(v=i, t=end-start))
                m += end-start
            f.write('Correlações: {c}\n'.format(c=" ".join([str(i) for i in corrs])))
            f.write('Delays: {c}\n'.format(c=" ".join([str(i) for i in delays])))
            f.write('---------------------------\n')
            f.write('Tempo Médio: {t}s\n\n\n'.format(t=m/l))

