import PySimpleGUI as sg
import os.path
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
import scipy.signal as sig
import matplotlib
from Dataset import *
from datetime import *
import pytz
import webbrowser

matplotlib.use('TkAgg')
VERSION = '(V0.1.0)'


class App():

    def __init__(self, layout, FIGSIZE_X, FIGSIZE_Y, name="Foxhound", img="Imgs/foxhound.ico", CANVAS_NAME='-CANVAS-',
            DATASET='-DATASET-', MAIN_VAR='-MAIN VAR-', OTHER_VAR='-OTHER VARS-',
            CORRELATE='Correlate', PLOT='Plot', CORRELATION_SEL='-CORR-', PVS='-PVS-',
            IN='-IN-', DATE_BEG='-DATE_BEG-', DATE_END='-DATE_END-', TIME_BEG='-TIME_BEG-',
            TIME_END='-TIME_END-',SELECT='Select', MARGIN='-MARGIN-', EPICS='Use EPICS',
            SEARCH='Search', CHOOSE='Choose', NUMBER='-N_VARS-', REGEX='-REGEX-', 
            REDIRECT='-REDIRECT-', DELAY='-DELAY-', ORIGINAL='-ORIG-'):
        self.window = sg.Window(name+VERSION, layout, resizable=True, icon=img).Finalize()
        self.window.Maximize()
        self.CANVAS_NAME = CANVAS_NAME
        self.DATASET = DATASET
        self.MAIN_VAR = MAIN_VAR
        self.OTHER_VARS = OTHER_VAR
        self.CORRELATE=CORRELATE
        self.PLOT = PLOT
        self.CORR = CORRELATION_SEL
        self.DATE_BEG = DATE_BEG
        self.DATE_END = DATE_END
        self.TIME_BEG = TIME_BEG
        self.TIME_END = TIME_END
        self.PVS = PVS
        self.IN = IN
        self.SELECT = SELECT
        self.MARGIN = MARGIN
        self.EPICS = EPICS
        self.SEARCH = SEARCH
        self.CHOOSE = CHOOSE
        self.N_VARS = NUMBER
        self.REGEX = REGEX
        self.DELAY = DELAY
        self.ORIGINAL = ORIGINAL
        self.REDIRECT = REDIRECT
        self.REGEX_LINK = 'https://docs.oracle.com/javase/7/docs/api/java/util/regex/Pattern.html'
        self.is_EPICS = False
        self.RESIZE = '-RESIZE-'
        self.current_size = self.window.size

        self.begin_date = None
        self.end_date = None
        self.ax3 = None
        self.main_variable = None

        self.init_canvas(FIGSIZE_X, FIGSIZE_Y)


    def init_canvas(self, FIGSIZE_X=8,FIGSIZE_Y=8):
        self.FIGSIZE_X = FIGSIZE_X
        self.FIGSIZE_Y = FIGSIZE_Y
        self.fig, self.axs1 = plt.subplots(figsize=(FIGSIZE_X/100,FIGSIZE_Y/100), dpi=100)
        self.figure_canvas_agg = FigureCanvasTkAgg(self.fig, self.window[self.CANVAS_NAME].TKCanvas)
        self.figure_canvas_agg.draw()
        self.figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)

    def twinx_canvas(self,x,x_label,y,y_label,colors='r',t=None,t_label='Time'):
        self.axs1.cla()

        if(self.ax3 != None):
            self.ax3.remove()

        self.ax3 = self.axs1.twinx()

        self.row = x_label

        if(t==None):
            self.axs1.plot(x,label=x_label)
            self.axs1.set_ylabel(x_label)
            self.axs1.set_xlabel(t_label)
        else:
            self.axs1.plot(t,x,label=x_label)
            self.axs1.set_ylabel(x_label)
            self.axs1.set_xlabel(t_label)
        

        if(t==None):
            for signal, color in zip(y,colors):
                self.ax3.plot(signal,color=color,label=y_label)
            self.ax3.set_ylabel(y_label, rotation=-90,labelpad=7)
        else:
            for signal, color in zip(y,colors):
                self.ax3.plot(t,signal,color=color,label=y_label)
            self.ax3.set_ylabel(y_label, rotation=-90,labelpad=7)

        k = int(len(self.axs1.xaxis.get_ticklabels())/5)

        self.axs1.yaxis.label.set_color('blue')
        self.ax3.yaxis.label.set_color(colors[0])

        for n, label in enumerate(self.axs1.xaxis.get_ticklabels()):
            if n % k != 0:
                label.set_visible(False)

        self.window[self.CANVAS_NAME].TKCanvas.delete('all')
        self.figure_canvas_agg.draw()
        self.figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)


    def update_canvas(self,x,x_label,t=None,t_label='Time'):
        self.row = x_label

        self.axs1.clear()

        if(self.ax3!=None):
            self.ax3.remove()
            self.ax3 = None

        if(t==None):
            self.axs1.plot(x,label=x_label)
            self.axs1.set_ylabel(x_label)
            self.axs1.set_xlabel(t_label)
        else:
            self.axs1.plot(t,x,label=x_label)
            self.axs1.set_ylabel(x_label)
            self.axs1.set_xlabel(t_label)

        k = int(len(self.axs1.xaxis.get_ticklabels())/5)

        for n, label in enumerate(self.axs1.xaxis.get_ticklabels()):
            if n % k != 0:
                label.set_visible(False)

        self.axs1.yaxis.label.set_color('blue')

        self.window[self.CANVAS_NAME].TKCanvas.delete('all')
        self.figure_canvas_agg.draw()
        self.figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)


    def create_tree(self, values, index=None):
        new_tree = sg.TreeData()
        
        if(index==None):
            index = range(len(values))

        for i,j in enumerate(index):
            new_tree.Insert("",j,j,values[i])

        return new_tree

    def create_from_EPICS(self, regex=None, limit=100):
        self.dataset.update_pv_names(regex=regex,limit=limit)
        self.window.Element(self.PVS).Update(values=self.create_tree(self.dataset.get_columns()))

    def open_dataset(self, name, is_EPICS):
        if(is_EPICS and name != ''):
            self.is_EPICS = False
            self.dataset = Dataset(name)    
            self.window.Element(self.PVS).Update(values=self.create_tree(self.dataset.get_columns()))

        else:
            self.dataset = Dataset(name)    
            self.window.Element(self.PVS).Update(values=self.create_tree(self.dataset.get_columns()))

    def initialize_EPICS(self):
        self.is_EPICS = True
        self.window.Element(self.DATASET).Update(value='EPICS')
        self.dataset = Dataset()
        self.create_from_EPICS()

    def update_main_list(self, text, is_EPICS, clicked=False):
        if(is_EPICS and clicked):
            self.create_from_EPICS(regex=".*"+text+".*")

        elif(not is_EPICS):
            self.window.Element(self.PVS).Update(
                    values=self.create_tree(self.dataset.get_columns(
                        regex=".*"+text+".*")
                        )
                    )

    def choose_corr(self, main_var, begin_date, end_date, margin, is_delayed, is_original, is_EPICS):
        if(not (is_delayed or is_original)):
            sg.Popup('Selecione ao menos um entre: Original Signal e Delay Corrected Signal')
            return

        selected_row = self.window.Element(self.CORR).SelectedRows[0]
        selected_row = self.window.Element(self.CORR).TreeData.tree_dict[selected_row].values[0]
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

        self.twinx_canvas(x,main_var,y1,selected_row,colors=colors,t=None,t_label='Time')

    def open_in_browser(self, link):
        webbrowser.open(link, new=2)

    def correlate_vars(self, main_var, begin_date, end_date, margin, regex, is_EPICS):
        if(self.is_EPICS):
            if(regex == ''):
                regex = ".*"
            delays, corrs, names = self.dataset.correlate_EPICS(main_var, regex, begin_date, end_date, margin)
        else:
            delays, corrs, names = self.dataset.correlate(main_var, begin_date, end_date, margin)

        self.delays = dict(zip(names, delays))
        delays = self.dataset.to_date(delays,names)

        corrs, delays, names = zip(*sorted(zip(corrs, delays, names),reverse=True,key=lambda x: abs(x[0])))

        self.window.Element(self.CORR).Update(values=self.create_tree(list(map(list, zip(names, corrs, delays)))))

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

    def choose_pv(self, is_EPICS, beg_date, end_date):
        selected_row = self.window.Element(self.PVS).SelectedRows[0]
        x_label = self.window.Element(self.PVS).TreeData.tree_dict[selected_row].values


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
            self.window.Element(self.DATE_BEG).Update(value=d)
            self.window.Element(self.TIME_BEG).Update(value=t)
        if(end_date == ' 00:00'):
            d = x.index[-1].date().isoformat()
            t = x.index[-1].strftime('%H:%M')
            self.end_date = self.convert_time(is_EPICS,x.index[-1])

            self.window.Element(self.DATE_END).Update(value=d)
            self.window.Element(self.TIME_END).Update(value=t)

        self.update_canvas(x,x_label,t=None,t_label='Time')
        self.main_variable = x_label

    def select_time(self, main_var, begin_date, end_date, is_EPICS):
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
            self.update_canvas(x,main_var,t=None,t_label='Time')

    def clean_regex(self, regex):
        if(regex==''):
            return '.*'
        
        return '?'.join([*['(.*'+'.*'.join(el.split('&'))+'.*)' for el in regex.split()], ''])

    def choose_regex(self, regex, is_EPICS):
        if(is_EPICS):
            n = self.dataset.number_of_vars(regex)
            message = 'Number of Signals: '+str(n)

            self.window.Element(self.N_VARS).Update(message)
        else:
            self.window.Element(self.N_VARS).Update('O dataset próprio realiza a comparação com todas as variáveis')

    def iteration(self):

        event, values = self.window.read()
        
        if event == sg.WIN_CLOSED:
            return 0

        if event == self.DATASET:
            try:
                self.open_dataset(values[self.DATASET], self.is_EPICS)
            except:
                sg.Popup('Erro ao abrir dataset')

        elif event == self.EPICS:
            try:
                self.initialize_EPICS()
            except:
                sg.Popup('Erro ao inicializar EPICS')

        elif event == self.IN or event == self.SEARCH:
            try:
                self.update_main_list(values[self.IN], self.is_EPICS, clicked=(event==self.SEARCH))
            except:
                sg.Popup('Erro ao pesquisar variáveis')

        elif event == self.CORR:
#            try:
            self.choose_corr(self.main_variable, self.begin_date, self.end_date, float(values[self.MARGIN]), values[self.DELAY], values[self.ORIGINAL], self.is_EPICS)
 #           except:
 #               sg.Popup('Erro ao plotar variavel')

        elif event == self.REDIRECT:
            try:
                self.open_in_browser(self.REGEX_LINK)
            except:
                sg.Popup('Erro ao abrir o link')

        elif event == self.PVS:
            try:
                beg = values[self.DATE_BEG].strip()+" "+values[self.TIME_BEG].strip()
                end = values[self.DATE_END].strip()+" "+values[self.TIME_END].strip()
                self.choose_pv(self.is_EPICS, beg, end)
            except:
                sg.Popup('Erro na escolha do sinal principal')
               
        elif event==self.CORRELATE:
            try:
                self.correlate_vars(self.main_variable, self.begin_date, self.end_date, float(values[self.MARGIN]), self.clean_regex(values[self.REGEX]), self.is_EPICS)
            except:
                sg.Popup('Erro na correlação')

        elif event==self.SELECT:
            try:
                beg = values[self.DATE_BEG].strip()+" "+values[self.TIME_BEG].strip()
                end = values[self.DATE_END].strip()+" "+values[self.TIME_END].strip()
                self.select_time(self.main_variable, beg, end, self.is_EPICS)
            except:
                sg.Popup('Erro na seleção do tempo')

        elif event == self.CHOOSE:
            try:
                self.choose_regex(self.clean_regex(values[self.REGEX]), self.is_EPICS)
            except:
                sg.Popup('Erro na contagem de variáveis')

        return 1

    def quit(self):
        self.window.close()
