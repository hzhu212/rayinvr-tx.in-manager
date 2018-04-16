import logging
import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import traceback

from . import ROOT_DIR


class TxMaker(ttk.Frame):
    """tx.in maker"""
    def __init__(self, master=None):
        super().__init__(master)
        self.logger = self._get_logger()
        self.create_widgets()

    def create_widgets(self):
        # make window resizable
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # test widget
        ttk.Label(self, text='tx.in maker').grid()

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

    def report_callback_exception(self, exc, val, tb):
        self.logger.exception(val)
        err_msg = traceback.format_exception(exc, val, tb)
        err_msg = ''.join(err_msg)
        messagebox.showerror('Internal Error', err_msg)


if __name__ == '__main__':
    root = tk.Tk()
    root.title('tx.in maker')

    # make window resizable
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    # create app
    app = TxMaker(master=root)
    root.report_callback_exception = app.report_callback_exception
    app.grid(sticky=tk.N+tk.S+tk.E+tk.W)

    app.mainloop()
