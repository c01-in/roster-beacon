"""Dark bilingual modal dialogs, dispatched safely to the GUI thread."""
import threading
import tkinter as tk
from tkinter import ttk

from i18n import language,localize,tr
from ui_theme import PANEL,TEXT,configure_styles,dark_titlebar,enable_dpi_awareness,ui_scale

_dispatcher=None


def configure_dispatcher(callback):
    global _dispatcher
    _dispatcher=callback


def themed_dialog(parent,title,text,confirm=False,accept_label=None):
    own_root=parent is None
    if own_root:
        enable_dpi_awareness()
        parent=tk.Tk()
        parent.withdraw()
        configure_styles(parent)
    dialog=tk.Toplevel(parent)
    px=lambda value:round(value*ui_scale(parent))
    dialog.withdraw()
    dialog.title(localize(title))
    dialog.configure(background=PANEL)
    dialog.resizable(False,False)
    if not own_root:
        dialog.transient(parent)
    result=[False]
    body=ttk.Frame(dialog,style='Card.TFrame',padding=px(24))
    body.pack(fill='both',expand=True)
    font='Microsoft YaHei UI' if language()=='zh-CN' else 'Segoe UI'
    label=ttk.Label(body,text=localize(text),style='Card.TLabel',wraplength=px(520),justify='left',font=(font,11))
    label.pack(anchor='w',pady=(0,px(24)))
    buttons=ttk.Frame(body,style='Card.TFrame')
    buttons.pack(fill='x')
    def done(value):
        result[0]=value
        dialog.destroy()
    if confirm:
        ttk.Button(buttons,text=tr('取消'),command=lambda:done(False)).pack(side='right')
    primary=ttk.Button(buttons,text=accept_label or tr('确定'),style='Primary.TButton',command=lambda:done(True))
    primary.pack(side='right',padx=(0,px(10)) if confirm else 0)
    dialog.protocol('WM_DELETE_WINDOW',lambda:done(False))
    dialog.bind('<Escape>',lambda event:done(False))
    dialog.bind('<Return>',lambda event:done(True))
    dialog.update_idletasks()
    width=max(px(400),dialog.winfo_reqwidth())
    limit=dialog.winfo_screenheight()-px(80)
    height=min(dialog.winfo_reqheight(),limit)
    if dialog.winfo_reqheight()>limit:
        label.destroy()
        content=ttk.Frame(body,style='Card.TFrame',height=max(px(100),limit-px(72)-buttons.winfo_reqheight()))
        content.pack(fill='both',expand=True,before=buttons,pady=(0,px(24)))
        content.pack_propagate(False)
        scroll=ttk.Scrollbar(content,orient='vertical');scroll.pack(side='right',fill='y')
        copy=tk.Text(content,wrap='word',background=PANEL,foreground=TEXT,font=(font,11),
                     relief='flat',highlightthickness=0,borderwidth=0,yscrollcommand=scroll.set)
        copy.pack(fill='both',expand=True);scroll.configure(command=copy.yview)
        copy.insert('1.0',localize(text));copy.configure(state='disabled')
    x=max(0,(dialog.winfo_screenwidth()-width)//2)
    y=max(0,(dialog.winfo_screenheight()-height)//2)
    dialog.geometry(f'{width}x{height}+{x}+{y}')
    dialog.attributes('-topmost',True)
    dialog.deiconify()
    dark_titlebar(dialog)
    dialog.grab_set()
    dialog.focus_force()
    primary.focus_set()
    parent.wait_window(dialog)
    if own_root:
        parent.destroy()
    return result[0]


def show_dialog(title,text,confirm=False,accept_label=None):
    if _dispatcher is not None and threading.current_thread() is not threading.main_thread():
        return _dispatcher(title,text,confirm,accept_label)
    return themed_dialog(tk._default_root,title,text,confirm,accept_label)
