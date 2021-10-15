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

print('Full')
with open('Results/test_full.txt','w') as f:
    for marg in [0.05, 0.1, 0.2, 0.3, 0.4]:
        m = 0
        print('Margem: {m}'.format(m=marg))
        f.write('Margem: {m}\n\n'.format(m=marg))
        for i in range(l):
            print(i)
            start = time.time()

            delays, corrs, names = dataset.test(main_var,'EPICS_full',begin_date,end_date,marg,regex=regex)

            end = time.time()
            f.write('Tempo {v}: {t}s\n'.format(v=i, t=end-start))
            m += end-start
        f.write('Correlações: {c}\n'.format(c=" ".join([str(i) for i in corrs])))
        f.write('Delays: {c}\n'.format(c=" ".join([str(i) for i in delays])))
        f.write('---------------------------\n')
        f.write('Tempo Médio: {t}s\n\n\n'.format(t=m/l))

print('Log')
with open('Results/test_log.txt','w') as f:
    for marg in [0.05, 0.1, 0.2, 0.3, 0.4]:
        m = 0
        print('Margem: {m}'.format(m=marg))
        f.write('Margem: {m}\n\n'.format(m=marg))
        for i in range(l):
            print(i)
            start = time.time()

            delays, corrs, names = dataset.test(main_var,'EPICS_log',begin_date,end_date,marg,regex=regex)

            end = time.time()
            f.write('Tempo {v}: {t}s\n'.format(v=i, t=end-start))
            m += end-start
        f.write('Correlações: {c}\n'.format(c=" ".join([str(i) for i in corrs])))
        f.write('Delays: {c}\n'.format(c=" ".join([str(i) for i in delays])))
        f.write('---------------------------\n')
        f.write('Tempo Médio: {t}s\n\n\n'.format(t=m/l))

