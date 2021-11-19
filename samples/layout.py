import ctypes
import tkinter as tk
from tkinter.font import Font
import platform
import PySimpleGUI as sg
import constants as cte

"""
This module encapsulates the pySimpleGUI layouts used.
"""


def get_screen_size():
    """Get screen size in pixels"""
    width, height = sg.Window.get_screen_size()

    return width*0.8, height*0.7


def window_dimension(monospaced_font):
    """Get window dimensions with respect to a font.

    Parameters
    ----------
    monospaced_font : `tkinter.font.Font`
        Font which will be used as unit of measure

    Returns
    -------
    (int, int)
        Width and Height of the screen in respective font units
    """
    root = tk.Tk()
    width, height = get_screen_size()
    tkfont = Font(font=monospaced_font)
    font_width, font_height = tkfont.measure("A"), tkfont.metrics("linespace")
    root.destroy()
    return width//font_width, height//font_height


def get_fig_size():
    """Get size of image to fit current window

    Parameters
    ----------

    Returns
    -------
    `(int, int)`
        Width and Height of the image in pixels
    """
    width, height = get_screen_size()

    return width, int(height/2.1)


def get_layout():
    """Get layout for main application window

    Parameters
    ----------

    Returns
    -------
    `List[List[Element]]`
        Layout for main application window
    """
    if platform.uname()[0] == "Windows":
        ctypes.windll.user32.SetProcessDPIAware()
    font = ('Courier', 12)
    font_width, font_height = window_dimension(font)

    search_block = [
        [
            sg.Text('      Select Dataset     ', size=(22, 1)),
            sg.In(size=(int(font_width/3), 1),
                  enable_events=True, key=cte.DATASET),
            sg.FileBrowse(size=(int(font_width/20), 1)),
            sg.Button(cte.EPICS, size=(int(font_width/16), 1))
        ],
        [
            sg.Text('Search Sample Signal', size=(22, 1)),
            sg.Input(key=cte.IN, enable_events=True,
                     size=(int(font_width/3), 1)),
            sg.Button(cte.SEARCH, size=(int(font_width/20), 1))
        ],
        [
            sg.Text(' ', size=(int(font_width/4), 1)),
            sg.Input(key=cte.DATE_BEG, size=(10, 1)),
            sg.CalendarButton('Begin Date', size=(int(font_width*0.07), 1),
                              key=cte.CAL_BEG, format='%Y-%m-%d'),
            sg.Input(key=cte.TIME_BEG, size=(5, 1), default_text="00:00")
        ],
        [
            sg.Text(' ', size=(int(font_width/4), 1)),
            sg.Input(key=cte.DATE_END, size=(10, 1)),
            sg.CalendarButton(' End Date ', size=(int(font_width*0.07), 1),
                              key=cte.CAL_END, format='%Y-%m-%d'),
            sg.Input(key=cte.TIME_END, size=(5, 1), default_text="00:00")
        ],
        [
            sg.Text(' ', size=(int(font_width/3.3), 1)),
            sg.Text('Margin (%): '),
            sg.Input(key=cte.MARGIN, size=(5, 1), default_text='0.2')
        ],
        [
            sg.Text(' ', size=(int(font_width/3.2), 1)),
            sg.Button(cte.SELECT),
            sg.Button(cte.CLEAR)
        ]
    ]

    select_var_block = [
        [
            sg.Tree(data=sg.TreeData(),
                    enable_events=True,
                    headings=["Variable"],
                    key=cte.PVS, auto_size_columns=False,
                    num_rows=int(font_height/4)-2,
                    col_widths=[int(font_width/3)],
                    justification="center")
        ]
    ]

    var_block = [
        sg.Column(search_block,
                  justification='left',
                  expand_x=True),
        sg.Column(select_var_block,
                  justification='center',
                  expand_x=True)
    ]

    plt_layout = [
        [sg.Canvas(key=cte.CANVAS)]
    ]

    rank_block = [
        [
            sg.Tree(data=sg.TreeData(),
                    enable_events=True,
                    headings=["Variable", "Correlation", "Phase"],
                    key=cte.CORR,
                    num_rows=int(font_height/5),
                    col0_width=5,
                    auto_size_columns=False,
                    col_widths=[int(font_width/3), 10, 10],
                    justification="center")
        ]
    ]

    regex_block = [
        [sg.Text(''.join(['Examples:\n\n',
                          'HLS for all PVs with HLS in the name\n',
                          'HLS MARE for all PVs with HLS OR MARE in the name\n'
                          ])
                 )
         ],
        [sg.Text("Regex: ", enable_events=True, key=cte.REDIRECT),
         sg.Input(key=cte.REGEX, size=(int(font_width/4), 1)),
         sg.Button(cte.CHOOSE)],
        [sg.Text(' '*100, key=cte.N_VARS)]
    ]

    checkbox = [
        [sg.Text(' ')],
        [sg.Text(' ')],
        [sg.Combo(['Pearson', 'Spearman', 'Kendall', 'Robust', 'Causation'],
                  default_value='Pearson',
                  key=cte.METHOD),
         sg.Button(cte.CORRELATE)],
        [sg.Checkbox('Delay Corrected Signal', default=True,
                     key=cte.DELAY, text_color='red', enable_events=True)],
        [sg.Checkbox('Original Signal',
                     default=True,
                     key=cte.ORIGINAL,
                     text_color='black',
                     enable_events=True)
         ]]

    left_side = [
        sg.Column(regex_block, element_justification='c', expand_x=True),
        sg.VSeparator(),
        sg.Column(rank_block, justification='left', element_justification='l'),
        sg.Column(checkbox, expand_x=True)
    ]

    layout = [
        var_block,
        [sg.HSeparator()],
        plt_layout,
        [sg.HSeparator()],
        left_side,
    ]

    return layout


def get_param_layout():
    """Get layout for causality finding parameters definition window

    Parameters
    ----------

    Returns
    -------
    `List[List[Element]]`
        Layout for causality finding parameters window
    """
    box = [
        [
            sg.Text('Parameters')
        ],
        [
            sg.Text('   Epochs: '), sg.Input(
                key=cte.EPOCHS, size=(10, 1), default_text="1000"),
            sg.Text('    Kernel Size: '), sg.Input(
                key=cte.KERNEL, size=(10, 1), default_text="4")
        ],
        [
            sg.Text('     Depth: '), sg.Input(
                key=cte.LEVEL, size=(10, 1), default_text="1"),
            sg.Text(' Learning Rate: '), sg.Input(
                key=cte.RATE, size=(10, 1), default_text="0.01")
        ],
        [
            sg.Text('   Dilation: '), sg.Input(
                key=cte.DILATION, size=(10, 1), default_text="4"),
            sg.Text('   Significance: '), sg.Input(
                key=cte.SIGNIFICANCE, size=(10, 1), default_text="0.8")
        ],
        [
            sg.Text('Optimizer: '), sg.Input(
                key=cte.OPTIMIZER, size=(10, 1), default_text="Adam"),
            sg.Text('    Log Interval: '), sg.Input(
                key=cte.LOGINT, size=(10, 1), default_text="500")
        ],
        [sg.Button('Create Causal Graph', key=cte.CREATE)]
    ]

    return box


def get_error_layout():
    """Get layout for error message windows

    Parameters
    ----------

    Returns
    -------
    `List[List[Element]]`
        Layout for error message window
    """
    error_layout = [[sg.Text('                     \n'*10, key='-ERROR-')]]

    return error_layout
