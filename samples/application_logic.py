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
import interface as itf

"""
Module to control the application.
"""

matplotlib.use('TkAgg')
VERSION = '(V0.1.2)'

class Toolbar(NavigationToolbar2Tk):
    def __init__(self, *args, **kwargs):
        super(Toolbar, self).__init__(*args, **kwargs)

class App():
    """ Class used to control the operations of the application
    """

    def __init__(self, name="Foxhound", img="Imgs/foxhound.ico",config_img="Imgs/config.ico"):
        """Instantiates App object

        Parameters
        ----------
        name : str, optional
            Name of the main window of the application
        img : str, optional
            Icon for the main window
        config_img : str, optional
            Icon for the configuration window
        """
        self.config_img = config_img

        self.window = itf.Interface()
        self.window.create_window(name+VERSION, 
                                layout.get_layout(), 
                                resizable=True,
                                icon=img,
                                maximize=True)
        self.params = None
        self.layout = layout

        self.is_EPICS = False
        self.current_size = self.window.get_window_size()
        self.running = False
        self.timeout = None

        self.choosing_params = False
        self.thread = None
        self.begin_date = None
        self.end_date = None
        self.main_variable = None

        self.causes = cause.Causations(optimizer = 'Adam',
                                        levels = 1,
                                        kernel_size = 4,
                                        significance = 0.8,
                                        dilation = 4,
                                        loginterval = 500,
                                        learningrate=0.01,
                                        epochs=1000)

        self.plots = Plots(self.window.get_canvas(cte.CANVAS),*self.layout.get_fig_size())
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    def open_dataset(self, name, is_EPICS):
        if(is_EPICS and name != ''):
            self.is_EPICS = False
            self.dataset = Dataset(name)    
            self.window.update_tree(self.dataset.get_columns(),cte.PVS)

        else:
            self.dataset = Dataset(name)    
            self.window.update_tree(self.dataset.get_columns(),cte.PVS)

    def initialize_EPICS(self):
        try:
            self.is_EPICS = True
            self.window.update_element('EPICS', cte.DATASET)
            self.dataset.update_pv_names(regex=None,limit=100)
            data = self.dataset.get_columns()
            self.window.write_event(cte.INITIALIZE, data)
        except:
            self.window.write_event(cte.ERROR, 'Error initializing EPICS')

    def update_main_list(self, text, is_EPICS, clicked=False):
        if(is_EPICS and clicked):
            try:
                self.dataset.update_pv_names(regex=".*"+text+".*",limit=100)
                data = self.dataset.get_columns()
            except:
                self.window.write_event(cte.ERROR, 'Error during search')

        elif(not is_EPICS):
            data = self.dataset.get_columns(regex=".*"+text+".*")

        self.window.write_event(cte.INITIALIZE, data)

    def choose_corr(self, main_var, begin_date, end_date, margin, is_delayed, is_original, is_EPICS):
        try:
            selected_row = self.window.get_selected_row(cte.CORR)
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

            self.window.write_event(cte.TWINX, (x,main_var,y1,selected_row,colors,None,'Time'))
        except:
            self.window.write_event(cte.ERROR, 'Error choosing signal')

    def open_in_browser(self, link):
        webbrowser.open(link, new=2)

    def causal_discovery(self, main_var, begin_date, end_date, margin, regex, options, is_EPICS):
        try:
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

            self.window.write_event(cte.CAUSATION, (all_delays,columns))
        except:
            self.window.write_event(cte.ERROR, 'Error during causal discovery')

    def correlate_vars(self, main_var, begin_date, end_date, margin, regex, method, is_EPICS):
        try:
            if(self.is_EPICS):
                if(regex == ''):
                    regex = ".*"
                delays, corrs, names = self.dataset.correlate_EPICS(main_var, regex, begin_date, end_date, margin, method)
            else:
                delays, corrs, names = self.dataset.correlate(main_var, begin_date, end_date, margin, method)

            self.delays = dict(zip(names, delays))
            delays = self.dataset.to_date(delays,names)

            corrs, delays, names = zip(*sorted(zip(corrs, delays, names),reverse=True,key=lambda x: abs(x[0])))

            self.window.update_tree(list(map(list, zip(names, corrs, delays))),cte.CORR)
            self.window.write_event(cte.THREAD, '*** Correlation Finished ***')
        except:
            self.window.write_event(cte.ERROR, 'Error during correlation')

    def convert_time(self, is_EPICS, time):
        if(is_EPICS):
            if(time != None):
                return datetime(time.year,
                                time.month,
                                time.day,
                                hour=time.hour,
                                minute=time.minute,
                                tzinfo=pytz.timezone('America/Sao_Paulo'))
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

    def choose_pv(self, is_EPICS, beg_date, end_date):
        try:
            x_label = self.window.get_selected_row(cte.PVS)

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
                self.window.update_element(d, cte.DATE_BEG)
                self.window.update_element(t,cte.TIME_BEG)
            if(end_date == ' 00:00'):
                d = x.index[-1].date().isoformat()
                t = x.index[-1].strftime('%H:%M')
                self.end_date = self.convert_time(is_EPICS,x.index[-1])

                self.window.update_element(d, cte.DATE_END)
                self.window.update_element(t,cte.TIME_END)

            self.main_variable = x_label
            self.window.write_event(cte.UPDATE, (x,x_label,None,'Time'))
        except:
            self.window.write_event(cte.ERROR, 'Error choosing variable')

    def select_time(self, main_var, begin_date, end_date, is_EPICS):
        try:
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
                d = x.index[0].date().isoformat()
                t = x.index[0].strftime('%H:%M')

                self.begin_date = self.convert_time(is_EPICS,x.index[0])
                self.window.update_element(d, cte.DATE_BEG)
                self.window.update_element(t,cte.TIME_BEG)

                d = x.index[-1].date().isoformat()
                t = x.index[-1].strftime('%H:%M')
                self.end_date = self.convert_time(is_EPICS,x.index[-1])

                self.window.update_element(d, cte.DATE_END)
                self.window.update_element(t,cte.TIME_END)
                self.window.write_event(cte.UPDATE, (x,main_var,None,'Time'))
            else:
                self.window.write_event(cte.THREAD, '*** Time Selected ***')
        except:
            self.window.write_event(cte.ERROR, 'Error during time selection')

    def clean_regex(self, regex):
        if(regex==''):
            return '.*'
        
        return '?'.join([*['(.*'+'.*'.join(el.split('&'))+'.*)' for el in regex.split()], ''])

    def choose_regex(self, regex, is_EPICS):
        try:
            if(is_EPICS):
                n = self.dataset.number_of_vars(regex)
                message = 'Number of Signals: '+str(n)

                self.window.update_element(message,cte.N_VARS)
            else:
                message = 'O dataset próprio realiza a comparação com todas as variáveis'
                self.window.update_element(message,cte.N_VARS)

            self.window.write_event(cte.THREAD, '*** Regex Chosen ***')
        except:
            self.window.write_event(cte.ERROR, 'Error counting variables')

    def stop_loading(self):
        try:
            if(self.thread != None):
                self.thread.join()
            self.window.stop_loading()

            self.running = False
            self.thread = None
            self.timeout = None
        except:
            pass
    
    def start_thread(self):
        self.thread.start()
        self.timeout = 100
        self.window.start_loading(timeout=self.timeout)
        self.running = True


    def iteration(self):

        if(self.choosing_params):
            event, values = self.window.read_events(timeout=self.timeout, index=self.params)
        else:
            event, values = self.window.read_events(timeout=self.timeout)

        if event == sg.WIN_CLOSED:
            if(self.choosing_params):
               self.window.close(index=self.params)
               self.choosing_params=False
            else:
                return 0

        if event == cte.DATASET:
            try:
                if(values[cte.DATASET] != ''):
                    self.open_dataset(values[cte.DATASET], self.is_EPICS)
            except:
                self.window.popup('Error opening dataset')

        elif event == cte.EPICS:
            try:
                if(self.thread == None):
                    self.dataset = Dataset()
                    self.thread = threading.Thread(target=self.initialize_EPICS, daemon=True)
                    self.start_thread()
            except:
                self.stop_loading()
                self.window.popup('Error initializing EPICS')

        elif event == cte.IN or event == cte.SEARCH:
            try:
                if(self.thread == None and self.is_EPICS and event==cte.SEARCH):
                    self.thread = threading.Thread(target=self.update_main_list, args=(
                                                                    values[cte.IN],
                                                                    self.is_EPICS,
                                                                    (event==cte.SEARCH)),
                                                                    daemon=True)
                    self.start_thread()
                elif(not self.is_EPICS):
                    self.update_main_list(values[cte.IN], self.is_EPICS, clicked=(event==cte.SEARCH))
            except:
                self.stop_loading()
                self.window.popup('Error searching for variables')

        elif event == cte.CORR:
            try:
                if(not (values[cte.DELAY] or values[cte.ORIGINAL])):
                    self.window.popup('You must choose at least one between:\n  - Original Signal\n  - Delay Corrected Signal')

                elif(self.thread == None):
                    self.thread = threading.Thread(target=self.choose_corr, args=(self.main_variable, 
                                                                                self.begin_date, 
                                                                                self.end_date, 
                                                                                float(values[cte.MARGIN]), 
                                                                                values[cte.DELAY], 
                                                                                values[cte.ORIGINAL], 
                                                                                self.is_EPICS), daemon=True)
                    self.start_thread()
            except:
                self.stop_loading()
                self.window.popup('Error plotting the variable')

        elif event == cte.REDIRECT:
            try:
                self.open_in_browser(cte.REGEX_LINK)
            except:
                self.window.popup('Error opening link')

        elif event == cte.PVS:
            try:
                if(self.thread == None):
                    beg = values[cte.DATE_BEG].strip()+" "+values[cte.TIME_BEG].strip()
                    end = values[cte.DATE_END].strip()+" "+values[cte.TIME_END].strip()

                    self.thread = threading.Thread(target=self.choose_pv, args=(self.is_EPICS, 
                                                                       beg,
                                                                       end), daemon=True)
                    self.start_thread()
            except:
                self.stop_loading()
                self.window.popup('Error choosing main signal')
              
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
            self.window.close(self.params)
            self.window.write_event(cte.START_CAUSATION, opts)

        elif event==cte.CORRELATE:
            try:
                if(self.thread == None):
                    if(values[cte.METHOD]=='Causation'):
                        self.params = self.window.create_window('Parameters', 
                                                                self.layout.get_param_layout(),
                                                                icon=self.config_img,
                                                                resizable=True)
                        self.choosing_params = True
                    else:
                        self.thread = threading.Thread(target=self.correlate_vars, args=(self.main_variable, 
                                                                           self.begin_date,
                                                                           self.end_date, 
                                                                           float(values[cte.MARGIN]), 
                                                                           self.clean_regex(values[cte.REGEX]), 
                                                                           values[cte.METHOD],
                                                                           self.is_EPICS), daemon=True)
                        self.start_thread()
            except:
                self.stop_loading()
                self.window.popup('Error during correlation')
        
        elif event == cte.START_CAUSATION:
            try:
                if(self.thread == None):
                    self.thread = threading.Thread(target=self.causal_discovery, args=(self.main_variable, 
                                                                   self.begin_date,
                                                                   self.end_date, 
                                                                   float(values[cte.MARGIN]), 
                                                                   self.clean_regex(values[cte.REGEX]), 
                                                                   values[cte.START_CAUSATION],
                                                                   self.is_EPICS), daemon=True)
                    self.start_thread()
            except:
                self.stop_loading()
                self.window.popup('Error searching for causes')

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
                self.window.update_tree(values[cte.INITIALIZE], cte.PVS)
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
                                                                       self.is_EPICS), daemon=True)
                    self.start_thread()
            except:
                self.stop_loading()
                self.window.popup('Error selecting time')

        elif event == cte.CHOOSE:
            try:
                if(self.thread == None):
                    self.thread = threading.Thread(target=self.choose_regex, args=(self.clean_regex(values[cte.REGEX]), 
                                                                       self.is_EPICS), daemon=True)
                    self.start_thread()
            except:
                self.stop_loading()
                self.window.popup('Error counting variables')

        elif event == cte.CLEAR:
            try:
                self.plots.clear()
            except:
                self.window.popup('Error displaying markers')
        elif event == cte.ERROR:
            self.stop_loading()
            self.window.popup(values[cte.ERROR])

        if(self.running):
            self.window.start_loading(timeout=self.timeout)

        return 1

    def quit(self):
        self.window.close()
