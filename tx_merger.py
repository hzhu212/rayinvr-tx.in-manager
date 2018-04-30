import logging
import os
import re
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import traceback

from . import ROOT_DIR


class TxMerger(ttk.Frame):
    """Merge tx.in(s) from several OBS(s) into one tx.in file"""
    def __init__(self, master=None):
        super().__init__(master)
        self.logger = self._get_logger()
        self.init_variables()
        # self.set_custom_style()
        self.create_widgets()
        self.load_all_txins()
        self.tx_merger = TxMergerCore()

    def init_variables(self):
        self.search_path = tk.StringVar()
        self.filter_str = tk.StringVar()
        self.ray_number = tk.IntVar()
        self.enable_ray_number = tk.IntVar()
        self.save_path = tk.StringVar()
        self.search_path.set(os.path.join(ROOT_DIR, 'tx_in'))
        self.enable_ray_number.set(1)
        self.save_path.set(os.path.join(self.search_path.get(), 'undefined_tx.in'))

    def set_custom_style(self):
        s = ttk.Style()
        s.configure('.', font=('Microsoft YaHei UI', 10))
        s.configure('sm.TButton', font=('Microsoft YaHei UI', 8), width=7)

    def create_widgets(self):
        PADX_LG = (15, 15)
        PADY_SM, PADY_LG, PADY_LLG = (5, 0), (10, 0), (20, 0)
        PADY_SM_E, PADY_LG_E, PADY_LLG_E = (5, 5), (10, 10), (20, 20)

        # make frame resizable
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # frame for selecting tx.in(s)
        row1 = ttk.LabelFrame(self, text='Select tx.in(s) for merging')
        IROW_PATH, IROW_FILTER, IROW_LABEL, IROW_BOX = 0, 1, 2, 3
        row1.columnconfigure(0, weight=1)
        row1.columnconfigure(2, weight=1)
        row1.rowconfigure(IROW_BOX, weight=1)
        row1.grid(column=0, padx=PADX_LG, pady=PADY_LG, sticky='nswe')

        # set search path
        path_area = ttk.Frame(row1)
        path_area.grid(row=IROW_PATH, column=0, columnspan=3, pady=PADY_SM, sticky='nswe')
        path_area.columnconfigure(1, weight=1)
        ttk.Label(path_area, text='Search tx.in(s) from: ').grid(row=0, column=0, sticky='nsw')
        ttk.Entry(path_area, textvariable=self.search_path).grid(row=0, column=1, sticky='nswe')
        ttk.Button(path_area, text='Change', command=self.change_search_path)\
            .grid(row=0, column=2, padx=5, sticky='nse')

        # filter
        filter_area = ttk.Frame(row1)
        filter_area.grid(row=IROW_FILTER, column=0, pady=PADY_SM, sticky='nswe')
        filter_area.columnconfigure(1, weight=1)
        ttk.Label(filter_area, text='Filter: ').grid(row=0, column=0, sticky='nsw')
        self.combo_filter = ttk.Combobox(filter_area, width=10, values=tuple(), textvariable=self.filter_str)
        self.combo_filter.grid(row=0, column=1, sticky='nswe')
        self.combo_filter.bind('<Return>', self.filter_txin)
        ttk.Button(filter_area, text='OK', width=5, command=self.filter_txin)\
            .grid(row=0, column=2, sticky='nsw')

        # left listbox: tx.in(s) for selecting
        ttk.Label(row1, text='All tx.in(s) available: ')\
            .grid(row=IROW_LABEL, column=0, pady=PADY_SM ,sticky='nsw')
        left_part = ttk.Frame(row1)
        left_part.rowconfigure(0, weight=1)
        left_part.columnconfigure(0, weight=1)
        left_part.grid(row=IROW_BOX, column=0, pady=PADY_SM_E, sticky='nswe')
        self.left_box = tk.Listbox(left_part, selectmode=tk.EXTENDED)
        y_scroll1 = tk.Scrollbar(left_part, orient=tk.VERTICAL, command=self.left_box.yview)
        y_scroll1.grid(row=0, column=1, sticky='ns')
        self.left_box['yscrollcommand'] = y_scroll1.set
        self.left_box.grid(row=0, column=0, sticky='nswe')

        # right listbox: selected tx.in(s)
        ttk.Label(row1, text='Selected tx.in(s): ')\
            .grid(row=IROW_LABEL, column=2, pady=PADY_SM ,sticky='nsw')
        right_part = ttk.Frame(row1)
        right_part.rowconfigure(0, weight=1)
        right_part.columnconfigure(0, weight=1)
        right_part.grid(row=IROW_BOX, column=2, pady=PADY_SM_E, sticky='nswe')
        self.right_box = tk.Listbox(right_part, selectmode=tk.EXTENDED)
        y_scroll2 = tk.Scrollbar(right_part, orient=tk.VERTICAL, command=self.right_box.yview)
        y_scroll2.grid(row=0, column=1, sticky='ns')
        self.right_box['yscrollcommand'] = y_scroll2.set
        self.right_box.grid(row=0, column=0, sticky='nswe')

        #select button between left and right listbox
        mid_part = ttk.Frame(row1)
        mid_part.rowconfigure(0, weight=1)
        mid_part.rowconfigure(1, weight=1)
        mid_part.grid(row=IROW_BOX, column=1, padx=10, pady=PADY_SM_E, sticky='ns')
        ttk.Button(mid_part, text='Add >>', command=self.add_txins).grid(pady=8, sticky=tk.S)
        ttk.Button(mid_part, text='Drop <<', command=self.rm_txins).grid(pady=8, sticky=tk.N)

        # frame for merging selected tx.in(s)
        row2 = ttk.LabelFrame(self, text='Merge selected tx.in(s)')
        row2.columnconfigure(0, weight=1)
        row2.grid(column=0, padx=PADX_LG, pady=PADY_LG, sticky='nswe')

        # set target ray-group number
        row2_1 = ttk.Frame(row2)
        row2_1.grid(column=0, pady=PADY_SM, sticky='nswe')
        row2_1.columnconfigure(1, weight=1)
        ttk.Checkbutton(
            row2_1, text='Reset ray-group number. If disabled, will keep the original ray-group number defined in source tx.in(s).',
            variable=self.enable_ray_number, command=self.toggle_ray_number,
            ).grid(row=0, column=0, columnspan=2, sticky='nsw')
        self.ray_number_label = ttk.Label(row2_1, text='    Target ray-group number: ')
        self.ray_number_label.grid(row=1, column=0, sticky='nsw')
        self.ray_number_box = tk.Spinbox(row2_1, state='readonly', from_=1, to=1e3, increment=1, width=4, textvariable=self.ray_number)
        self.ray_number_box.grid(row=1, column=1, sticky='nsw')

        # set path for target tx.in file
        row2_2 = ttk.Frame(row2)
        row2_2.grid(column=0, pady=PADY_SM_E, sticky='nswe')
        row2_2.columnconfigure(1, weight=1)
        ttk.Label(row2_2, text='Save to: ').grid(row=0, column=0, sticky='nsw')
        entry = ttk.Entry(row2_2, textvariable=self.save_path)
        entry.grid(row=0, column=1, sticky='nswe')
        entry.bind('<Return>', self.handle_ok)
        ttk.Button(row2_2, text='Select', command=self.select_save_path)\
            .grid(row=0, column=2, sticky='nse')

        # command buttons
        row_cmd = ttk.Frame(self)
        row_cmd.rowconfigure(0, weight=1)
        row_cmd.columnconfigure(0, weight=1)
        row_cmd.grid(column=0, padx=PADX_LG, pady=PADY_LLG_E, sticky='nswe')
        ttk.Button(row_cmd, text='OK', command=self.handle_ok).grid(row=0, column=0)


    def _get_logger(self):
        logger = logging.getLogger('TxMerger')
        logger.setLevel(logging.DEBUG)
        LOG_FILE_PATH = os.path.join(ROOT_DIR, 'log', 'tx_merger.log')
        file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf8')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s: %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

    def change_search_path(self):
        p = filedialog.askdirectory(
            initialdir=self.search_path.get(),
            parent=self,
            title='Change Searching Path As')
        p = p.strip()
        if p:
            self.search_path.set(os.path.normpath(p))
            self.load_all_txins()

    def _get_all_txins(self):
        search_path = self.search_path.get()
        return [s for s in os.listdir(search_path) if s.endswith('tx.in')]

    def load_all_txins(self):
        self.left_box.delete(0, self.left_box.size())
        self.left_box.insert(tk.END, *self._get_all_txins())

    def filter_txin(self, event=None):
        filter_str = self.filter_str.get()
        # add filter string to Combobox
        MAX_HISTORY = 10
        if filter_str != '':
            lst = list(self.combo_filter['values'])
            if filter_str in lst:
                lst.pop(lst.index(filter_str))
            lst.insert(0, filter_str)
            lst = lst[:MAX_HISTORY]
            self.combo_filter.config(values=tuple(lst))

        # filter tx.in(s)
        self.load_all_txins()
        for i in reversed(range(self.left_box.size())):
            file_name = self.left_box.get(i)
            if filter_str not in file_name:
                self.left_box.delete(i)

    def add_txins(self):
        """add tx.in(s) from left listbox to right listbox"""
        left_selected = [self.left_box.get(i) for i in self.left_box.curselection()]
        right_all = self.right_box.get(0, self.right_box.size())
        check_ins = filter(lambda s: s not in right_all, left_selected)
        self.right_box.insert(tk.END, *check_ins)

    def rm_txins(self):
        """remove tx.in(s) from right listbox"""
        for i in sorted(self.right_box.curselection(), reverse=True):
            self.right_box.delete(i)

    def toggle_ray_number(self):
        if self.ray_number_box['state'] != tk.DISABLED:
            self.ray_number_label.config(state=tk.DISABLED)
            self.ray_number_box.config(state=tk.DISABLED)
        else:
            self.ray_number_label.config(state=tk.NORMAL)
            self.ray_number_box.config(state=tk.NORMAL)

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

    def _start_merge(self):
        ok = True
        dest_path = self.save_path.get()
        if os.path.isfile(dest_path):
            ok = messagebox.askquestion(
                title='Confirm Save As',
                message='%s already exists.\nDo you want to replace it?' %os.path.split(dest_path)[1],
                icon=messagebox.WARNING,
                parent=self)
        if not ok:
            return
        src_paths = [os.path.join(ROOT_DIR, 'tx_in', s) for s in self.right_box.get(0, self.right_box.size())]
        ray_number = self.ray_number.get() if self.enable_ray_number.get() else None
        self.tx_merger.run(src_paths, dest_path, ray_number)

    def handle_ok(self, event=None):
        if self.right_box.size() == 0:
            messagebox.showerror('Error', 'You hasn\'t select any tx.in(s)')
            return
        try:
            self._start_merge()
        except Exception as e:
            self.logger.exception(e)
            messagebox.showerror('Error', 'Failed merging tx.in(s).\nPlease read log for detailed error message.')
        else:
            messagebox.showinfo('Info', 'Merge complete.')

    def report_callback_exception(self, exc, val, tb):
        self.logger.exception(val)
        err_msg = traceback.format_exception(exc, val, tb)
        err_msg = ''.join(err_msg)
        messagebox.showerror('Internal Error', err_msg)


class TxMergerCore(object):
    """Merge tx.in(s) from several OBS(s) into one tx.in file"""

    TX_ENDING_LINE = '%10.3f%10.3f%10.3f%10d\n' %(0,0,0,-1)

    def __init__(self):
        super().__init__()

    def run(self, src_paths, target_path, ray_number=None):
        with open(target_path, 'w') as fw:
            for file in src_paths:
                string = ''
                with open(file, 'r') as fr:
                    string = fr.read()
                if not string.strip():
                    raise ValueError('Empty tx.in file: %s' %file)
                string = self.remove_tx_ending_line(string)
                if ray_number is not None:
                    if not isinstance(ray_number, int):
                        raise ValueError('Invalid ray_number: %r' %ray_number)
                    string = self.reset_ray_number(string, ray_number)
                fw.write(string)
            fw.write(self.TX_ENDING_LINE)

    def remove_tx_ending_line(self, string):
        string = string.rstrip()
        if not string.endswith('-1'):
            return string + '\n'
        idx = string.rfind('\n')
        if idx == -1:
            raise ValueError('Invalid tx.in format')
        return string[:idx+1]

    def reset_ray_number(self, string, ray_number):
        return re.sub('\s+[1-9]\d*\n', '%10d\n'%ray_number, string)



if __name__ == '__main__':
    root = tk.Tk()
    root.title('tx.in merger')
    root.geometry('700x700+200+30')

    # make window resizable
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    # create app
    app = TxMerger(master=root)
    root.report_callback_exception = app.report_callback_exception
    app.grid(padx=0, sticky='nswe')

    app.mainloop()
