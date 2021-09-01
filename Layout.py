import PySimpleGUI as sg

class Layout():
    def __init__(self):
        search_block = [
                [
                    sg.Text('      Select Dataset     '),
                    sg.In(size=(70, 1), enable_events=True, key="-DATASET-"),
                    sg.FileBrowse(),
                    sg.Button('Use EPICS')
                ],
                [
                    sg.Text('Search Sample Signal'),
                    sg.Input(key='-IN-', enable_events=True, size=(70,1)),
                    sg.Button('Search')
                ],
                [
                    sg.Text(' '*70),
                    sg.Input(key='-DATE_BEG-', size=(10,1)),
                    sg.CalendarButton('Begin Date',key="-CAL_BEG-", format='%Y-%m-%d'), 
                    sg.Input(key='-TIME_BEG-', size=(5,1), default_text="00:00")
                ],
                [
                    sg.Text(' '*70),
                    sg.Input(key='-DATE_END-', size=(10,1)),
                    sg.CalendarButton(' End Date ',key="-CAL_END-", format='%Y-%m-%d'),
                    sg.Input(key='-TIME_END-', size=(5,1), default_text="00:00")
                ],
                [
                    sg.Text(' '*80),
                    sg.Text('Margin (%): '),
                    sg.Input(key='-MARGIN-', size=(5,1), default_text='0.2')
                ],
                [sg.Text(' '*94),sg.Button('Select')]
        ]

        select_var_block = [
                [
                    sg.Tree(data=sg.TreeData(),enable_events=True, 
                            headings=["Variable"],
                            key="-PVS-", auto_size_columns=False,
                            num_rows=9,col_widths=[30],justification = "left")
                ]
        ]

        var_block = [sg.Column(search_block, justification='left'), sg.Column(select_var_block, justification='center')]

        plt_layout = [
            [sg.Canvas(key='-CANVAS-')]
        ]

        rank_block = [[
                sg.Text('Correlations'),
                sg.Tree(data=sg.TreeData(),enable_events=True, 
                        headings=["Variable","Correlation", "Phase"],
                        key="-CORR-", num_rows=5,col0_width=45, col_widths=[60, 15], justification="center")
                ]]

        buttons_block = [[sg.Button('Correlate')]]

        regex_block = [
            [sg.Text('. --> Any Character\n* --> Repeat 0 or more times\n() --> Capture in group')],
            [sg.Text("Regex: ", enable_events=True, key='-REDIRECT-'),
            sg.Input(key='-REGEX-')],
            [sg.Text(' '*75, key='-N_VARS-')]
        ]

        left_side = [
            sg.Column(regex_block),
            sg.Button("Choose"),
            sg.Column(buttons_block),
            sg.Column(rank_block),
            sg.Checkbox('Correct Delay:', default=True, key="-DELAY-", enable_events=True)
                ]

        self.layout = [
            var_block,
            [sg.HSeparator()],
            plt_layout,
            [sg.HSeparator()],
            left_side,
        ]

        error_layout = [[sg.Text('                                                                \n'*10, key='-ERROR-')]]

    def get_layout(self):
        return self.layout

    def get_error_layout(self):
        return error_layout
