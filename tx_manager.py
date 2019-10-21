import logging
import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import traceback

from __init__ import ROOT_DIR
from tx_maker import TxMaker
from tx_merger import TxMerger


class TxManager(ttk.Frame):
    """tx.in manager"""
    def __init__(self, master=None):
        super().__init__(master)
        self.logger = self._get_logger()
        # self.set_custom_style()
        self.create_widgets()

    def set_custom_style(self):
        s = ttk.Style()
        s.configure('.', font=('Microsoft YaHei UI', 10))
        s.configure('sm.TButton', font=('Microsoft YaHei UI', 8), width=7)
        s.configure('TLabelFrame', padx=20)

    def create_widgets(self):
        # make frame resizable
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # create a Notebook widget to contain several panels
        notebook = ttk.Notebook(self)
        notebook.grid(row=0, column=0, sticky='nswe')
        tx_maker = TxMaker(notebook)
        notebook.add(tx_maker, text=' Create tx.in ', sticky='nswe')
        tx_merger = TxMerger(notebook)
        notebook.add(tx_merger, text=' Merge tx.in ', sticky='nswe')

    def _get_logger(self):
        logger = logging.getLogger('TxManager')
        logger.setLevel(logging.DEBUG)
        LOG_FILE_PATH = os.path.join(ROOT_DIR, 'log', 'tx_manager.log')
        file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf8')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s: %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

    def report_callback_exception(self, exc, val, tb):
        self.logger.exception(val)
        err_msg = traceback.format_exception(exc, val, tb)
        err_msg = ''.join(err_msg)
        messagebox.showerror('Internal Error', err_msg)


if __name__ == '__main__':
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)

    root = tk.Tk()
    root.title('tx.in manager')
    root.geometry('700x700+200+30')

    # make window resizable
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    # create app
    app = TxManager(master=root)
    root.report_callback_exception = app.report_callback_exception
    app.grid(sticky='nswe')

    app.mainloop()
