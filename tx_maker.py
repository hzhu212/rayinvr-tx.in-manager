from enum import Enum
from itertools import islice
import logging
import numpy as np
import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import traceback

from . import ROOT_DIR
from .util.custom_widgets import TextLineNumbers, CustomText


class TxMaker(ttk.Frame):
    """tx.in maker"""

    SURVEY_NAMES = ('obs33a', 'obs34a', 'obs31', 'obs30', 'scs_line4a', 'scs_line1a')
    TIME_OFFSETS = (0.0220, 0.0290, 0.0365, 0.1537, -0.0348, 0)
    NLINE_PREVIEW = 100
    SURVEY_DIR = 'trace_number_vs_x'

    def __init__(self, master=None):
        super().__init__(master)
        self.logger = self._get_logger()
        self.init_variables()
        # self.set_custom_style()
        self.create_widgets()

    def init_variables(self):
        self.survey_idx = None
        self.horizon_path = tk.StringVar()
        self.horizon_preview_msg = tk.StringVar()
        self.horizon_precision = tk.DoubleVar()
        self.survey_time_offset = tk.DoubleVar()
        self.survey_preview_msg = tk.StringVar()
        self.ray_number = tk.IntVar()
        self.save_path = tk.StringVar()
        self.horizon_preview_msg.set(
            'The heading %d lines of selected horizon file. (Format as "Line,Trace,Time"): ' %(self.NLINE_PREVIEW))
        self.horizon_precision.set(0.02)
        self.survey_preview_msg.set('The Trace-Number vs. X-Offset Table for selected survey: ')
        self.ray_number.set(1)
        self.save_path.set(os.path.join(ROOT_DIR, 'tx_in', 'undefined_tx.in'))

    def set_custom_style(self):
        s = ttk.Style()
        s.configure('.', font=('Microsoft YaHei UI', 10))
        s.configure('sm.TButton', font=('Microsoft YaHei UI', 8), width=7)

    def create_widgets(self):
        PADX_LG = (15, 15)
        PADY_SM, PADY_LG, PADY_LLG = (5, 0), (10, 0), (20, 0)
        PADY_SM_E, PADY_LG_E, PADY_LLG_E = (5, 5), (10, 10), (20, 20)

        # Make window resizable
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # Horizon File (exported from the Kingdom Software) Options
        row_horizon = ttk.LabelFrame(self, text='Horizon File (exported from the Kingdom Software) Options')
        row_horizon.columnconfigure(0, weight=1)
        row_horizon.rowconfigure(2, weight=1)
        row_horizon.grid(column=0, padx=PADX_LG, pady=PADY_LG, sticky='nswe')
        horizon_selector = ttk.Frame(row_horizon)
        horizon_selector.columnconfigure(1, weight=1)
        horizon_selector.grid(row=0, column=0, pady=PADY_SM, sticky='nswe')
        ttk.Label(horizon_selector, text='Horizon file (.csv): ')\
            .grid(row=0, column=0, sticky='nsw')
        entry = ttk.Entry(horizon_selector, textvariable=self.horizon_path)
        entry.grid(row=0, column=1, sticky='nswe')
        entry.bind('<Return>', self.horizon_file_changed)
        ttk.Button(horizon_selector, text='Select', command=self.select_horizon_path)\
            .grid(row=0, column=2, sticky='nse')

        # Preview horizon with Text widget
        horizon_preview_header = ttk.Frame(row_horizon)
        horizon_preview_header.grid(row=1, column=0, pady=PADY_SM, sticky='nswe')
        ttk.Label(horizon_preview_header, textvariable=self.horizon_preview_msg)\
            .grid(row=0, column=0,  sticky='nsw')
        self.btn_open_horizon_file = ttk.Button(
            horizon_preview_header, text='open it', style='sm.TButton', state=tk.DISABLED,
            command=self.open_horizon_file)
        self.btn_open_horizon_file.grid(row=0, column=1, sticky='nsw')
        horizon_previewer = ttk.Frame(row_horizon)
        self.horizon_text = self.create_text_previewer(horizon_previewer)
        horizon_previewer.grid(row=2, column=0, pady=PADY_SM, sticky='nswe')

        # Set horizon time precision
        prec_setter = ttk.Frame(row_horizon)
        prec_setter.grid(row=3, column=0, pady=PADY_LG_E, sticky='nswe')
        ttk.Label(prec_setter, text='Time Precision for horizon(0.03 for OBS and 0.02 for SCS in general): ')\
            .grid(row=0, column=0, sticky='nsw')
        tk.Spinbox(
            prec_setter, state='readonly', from_=0, to=0.1, increment=0.005, width=6,
            textvariable=self.horizon_precision,
            ).grid(row=0, column=1, sticky='nsw')

        # Survey Options
        row_survey = ttk.LabelFrame(self, text='Survey Options')
        row_survey.rowconfigure(2, weight=1)
        row_survey.columnconfigure(0, weight=1)
        row_survey.grid(column=0, padx=PADX_LG, pady=PADY_LG, sticky='nswe')
        survey_selector = ttk.Frame(row_survey)
        survey_selector.grid(row=0, column=0, pady=PADY_SM, sticky='nswe')
        ttk.Label(survey_selector, text='Select Survey Name: ')\
            .grid(row=0, column=0, sticky='nsw')
        cbox = ttk.Combobox(survey_selector, width=12, state='readonly', values=self.SURVEY_NAMES)
        cbox.grid(row=0, column=1, sticky='nsw')
        cbox.bind('<<ComboboxSelected>>', self.survey_changed)
        ttk.Label(survey_selector, text='Time offset for selected survey (second): ')\
            .grid(row=0, column=2, padx=(10, 0), sticky='nsw')
        ttk.Entry(survey_selector, state='readonly', width=10, textvariable=self.survey_time_offset)\
            .grid(row=0, column=3, sticky='nsw')

        # Preview survey file
        ttk.Label(row_survey, textvariable=self.survey_preview_msg)\
            .grid(row=1, column=0, pady=PADY_SM, sticky='nsw')
        survey_previewer = ttk.Frame(row_survey)
        self.survey_text = self.create_text_previewer(survey_previewer)
        survey_previewer.grid(row=2, column=0, pady=PADY_SM_E, sticky='nswe')

        # tx.in Options
        row_txin = ttk.LabelFrame(self, text='tx.in Options')
        row_txin.columnconfigure(0, weight=1)
        row_txin.grid(column=0, padx=PADX_LG, pady=PADY_LG, sticky='nswe')

        # Set ray number
        ray_number_setter = ttk.Frame(row_txin)
        ray_number_setter.grid(row=0, column=0, pady=PADY_SM, sticky='nswe')
        ttk.Label(ray_number_setter, text='Ray group number in tx.in: ')\
            .grid(row=0, column=0, sticky='nsw')
        tk.Spinbox(
            ray_number_setter, state='readonly', from_=1, to=1e3, increment=1, width=5,
            textvariable=self.ray_number,
            ).grid(row=0, column=1, sticky='nsw')

        # Set save path
        save_path_setter = ttk.Frame(row_txin)
        save_path_setter.columnconfigure(1, weight=1)
        save_path_setter.grid(row=1, column=0, pady=PADY_SM_E, sticky='nswe')
        ttk.Label(save_path_setter, text='Save to: ').grid(row=0, column=0, sticky='nsw')
        ttk.Entry(save_path_setter, textvariable=self.save_path)\
            .grid(row=0, column=1, sticky='nswe')
        ttk.Button(save_path_setter, text='Change', command=self.select_save_path)\
            .grid(row=0, column=2, sticky='nse')

        # command buttons
        row_cmd = ttk.Frame(self)
        row_cmd.rowconfigure(0, weight=1)
        row_cmd.columnconfigure(0, weight=1)
        row_cmd.grid(column=0, padx=PADX_LG, pady=PADY_LLG_E, sticky='nswe')
        ttk.Button(row_cmd, text='OK', command=self.handle_ok).grid(row=0, column=0)


    def create_text_previewer(self, container):
        container.rowconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        text_widget = CustomText(container, font=('Consolas', 10), state=tk.DISABLED)
        text_widget.grid(row=0, column=1, sticky='nswe')
        y_scroll = tk.Scrollbar(container, orient=tk.VERTICAL, command=text_widget.yview)
        y_scroll.grid(row=0, column=2, sticky='ns')
        text_widget.config(yscrollcommand=y_scroll.set)
        # show text line numbers
        horizon_text_ln = TextLineNumbers(container, width=30)
        horizon_text_ln.attach(text_widget)
        horizon_text_ln.grid(row=0, column=0, sticky='nsw')
        text_widget.bind("<<Change>>", horizon_text_ln.redraw)
        text_widget.bind("<Configure>", horizon_text_ln.redraw)
        return text_widget


    def _get_logger(self):
        logger = logging.getLogger('TxMaker')
        logger.setLevel(logging.DEBUG)
        LOG_FILE_PATH = os.path.join(ROOT_DIR, 'log', 'tx_maker.log')
        file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf8')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s: %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

    def select_horizon_path(self):
        p = filedialog.askopenfilename(
            defaultextension='.csv',
            filetypes=[('comma-separated values', '.csv'), ('any type', '.*')],
            initialdir=os.path.join(ROOT_DIR, 'horizon'),
            parent=self,
            title='Select Horizon File')
        p = p.strip()
        if not p:
            return
        self.horizon_path.set(os.path.normpath(p))
        self.horizon_file_changed()

    def horizon_file_changed(self, event=None):
        new_path = self.horizon_path.get()
        # enable open-horizon-file button
        self.btn_open_horizon_file.config(state=tk.NORMAL)
        # show horizon preview
        text = self._get_horizon_content()
        self.horizon_text.config(state=tk.NORMAL)
        self.horizon_text.delete('1.0', tk.END)
        self.horizon_text.insert(tk.END, text)
        self.horizon_text.config(state=tk.DISABLED)
        # # set default value for horizon precision
        # precision = 0.03 if 'obs' in new_path else 0.02
        # self.horizon_precision.set(precision)
        # set default value for save path
        horizon_name = os.path.splitext(os.path.split(new_path)[1])[0]
        sp = os.path.join(os.path.split(self.save_path.get())[0], horizon_name+'_tx.in')
        self.save_path.set(sp)

    def select_save_path(self):
        p = filedialog.asksaveasfilename(
            defaultextension='.in',
            filetypes=[('rayinvr tx.in files', '.in'), ('any type', '.*')],
            initialdir=os.path.join(ROOT_DIR, 'tx_in'),
            initialfile='untitled_tx.in',
            parent=self,
            title='Save As')
        p = p.strip()
        if p:
            self.save_path.set(os.path.normpath(p))

    def open_horizon_file(self):
        os.system('start "" "%s"' %(self.horizon_path.get()))

    def survey_changed(self, event):
        self.survey_idx = event.widget.current()
        self.survey_time_offset.set(self.TIME_OFFSETS[self.survey_idx])
        text = self._get_survey_content()
        self.survey_text.config(state=tk.NORMAL)
        self.survey_text.delete('1.0', tk.END)
        self.survey_text.insert(tk.END, text)
        self.survey_text.config(state=tk.DISABLED)

    def _get_horizon_content(self):
        file_path = self.horizon_path.get()
        if not os.path.isfile(file_path):
            messagebox.showerror('Error', 'File not exists: \n%s'%(file_path))
            return ''
        with open(file_path, 'r') as f:
            lines = list(islice(f, self.NLINE_PREVIEW))
            return ''.join(lines)

    def _get_survey_file_path(self):
        survey_name = self.SURVEY_NAMES[self.survey_idx]
        survey_path = os.path.join(ROOT_DIR, self.SURVEY_DIR, survey_name+'.txt')
        return survey_path

    def _get_survey_content(self):
        """Survey info: trace-number vs. x-offset table"""
        survey_name = self.SURVEY_NAMES[self.survey_idx]
        survey_path = self._get_survey_file_path()
        if not os.path.isfile(survey_path):
            messagebox.showerror(
                'Error', 'No Trace-Number vs. X-Offset table for survey "%s".\nPlease create one '
                'at "%s"' %(survey_name, os.path.join('.', self.SURVEY_DIR, survey_name+'.txt')))
            return ''
        with open(survey_path, 'r') as f:
            return f.read()

    def handle_ok(self):
        survey_name = self.SURVEY_NAMES[self.survey_idx]
        survey_type = SurveyType.OBS if 'obs' in survey_name else SurveyType.SCS
        survey_path = self._get_survey_file_path()
        tx_maker = TxMakerCore(
            survey_type, survey_path, self.survey_time_offset.get(),
            self.horizon_path.get(), self.horizon_precision.get(),
            self.ray_number.get(), self.save_path.get(),)
        tx_maker.run()
        messagebox.showinfo('Info', 'Completed.')

    def report_callback_exception(self, exc, val, tb):
        self.logger.exception(val)
        err_msg = traceback.format_exception(exc, val, tb)
        err_msg = ''.join(err_msg)
        messagebox.showerror('Internal Error', err_msg)



class SurveyType(Enum):
    """Enumerate class for survey types"""
    SCS = 1
    OBS = 2


class TxMakerCore(object):
    """Create tx.in file from trace-time data exported from the Kingdom Software"""

    LINE_FMT = '%10.3f%10.3f%10.3f%10d'

    def __init__(
            self, survey_type, survey_path, survey_time_offset, horizon_path,
            horizon_precision, ray_number, save_path):
        self.survey_type = survey_type
        self.survey_path = survey_path
        self.survey_time_offset = survey_time_offset
        self.horizon_path = horizon_path
        self.horizon_precision = horizon_precision
        self.ray_number = ray_number
        self.save_path = save_path

    def load_survey_data(self):
        with open(self.survey_path, 'r') as f:
            shot_site = f.readline().strip()
            trace_number_map = np.genfromtxt(f, delimiter=',')
        if not np.all(np.diff(trace_number_map, axis=0) > 0):
            raise ValueError(
                'Invalid Trace-Number vs. X-Offset Table: [%s].'
                'Rows should in order of increasing.' %(self.survey_path))
        return shot_site, trace_number_map

    def load_horizon_data(self):
        return np.genfromtxt(self.horizon_path, delimiter=',', usecols=(1, 2))

    def make_tx_for_obs(self, tx_data, shot_site):
        idx = np.searchsorted(tx_data[:, 0], shot_site)
        res = np.vstack([
            [shot_site, -1, 0, 0],
            tx_data[:idx, :],
            [shot_site, 1, 0, 0],
            tx_data[idx:, :],
            [0, 0, 0, -1],
            ])
        np.savetxt(self.save_path, res, fmt=self.LINE_FMT)

    def make_tx_for_scs(self, tx_data):
        fmt = self.LINE_FMT+'\n'
        with open(self.save_path, 'w') as f:
            for row in tx_data:
                shot_site = row[0]
                f.write(fmt %(shot_site, 1, 0, 0))
                f.write(fmt %tuple(row))
            f.write(fmt %(0, 0, 0, -1))

    def run(self):
        shot_site, trace_number_map = self.load_survey_data()
        horizon_data = self.load_horizon_data()
        trace_number = horizon_data[:, 0:1]
        x = np.interp(trace_number, trace_number_map[:, 0], trace_number_map[:, 1])
        time = horizon_data[:, 1:2] + self.survey_time_offset
        tx_data = np.hstack([x, time, np.ones_like(x)*self.horizon_precision, np.ones_like(x)*self.ray_number])
        obs, scs = SurveyType.OBS, SurveyType.SCS
        if self.survey_type in (obs, obs.name, obs.value, obs.name.lower()):
            shot_site = float(shot_site)
            self.make_tx_for_obs(tx_data, shot_site)
        elif self.survey_type in (scs, scs.name, scs.value, scs.name.lower()):
            self.make_tx_for_scs(tx_data)
        else:
            raise ValueError('Invalid survey type "%r". Support only "obs" and "scs"' %(self.survey_type))


if __name__ == '__main__':
    root = tk.Tk()
    root.title('tx.in maker')
    root.geometry('700x700+200+30')

    # make window resizable
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    # create app
    app = TxMaker(master=root)
    root.report_callback_exception = app.report_callback_exception
    app.grid(padx=0, sticky='nswe')

    app.mainloop()
