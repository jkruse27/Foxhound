import PySimpleGUI as sg
import os.path
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
import scipy.signal as sig
import matplotlib
from Correlation import *
from datetime import *
import pytz

matplotlib.use('TkAgg')

class App():

    def __init__(self, layout, name="Correlations", CANVAS_NAME='-CANVAS-',
            DATASET='-DATASET-', MAIN_VAR='-MAIN VAR-', OTHER_VAR='-OTHER VARS-',
            CORRELATE='Correlate', PLOT='Plot', CORRELATION_SEL='-CORR-', PVS='-PVS-',
            IN='-IN-', DATE_BEG='-DATE_BEG-', DATE_END='-DATE_END-', TIME_BEG='-TIME_BEG-',
            TIME_END='-TIME_END-',SELECT='Select', MARGIN='-MARGIN-', EPICS='Use EPICS',
            SEARCH='Search', CHOOSE='Choose', NUMBER='-N_VARS-', REGEX='-REGEX-'):
        self.window = sg.Window(name, layout, resizable=True).Finalize()
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
        self.is_EPICS = False


        self.begin_date = None
        self.end_date = None
        self.ax3 = None


    def init_canvas(self, FIGSIZE_X=8,FIGSIZE_Y=8):
        self.FIGSIZE_X = FIGSIZE_X
        self.FIGSIZE_Y = FIGSIZE_Y
        self.fig, self.axs1 = plt.subplots(figsize=(FIGSIZE_X,FIGSIZE_Y))
        self.figure_canvas_agg = FigureCanvasTkAgg(self.fig, self.window[self.CANVAS_NAME].TKCanvas)
        self.figure_canvas_agg.draw()
        self.figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)

    def twinx_canvas(self,x,x_label,y,y_label,t=None,t_label='Time'):
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
            self.ax3.plot(y,color='r',label=y_label)
            self.ax3.set_ylabel(y_label, rotation=-90,labelpad=7)
        else:
            self.ax3.plot(t,y,color='r',label=y_label)
            self.ax3.set_ylabel(y_label, rotation=-90,labelpad=7)

        k = int(len(self.axs1.xaxis.get_ticklabels())/5)

        self.axs1.yaxis.label.set_color('blue')
        self.ax3.yaxis.label.set_color('red')

        for n, label in enumerate(self.axs1.xaxis.get_ticklabels()):
            if n % k != 0:
                label.set_visible(False)

        self.window[self.CANVAS_NAME].TKCanvas.delete('all')
        self.figure_canvas_agg.draw()


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

    def iteration(self):

        event, values = self.window.read()
        
        if event == sg.WIN_CLOSED:
            return 0

        if self.is_EPICS == False:
            if event == self.DATASET:
                try:
                    self.dataset = Correlations(values[self.DATASET])    
                    self.window.Element(self.PVS).Update(values=self.create_tree(self.dataset.get_columns()))
                except:
                    print('Erro ao abrir dataset')

            elif event == self.EPICS:
                self.is_EPICS = True
                self.window.Element(self.DATASET).Update(value='EPICS')
                self.dataset = Correlations()
                self.create_from_EPICS()

            elif event == self.IN:
                self.window.Element(self.PVS).Update(
                        values=self.create_tree(self.dataset.get_columns(
                            regex=".*"+values[self.IN]+".*")
                            )
                        )

            elif event == self.CORRELATE:
                margin = float(values[self.MARGIN])
               
                delays, corrs, names = self.dataset.correlate(self.main_variable, self.begin_date, self.end_date, margin)
                self.delays = dict(zip(names, delays))
                delays = self.dataset.to_date(delays,names)

                corrs, delays, names = zip(*sorted(zip(corrs, delays, names),reverse=True,key=lambda x: abs(x[0])))

                self.window.Element(self.CORR).Update(values=self.create_tree(list(map(list, zip(names, corrs, delays)))))

            elif event == self.CORR:
                selected_row = self.window.Element(self.CORR).SelectedRows[0]
                selected_row = self.window.Element(self.CORR).TreeData.tree_dict[selected_row].values[0]
                y = self.dataset.get_series(selected_row)
                y = y.shift(self.delays[selected_row])[self.begin_date:self.end_date]
                x = self.dataset.get_series(self.main_variable, self.begin_date,self.end_date)
                self.twinx_canvas(x,self.main_variable, y,selected_row,t=None,t_label='Time')

            elif event==self.PVS:
                selected_row = self.window.Element(self.PVS).SelectedRows[0]
                x_label = self.window.Element(self.PVS).TreeData.tree_dict[selected_row].values
                x = self.dataset.get_series(x_label)
                self.update_canvas(x,x_label,t=None,t_label='Time')
                self.main_variable = x_label

            elif event==self.SELECT:
                try:
                    self.begin_date = datetime.strptime(values[self.DATE_BEG].strip()+" "+values[self.TIME_BEG].strip(),"%Y-%m-%d %H:%M")
                except:
                    self.begin_date = None

                try:
                    self.end_date = datetime.strptime(values[self.DATE_END].strip()+" "+values[self.TIME_END].strip(),"%Y-%m-%d %H:%M")
                except:
                    self.end_date = None

                x = self.dataset.get_series(self.main_variable, self.begin_date,self.end_date)
                self.update_canvas(x,self.main_variable,t=None,t_label='Time')
        else:
            if event == self.SEARCH:
                self.create_from_EPICS(regex=".*"+values[self.IN]+".*")

            elif event == self.DATASET:
                try:
                    self.is_EPICS = False
                    self.dataset = Correlations(values[self.DATASET])    
                    self.window.Element(self.PVS).Update(values=self.create_tree(self.dataset.get_columns()))
                except:
                    print('Erro ao abrir dataset')

            elif event==self.PVS:
                selected_row = self.window.Element(self.PVS).SelectedRows[0]
                x_label = self.window.Element(self.PVS).TreeData.tree_dict[selected_row].values
                x = self.dataset.get_EPICS_pv([x_label])
                self.update_canvas(x,x_label,t=None,t_label='Time')
                self.main_variable = x_label

            elif event==self.SELECT:
                try:
                    tmp = datetime.strptime(values[self.DATE_BEG].strip()+" "+values[self.TIME_BEG].strip(),"%Y-%m-%d %H:%M")
                    self.begin_date = datetime(tmp.year,tmp.month,tmp.day,hour=tmp.hour,minute=tmp.minute, tzinfo=pytz.timezone('America/Sao_Paulo'))
                except:
                    self.begin_date = None

                try:
                    tmp = datetime.strptime(values[self.DATE_END].strip()+" "+values[self.TIME_END].strip(),"%Y-%m-%d %H:%M")
                    self.end_date = datetime(tmp.year,tmp.month,tmp.day,hour=tmp.hour,minute=tmp.minute, tzinfo=pytz.timezone('America/Sao_Paulo'))
                except:
                    self.end_date = None

                x = self.dataset.get_EPICS_pv([self.main_variable], self.begin_date,self.end_date)
                self.update_canvas(x,self.main_variable,t=None,t_label='Time')

            elif event == self.CORRELATE:
                margin = float(values[self.MARGIN])
                self.marg = margin
                regex = values[self.REGEX]
                if(regex == ''):
                    regex = ".*"

                delays, corrs, names = self.dataset.correlate_EPICS(self.main_variable, regex, self.begin_date, self.end_date, margin)
                self.delays = dict(zip(names, delays))
                delays = self.dataset.to_date(delays,names)

                corrs, delays, names = zip(*sorted(zip(corrs, delays, names),reverse=True,key=lambda x: abs(x[0])))

                self.window.Element(self.CORR).Update(values=self.create_tree(list(map(list, zip(names, corrs, delays)))))

            elif event == self.CORR:
                selected_row = self.window.Element(self.CORR).SelectedRows[0]
                selected_row = self.window.Element(self.CORR).TreeData.tree_dict[selected_row].values[0]

                dt = self.end_date - self.begin_date

                y = self.dataset.get_EPICS_pv([selected_row], self.begin_date-self.marg*dt,self.end_date+self.marg*dt)
                y = y.shift(self.delays[selected_row])[self.begin_date:self.end_date]
                x = self.dataset.get_EPICS_pv([self.main_variable], self.begin_date,self.end_date)
                self.twinx_canvas(x,self.main_variable, y,selected_row,t=None,t_label='Time')

        if event == self.CHOOSE:
            n = self.dataset.number_of_vars(values[self.REGEX])
            message = 'Número de Sinais: '+str(n)

            self.window.Element(self.N_VARS).Update(message)


        return 1

    def quit(self):
        self.window.close()
