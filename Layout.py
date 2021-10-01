import PySimpleGUI as sg
import ctypes
import tkinter as tk
from tkinter.font import Font

class Layout():
    def __init__(self):
        font = ('Courier', 12)
        ctypes.windll.user32.SetProcessDPIAware()   # Set unit of GUI to pixels
        w, h = sg.Window.get_screen_size()
        tw, th = self.window_dimension(font)
        im_w, im_h = self.get_fig_size() 

        search_block = [
                [
                    sg.Text('      Select Dataset     ', size=(22,1)),
                    sg.In(size=(int(tw/3), 1), enable_events=True, key="-DATASET-"),
                    sg.FileBrowse(size=(int(tw/20),1)),
                    sg.Button('Use EPICS',size=(int(tw/16),1))
                ],
                [
                    sg.Text('Search Sample Signal', size=(22,1)),
                    sg.Input(key='-IN-', enable_events=True, size=(int(tw/3),1)),
                    sg.Button('Search', size=(int(tw/20),1))
                ],
                [
                    sg.Text(' ',size=(int(tw/4), 1)),
                    sg.Input(key='-DATE_BEG-', size=(10,1)),
                    sg.CalendarButton('Begin Date', size=(int(tw*0.07), 1),key="-CAL_BEG-", format='%Y-%m-%d'), 
                    sg.Input(key='-TIME_BEG-', size=(5,1), default_text="00:00")
                ],
                [
                    sg.Text(' ', size=(int(tw/4), 1)),
                    sg.Input(key='-DATE_END-', size=(10, 1)),
                    sg.CalendarButton(' End Date ', size=(int(tw*0.07), 1),key="-CAL_END-", format='%Y-%m-%d'),
                    sg.Input(key='-TIME_END-', size=(5, 1), default_text="00:00")
                ],
                [
                    sg.Text(' ',size=(int(tw/3.3), 1)),
                    sg.Text('Margin (%): '),
                    sg.Input(key='-MARGIN-', size=(5,1), default_text='0.2')
                ],
                [sg.Text(' ', size=(int(tw/3.2), 1)),sg.Button('Select'),sg.Button('Clear')]
        ]

        select_var_block = [
                [
                    sg.Tree(data=sg.TreeData(),enable_events=True, 
                            headings=["Variable"],
                            key="-PVS-", auto_size_columns=False,
                            num_rows=int(th/4)-2,col_widths=[int(tw/3)],justification = "center")
                ]
        ]

        var_block = [sg.Column(search_block, justification='left'), sg.Column(select_var_block, justification='center')]

        plt_layout = [
            [sg.Canvas(key='-CANVAS-', size=(im_w, im_h))]
        ]

        rank_block = [
                [sg.Text(' ', size=(int(tw/12),1)),sg.Tree(data=sg.TreeData(),enable_events=True, 
                        headings=["Variable","Correlation", "Phase"],
                        key="-CORR-", num_rows=int(th/5),col0_width=5,auto_size_columns=False, col_widths=[int(tw/3), 10,10], justification="center")
                ]]

        regex_block = [
                [sg.Text('Examples:\n\n.*HLS.* for all PVs with HLS in the name\n(.*HLS.*)?(.*MARE.*)? for all PVs with HLS OR MARE in the name\n')],
            [sg.Text("Regex: ", enable_events=True, key='-REDIRECT-'),
            sg.Input(key='-REGEX-', size=(int(tw/4),1)),
            sg.Button("Choose")],
            [sg.Text(' '*100, key='-N_VARS-')]
        ]
        
        checkbox =  [
                [sg.Text(' ')],
                [sg.Text(' ')],
                [sg.Combo(['Pearson', 'Spearman', 'Kendall', 'Robust'], default_value='Pearson',key='-METHOD-'), sg.Button('Correlate')],
                [sg.Checkbox('Delay Corrected Signal', default=True, key="-DELAY-", text_color='red',enable_events=True)],
                [sg.Checkbox('Original Signal', default=True, key="-ORIG-", text_color='black',enable_events=True)
            ]]   

        left_side = [
            sg.Column(regex_block),
            sg.VSeparator(),
            sg.Column(rank_block),
            sg.Column(checkbox)
            ]

        self.layout = [
            var_block,
            [sg.HSeparator()],
            plt_layout,
            [sg.HSeparator()],
            left_side,
        ]

        error_layout = [[sg.Text('                                                                \n'*10, key='-ERROR-')]]

    def window_dimension(self, monospaced_font):
        root = tk.Tk()
        width, height = sg.Window.get_screen_size()
        tkfont = Font(font=monospaced_font)
        w, h = tkfont.measure("A"), tkfont.metrics("linespace")
        root.destroy()
        return width//w, height//h

    def get_fig_size(self):
        w, h = sg.Window.get_screen_size()

        return w, int(h/2.1)

    def get_layout(self):
        return self.layout

    def get_error_layout(self):
        return error_layout
