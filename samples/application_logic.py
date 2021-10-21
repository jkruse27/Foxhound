import PySimpleGUI as sg
import layout as layout
import os.path
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
import scipy.signal as sig
import matplotlib
from dataset import Dataset
from datetime import *
from plots import Plots
import pytz
import webbrowser
import threading
import requests
import constants as cte
import causations as cause
from requests.packages.urllib3.exceptions import InsecureRequestWarning

matplotlib.use('TkAgg')
VERSION = '(V0.1.2)'

class Toolbar(NavigationToolbar2Tk):
    def __init__(self, *args, **kwargs):
        super(Toolbar, self).__init__(*args, **kwargs)

class App():

    def __init__(self, name="Foxhound", img="Imgs/foxhound.ico"):
        self.window = sg.Window(name+VERSION, layout.get_layout(), resizable=True, icon=img).Finalize()
        self.params = None
        self.layout = layout
        self.window.Maximize()

        self.is_EPICS = False
        self.current_size = self.window.size
        self.running = False
        self.timeout = None

        self.choosing_params = False
        self.thread = None
        self.begin_date = None
        self.end_date = None
        self.ax3 = None
        self.main_variable = None

        self.causes = cause.Causations(optimizer = 'Adam',
                                        levels = 1,
                                        kernel_size = 4,
                                        significance = 0.8,
                                        dilation = 4,
                                        loginterval = 500,
                                        learningrate=0.01,
                                        epochs=1000)
        self.plots = Plots(self.window[cte.CANVAS].TKCanvas,*self.layout.get_fig_size())
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    def create_tree(self, values, index=None):
        new_tree = sg.TreeData()
        
        if(index==None):
            index = range(len(values))

        for i,j in enumerate(index):
            new_tree.Insert("",j,j,values[i])

        return new_tree

    def create_from_EPICS(self, regex=None, limit=100):
        self.dataset.update_pv_names(regex=regex,limit=limit)
        self.window.Element(cte.PVS).Update(values=self.create_tree(self.dataset.get_columns()))

    def open_dataset(self, name, is_EPICS):
        if(is_EPICS and name != ''):
            self.is_EPICS = False
            self.dataset = Dataset(name)    
            self.window.Element(cte.PVS).Update(values=self.create_tree(self.dataset.get_columns()))

        else:
            self.dataset = Dataset(name)    
            self.window.Element(cte.PVS).Update(values=self.create_tree(self.dataset.get_columns()))

    def initialize_EPICS(self, window):
        self.is_EPICS = True
        window.Element(cte.DATASET).Update(value='EPICS')
        self.dataset.update_pv_names(regex=None,limit=100)
        window.write_event_value(cte.INITIALIZE, '*** The thread says.... "I am finished" ***')

    def update_main_list(self, text, is_EPICS, clicked=False):
        if(is_EPICS and clicked):
            self.create_from_EPICS(regex=".*"+text+".*")

        elif(not is_EPICS):
            self.window.Element(cte.PVS).Update(
                    values=self.create_tree(self.dataset.get_columns(
                        regex=".*"+text+".*")
                        )
                    )

    def choose_corr(self, main_var, begin_date, end_date, margin, is_delayed, is_original, is_EPICS, window):
        selected_row = self.window.Element(cte.CORR).SelectedRows[0]
        selected_row = self.window.Element(cte.CORR).TreeData.tree_dict[selected_row].values[0]
        dt = end_date - begin_date

        if(is_EPICS):
            y = self.dataset.get_EPICS_pv([selected_row], begin_date-margin*dt, end_date+margin*dt)
            x = self.dataset.get_EPICS_pv([main_var], begin_date, end_date)

        else:
            y = self.dataset.get_series(selected_row)
            x = self.dataset.get_series(main_var, begin_date,end_date)

        y1 = []
        colors = []

        if(is_delayed):
            y1.append(y.shift(self.delays[selected_row])[begin_date:end_date])
            colors.append('r')
        if(is_original):
            y1.append(y[begin_date:end_date])
            colors.append('k')

        #self.plots.twinx_canvas(x,main_var,y1,selected_row,colors=colors,t=None,t_label='Time')
        window.write_event_value(cte.TWINX, (x,main_var,y1,selected_row,colors,None,'Time'))

    def open_in_browser(self, link):
        webbrowser.open(link, new=2)

    def causal_discovery(self, main_var, begin_date, end_date, margin, regex, options, is_EPICS, window):
        if(self.is_EPICS):
            if(regex == ''):
                regex = ".*"
            all_delays, columns = self.dataset.causation_EPICS(main_var, 
                                                            regex, 
                                                            begin_date, 
                                                            end_date, 
                                                            margin,
                                                            optimizer = options['optimizer'],
                                                            levels = options['levels'],
                                                            kernel_size = options['kernel_size'],
                                                            significance = options['significance'],
                                                            dilation = options['dilation'],
                                                            loginterval = options['loginterval'],
                                                            learningrate = options['learningrate'],
                                                            epochs = options['epochs'])
        else:
            all_delays, columns = self.dataset.causation(main_var, 
                                                        begin_date, 
                                                        end_date, 
                                                        margin, 
                                                        optimizer = options['optimizer'],
                                                        levels = options['levels'],
                                                        kernel_size = options['kernel_size'],
                                                        significance = options['significance'],
                                                        dilation = options['dilation'],
                                                        loginterval = options['loginterval'],
                                                        learningrate = options['learningrate'],
                                                        epochs = options['epochs'])

        window.write_event_value(cte.CAUSATION, (all_delays,columns))

    def correlate_vars(self, main_var, begin_date, end_date, margin, regex, method, is_EPICS, window):
        if(self.is_EPICS):
            if(regex == ''):
                regex = ".*"
            delays, corrs, names = self.dataset.correlate_EPICS(main_var, regex, begin_date, end_date, margin, method)
        else:
            delays, corrs, names = self.dataset.correlate(main_var, begin_date, end_date, margin, method)

        self.delays = dict(zip(names, delays))
        delays = self.dataset.to_date(delays,names)

        corrs, delays, names = zip(*sorted(zip(corrs, delays, names),reverse=True,key=lambda x: abs(x[0])))

        self.window.Element(cte.CORR).Update(values=self.create_tree(list(map(list, zip(names, corrs, delays)))))
        window.write_event_value(cte.THREAD, '*** The thread says.... "I am finished" ***')

    def convert_time(self, is_EPICS, time):
        if(is_EPICS):
            if(time != None):
                return datetime(time.year,time.month,time.day,hour=time.hour,minute=time.minute, tzinfo=pytz.timezone('America/Sao_Paulo'))
        return time

    def get_var(self, is_EPICS, main_var):
        beg = self.convert_time(is_EPICS, self.begin_date)
        end = self.convert_time(is_EPICS, self.end_date)
        if(is_EPICS): 
            x = self.dataset.get_EPICS_pv([main_var], beg, end)
        else:
            if(beg != None and end != None):
                x = self.dataset.get_series(main_var, beg, end)
            else:
                x = self.dataset.get_series(main_var)
        return x

    def choose_pv(self, is_EPICS, beg_date, end_date, window):
        selected_row = self.window.Element(cte.PVS).SelectedRows[0]
        x_label = self.window.Element(cte.PVS).TreeData.tree_dict[selected_row].values


        if(end_date != ' 00:00'):
            self.end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M")
        if(beg_date != ' 00:00'):
            self.begin_date = datetime.strptime(beg_date,"%Y-%m-%d %H:%M")
        elif(self.end_date == None):
            dt = timedelta(days=7)
            self.begin_date = datetime.today()-dt

        x = self.get_var(is_EPICS, x_label)

        if(beg_date == ' 00:00'):
            d = x.index[0].date().isoformat()
            t = x.index[0].strftime('%H:%M')

            self.begin_date = self.convert_time(is_EPICS,x.index[0])
            self.window.Element(cte.DATE_BEG).Update(value=d)
            self.window.Element(cte.TIME_BEG).Update(value=t)
        if(end_date == ' 00:00'):
            d = x.index[-1].date().isoformat()
            t = x.index[-1].strftime('%H:%M')
            self.end_date = self.convert_time(is_EPICS,x.index[-1])

            self.window.Element(cte.DATE_END).Update(value=d)
            self.window.Element(cte.TIME_END).Update(value=t)

        #self.plots.update_canvas(x,x_label,t=None,t_label='Time')
        self.main_variable = x_label
        window.write_event_value(cte.UPDATE, (x,x_label,None,'Time'))

    def select_time(self, main_var, begin_date, end_date, is_EPICS,window):
        if(begin_date != ''):
            self.begin_date = datetime.strptime(begin_date,"%Y-%m-%d %H:%M")
        else:
            self.begin_date = None

        if(end_date != ''):
            self.end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M")
        else:
            self.end_date = None

        self.begin_date = self.convert_time(is_EPICS, self.begin_date)
        self.end_date = self.convert_time(is_EPICS, self.end_date)
        if(main_var != None): 
            x = self.get_var(is_EPICS, main_var)
            #self.plots.update_canvas(x,main_var,t=None,t_label='Time')
            d = x.index[0].date().isoformat()
            t = x.index[0].strftime('%H:%M')

            self.begin_date = self.convert_time(is_EPICS,x.index[0])
            self.window.Element(cte.DATE_BEG).Update(value=d)
            self.window.Element(cte.TIME_BEG).Update(value=t)

            d = x.index[-1].date().isoformat()
            t = x.index[-1].strftime('%H:%M')
            self.end_date = self.convert_time(is_EPICS,x.index[-1])

            self.window.Element(cte.DATE_END).Update(value=d)
            self.window.Element(cte.TIME_END).Update(value=t)
            window.write_event_value(cte.UPDATE, (x,main_var,None,'Time'))
        else:
            window.write_event_value(cte.THREAD, '*** The thread says.... "I am finished" ***')


    def clean_regex(self, regex):
        if(regex==''):
            return '.*'
        
        return '?'.join([*['(.*'+'.*'.join(el.split('&'))+'.*)' for el in regex.split()], ''])

    def choose_regex(self, regex, is_EPICS, window):
        if(is_EPICS):
            n = self.dataset.number_of_vars(regex)
            message = 'Number of Signals: '+str(n)

            self.window.Element(cte.N_VARS).Update(message)
        else:
            self.window.Element(cte.N_VARS).Update('O dataset próprio realiza a comparação com todas as variáveis')
        window.write_event_value(cte.THREAD, '*** The thread says.... "I am finished" ***')

    def stop_loading(self):
        try:
            self.thread.join()
            sg.popup_animated(None)                     # stop animination in case one is running
            self.running = False
            self.thread = None  # reset variables for next run
            self.timeout = None
        except:
            pass

    def iteration(self):

        if(self.choosing_params):
            event, values = self.params.read(timeout=self.timeout)
        else:
            event, values = self.window.read(timeout=self.timeout)

        if event == sg.WIN_CLOSED:
            if(self.choosing_params):
               self.params.close()
               self.choosing_params=False
            else:
                return 0

        if event == cte.DATASET:
            try:
                self.open_dataset(values[cte.DATASET], self.is_EPICS)
            except:
                sg.Popup('Erro ao abrir dataset')

        elif event == cte.EPICS:
            try:
                if(self.thread == None):
                    self.dataset = Dataset()
                    self.thread = threading.Thread(target=self.initialize_EPICS, args=(self.window,), daemon=True)
                    self.thread.start()
                    self.timeout = 100
                    sg.popup_animated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', transparent_color='white', time_between_frames=self.timeout)
                    self.running = True
                #self.initialize_EPICS()
            except:
                self.stop_loading()
                sg.Popup('Erro ao inicializar EPICS')

        elif event == cte.IN or event == cte.SEARCH:
            try:
                self.update_main_list(values[cte.IN], self.is_EPICS, clicked=(event==cte.SEARCH))
            except:
                sg.Popup('Erro ao pesquisar variáveis')

        elif event == cte.CORR:
            try:
                if(not (values[cte.DELAY] or values[cte.ORIGINAL])):
                    sg.Popup('Selecione ao menos um entre: Original Signal e Delay Corrected Signal')

                elif(self.thread == None):
                    #(self.main_variable, self.begin_date, self.end_date, float(values[self.MARGIN]), values[self.DELAY], values[self.ORIGINAL], self.is_EPICS)
                    self.thread = threading.Thread(target=self.choose_corr, args=(self.main_variable, 
                                                                                self.begin_date, 
                                                                                self.end_date, 
                                                                                float(values[cte.MARGIN]), 
                                                                                values[cte.DELAY], 
                                                                                values[cte.ORIGINAL], 
                                                                                self.is_EPICS, 
                                                                                self.window), daemon=True)
                    self.thread.start()
                    self.timeout = 100
                    sg.popup_animated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', transparent_color='white', time_between_frames=self.timeout)
                    self.running = True
            except:
                self.stop_loading()
                sg.Popup('Erro ao plotar variavel')

        elif event == cte.REDIRECT:
            try:
                self.open_in_browser(cte.REGEX_LINK)
            except:
                sg.Popup('Erro ao abrir o link')

        elif event == cte.PVS:
            try:
                if(self.thread == None):
                    beg = values[cte.DATE_BEG].strip()+" "+values[cte.TIME_BEG].strip()
                    end = values[cte.DATE_END].strip()+" "+values[cte.TIME_END].strip()

                    self.thread = threading.Thread(target=self.choose_pv, args=(self.is_EPICS, 
                                                                       beg,
                                                                       end, 
                                                                       self.window), daemon=True)
                    self.thread.start()
                    self.timeout = 100
                    sg.popup_animated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', transparent_color='white', time_between_frames=self.timeout)
                    self.running = True
            except:
                self.stop_loading()
                sg.Popup('Erro na escolha do sinal principal')
              
        elif event==cte.CREATE:
            self.choosing_params = False
            opts = {'optimizer': values[cte.OPTIMIZER],
                    'levels': int(values[cte.LEVEL]),
                    'kernel_size': int(values[cte.KERNEL]),
                    'significance': float(values[cte.SIGNIFICANCE]),
                    'dilation': int(values[cte.DILATION]),
                    'loginterval': int(values[cte.LOGINT]),
                    'learningrate': float(values[cte.RATE]),
                    'epochs': int(values[cte.EPOCHS])}
            self.params.close()
            self.window.write_event_value(cte.START_CAUSATION, opts)

        elif event==cte.CORRELATE:
            try:
                if(self.thread == None):
                    if(values[cte.METHOD]=='Causation'):
                        self.params = sg.Window('Parameters', self.layout.get_param_layout(), resizable=True).Finalize()
                        self.choosing_params = True
                    else:
                        self.thread = threading.Thread(target=self.correlate_vars, args=(self.main_variable, 
                                                                           self.begin_date,
                                                                           self.end_date, 
                                                                           float(values[cte.MARGIN]), 
                                                                           self.clean_regex(values[cte.REGEX]), 
                                                                           values[cte.METHOD],
                                                                           self.is_EPICS,self.window), daemon=True)
                        self.thread.start()
                        self.timeout = 100
                        sg.popup_animated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', transparent_color='white', time_between_frames=self.timeout)
                        self.running = True
            except:
                self.stop_loading()
                sg.Popup('Erro na correlação')
        
        elif event == cte.START_CAUSATION:
            #try:
                if(self.thread == None):
                    self.thread = threading.Thread(target=self.causal_discovery, args=(self.main_variable, 
                                                                   self.begin_date,
                                                                   self.end_date, 
                                                                   float(values[cte.MARGIN]), 
                                                                   self.clean_regex(values[cte.REGEX]), 
                                                                   values[cte.START_CAUSATION],
                                                                   self.is_EPICS,self.window), daemon=True)
                    self.thread.start()
                    self.timeout = 100
                    sg.popup_animated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', transparent_color='white', time_between_frames=self.timeout)
                    self.running = True
            #except:
            #    self.stop_loading()
            #    sg.Popup('Erro ao buscar causas')

        elif event == cte.THREAD:
            try:
                self.stop_loading()
            except:
                pass

        elif event == cte.CAUSATION:
            try:
                self.stop_loading()
                self.causes.plotgraph(*values[cte.CAUSATION])
            except:
                pass

        elif event == cte.TWINX:
            try:
                self.plots.twinx_canvas(*values[cte.TWINX])
                self.stop_loading()
            except:
                pass

        elif event == cte.INITIALIZE:
            try:
                self.window.Element(cte.PVS).Update(values=self.create_tree(self.dataset.get_columns()))
                self.stop_loading()
            except:
                pass

        elif event == cte.UPDATE:
            try:
                self.plots.update_canvas(*values[cte.UPDATE])
                self.stop_loading()
            except:
                pass

        elif event==cte.SELECT:
            try:
                if(self.plots.selected()):
                    beg, end = self.plots.get_times()
                else:
                    beg = values[cte.DATE_BEG].strip()+" "+values[cte.TIME_BEG].strip()
                    end = values[cte.DATE_END].strip()+" "+values[cte.TIME_END].strip()

                if(self.thread == None):
                    self.thread = threading.Thread(target=self.select_time, args=(self.main_variable, 
                                                                       beg,
                                                                       end, 
                                                                       self.is_EPICS,self.window), daemon=True)
                    self.thread.start()
                    self.timeout = 100
                    sg.popup_animated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', transparent_color='white', time_between_frames=self.timeout)
                    self.running = True
            except:
                self.stop_loading()
                sg.Popup('Erro na seleção do tempo')

        elif event == cte.CHOOSE:
            try:
                if(self.thread == None):
                    self.thread = threading.Thread(target=self.choose_regex, args=(self.clean_regex(values[cte.REGEX]), 
                                                                       self.is_EPICS,self.window), daemon=True)
                    self.thread.start()
                    self.timeout = 100
                    sg.popup_animated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', transparent_color='white', time_between_frames=self.timeout)
                    self.running = True
            except:
                self.stop_loading()
                sg.Popup('Erro na contagem de variáveis')

        elif event == cte.CLEAR:
            try:
                self.plots.clear()
            except:
                sg.Popup('Erro ao Excluir Marcadores')

        if(self.running):
            sg.popup_animated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', transparent_color='white', time_between_frames=self.timeout)
        return 1

    def quit(self):
        self.window.close()
