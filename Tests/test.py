from Dataset import *
from datetime import *
import time

dataset = Dataset('TestData/Dados.csv')
begin_date = datetime.strptime('2021-08-2 12:00',"%Y-%m-%d %H:%M")
end_date = datetime.strptime('2021-08-7 12:00',"%Y-%m-%d %H:%M")
main_var = 'TU-11C:SS-HLS-Ax48NW5:Level-Mon'

start = time.time()

delays, corrs, names = dataset.correlate(main_var, begin_date, end_date, 0.2)

end = time.time()
print(end - start)
print(delays)
print(corrs)
