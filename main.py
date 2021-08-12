import PySimpleGUI as sg
import os.path
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
import scipy.signal as sig
import matplotlib

FIGSIZE_X=8
FIGSIZE_Y=8

matplotlib.use('TkAgg')

treedata = sg.TreeData()

var_block = [
    [
        sg.Text('Main Variable')
    ],
    [
        sg.Listbox(values=[], enable_events=True, size=(40, 20), key="-MAIN VAR-")
    ],
    [
        sg.Text('Secondary Variables')
    ],
    [
        sg.Listbox(values=[], enable_events=True, select_mode="multiple",size=(40, 20), key="-OTHER VARS-")
    ]
]

search_block = [
        sg.Text('Dataset'),
        sg.In(size=(25, 1), enable_events=True, key="-DATASET-"),
        sg.FileBrowse(),
]

rank_block = [
    [
        sg.Text('Correlations')
    ],
    [
        sg.Tree(data=treedata, enable_events=True, 
                headings=["Correlation", "Phase"],
                key="-CORR-")
    ]
]

plt_layout = [
    [sg.Text('Plots')],
    [sg.Canvas(key='-CANVAS-')]
]


buttons_block = [sg.Button('Correlate'),sg.Button('Plot')]

left_side = [
    search_block,
    [sg.Column(rank_block)],
    [sg.HSeparator()],
    buttons_block

]

layout = [
    [
        sg.Column(left_side),
        sg.VSeperator(),
        sg.Column(plt_layout),
        sg.VSeperator(),
        sg.Column(var_block)
    ]]

# Create the window
window = sg.Window("Correlations", layout).Finalize()
window.Maximize()
fig, (axs1,axs2) = plt.subplots(2,figsize=(FIGSIZE_X,FIGSIZE_Y))
ax3 = axs2.twinx()
figure_canvas_agg = FigureCanvasTkAgg(fig, window['-CANVAS-'].TKCanvas)
figure_canvas_agg.draw()
figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)

dataset = []

# Create an event loop
while True:
    event, values = window.read()
    
    if event == sg.WIN_CLOSED:
        break

    if event == "-DATASET-":
        dataset = pd.read_csv(values["-DATASET-"])

        window.Element("-MAIN VAR-").Update(values=dataset.columns)
        window.Element("-OTHER VARS-").Update(values=dataset.columns)

    elif event == "Correlate":
        try:
            idxs = window['-OTHER VARS-'].get_indexes()
            all_items = window['-OTHER VARS-'].get_list_values()
            other_items = [all_items[index] for index in idxs]

            idxs = window['-MAIN VAR-'].get_indexes()
            all_items = window['-MAIN VAR-'].get_list_values()
            main_item = all_items[idxs[0]]
            
            df_others = dataset[other_items]
            df_main = dataset[main_item]
           
            convolutions = df_others.apply(lambda x: sig.correlate(x,df_main))
            
            max_idx = convolutions.idxmax().apply(lambda x: df_main.size-x-1) 

            for col in df_others:
                df_others[col] = df_others[col].shift(max_idx.loc[col], fill_value=0)

            correlations = df_others.corrwith(df_main)
            new_tree = sg.TreeData()

            for i,j in correlations.sort_values(ascending=False,key=abs).items():
                new_tree.Insert("",i,i,[j,max_idx[i]])

            window.Element("-CORR-").Update(values=new_tree)
        except:
            pass

    elif event == "Plot":
        row = window.Element("-CORR-").SelectedRows[0]
        axs1.cla()
        axs2.cla()
        ax3.cla()

        axs1.scatter(df_main,df_others[row])
        axs1.set_xlabel(main_item)
        axs1.set_ylabel(row)

        plt1,=axs2.plot(df_main)
        ax3 = axs2.twinx()
        plt2,=ax3.plot(df_others[row],color='r')
        ax3.set_ylabel(row)
        axs2.set_ylabel(main_item)
        axs2.set_xlabel('Tempo')
        axs2.legend([main_item,row])
        axs2.legend([plt1,plt2],[main_item,row])

        window['-CANVAS-'].TKCanvas.delete('all')
        #figure_canvas_agg = FigureCanvasTkAgg(fig, window['-CANVAS-'].TKCanvas)
        figure_canvas_agg.draw()
        #figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)

window.close()
