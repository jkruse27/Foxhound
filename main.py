import PySimpleGUI as sg
from Application import *

FIGSIZE_X=8
FIGSIZE_Y=8

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
        sg.Tree(data=sg.TreeData(),enable_events=True, 
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
app = App(layout)
app.init_canvas(FIGSIZE_X,FIGSIZE_Y)

# Create an event loop
while app.iteration():
    pass

app.quit()
