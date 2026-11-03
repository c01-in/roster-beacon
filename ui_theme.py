"""Desktop control tokens and DPI-aware, fixed-geometry dark styles."""
import ctypes
from tkinter import PhotoImage,ttk

BG='#121820'
SIDEBAR='#10151C'
PANEL='#1A222D'
RAISED='#263343'
BORDER='#354456'
TEXT='#F0F3F7'
MUTED='#B2BFCE'
LIME='#CAEF73'
CYAN='#70CFCB'


def enable_dpi_awareness():
    """Source launches match the system-aware manifest used by frozen builds."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError,OSError):
        try:ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError,OSError):pass


def ui_scale(root):
    return float(root.tk.call('tk','scaling'))/(96/72)


def configure_styles(root):
    from i18n import language
    font='Microsoft YaHei UI' if language()=='zh-CN' else 'Segoe UI'
    px=lambda value:round(value*ui_scale(root))
    style=ttk.Style(root)
    style.theme_use('clam')
    style.configure('.',background=BG,foreground=TEXT,font=(font,11),bordercolor=BORDER,lightcolor=BORDER,darkcolor=BORDER)
    for name,color in [('TFrame',BG),('Card.TFrame',PANEL)]:style.configure(name,background=color)
    style.configure('TLabel',background=BG,foreground=TEXT)
    root.option_add('*TEntry.font',(font,11))
    root.option_add('*TCombobox.font',(font,11))
    style.configure('Muted.TLabel',foreground=MUTED)
    style.configure('Section.TLabel',font=(font,11,'bold'))
    style.configure('Page.TLabel',font=(font,16,'bold'))
    style.configure('Card.TLabel',background=PANEL)
    style.configure('CardStrong.TLabel',background=PANEL,font=(font,11,'bold'))
    style.configure('CardMuted.TLabel',background=PANEL,foreground=MUTED)
    style.configure('Value.TLabel',background=PANEL,font=(font,16,'bold'))
    # All button states share exactly the same layout, font, padding and border.
    style.layout('TButton',[('Button.border',{'sticky':'nswe','children':[
        ('Button.padding',{'sticky':'nswe','children':[('Button.label',{'sticky':'nswe'})]})]})])
    style.configure('TButton',padding=(px(12),px(7)),background=RAISED,foreground=TEXT,
        font=(font,11),borderwidth=px(1),relief='flat',bordercolor=BORDER,lightcolor=BORDER,darkcolor=BORDER)
    for name,base,hover,pressed,ink in [('TButton',RAISED,'#304257','#1D2A3A',TEXT),
        ('Primary.TButton',LIME,'#DAF6A4','#B2D663',SIDEBAR),('Quiet.TButton',BG,PANEL,RAISED,TEXT)]:
        style.configure(name,background=base,foreground=ink)
        style.map(name,background=[('disabled','#202A36'),('pressed',pressed),('active',hover),('!disabled',base)],
            foreground=[('disabled','#8C9AAA'),('!disabled',ink)],
            bordercolor=[('focus',CYAN),('!focus',BORDER if name!='Quiet.TButton' else BG)],
            lightcolor=[('focus',CYAN),('!focus',BORDER if name!='Quiet.TButton' else BG)],
            darkcolor=[('focus',CYAN),('!focus',BORDER if name!='Quiet.TButton' else BG)])
    style.configure('TEntry',fieldbackground=SIDEBAR,foreground=TEXT,insertcolor=CYAN,padding=(px(8),px(7)),borderwidth=px(1))
    style.map('TEntry',fieldbackground=[('disabled',PANEL),('!disabled',SIDEBAR)],foreground=[('disabled',MUTED)],
        bordercolor=[('focus',CYAN),('!focus',BORDER)],lightcolor=[('focus',CYAN),('!focus',BORDER)],darkcolor=[('focus',CYAN),('!focus',BORDER)])
    style.configure('TCombobox',font=(font,11),fieldbackground=SIDEBAR,background=RAISED,foreground=TEXT,
        arrowcolor=TEXT,padding=(px(8),px(7)),arrowsize=px(14),borderwidth=px(1))
    style.map('TCombobox',fieldbackground=[('disabled',PANEL),('readonly',SIDEBAR)],
        background=[('active',RAISED),('!active',RAISED)],foreground=[('disabled',MUTED),('readonly',TEXT)],
        selectbackground=[('readonly',SIDEBAR)],selectforeground=[('readonly',TEXT)],
        bordercolor=[('focus',CYAN),('!focus',BORDER)],lightcolor=[('focus',CYAN),('!focus',BORDER)],darkcolor=[('focus',CYAN),('!focus',BORDER)],
        arrowcolor=[('disabled',MUTED),('!disabled',TEXT)])
    # Original fixed-size checkbox indicators replace clam's white native states.
    if not hasattr(root,'_check_images'):
        images=[]
        size=px(16);edge=max(1,px(1))
        for selected in (False,True):
            image=PhotoImage(master=root,width=size,height=size)
            image.put(CYAN if selected else MUTED,to=(0,0,size,size))
            image.put(CYAN if selected else SIDEBAR,to=(edge,edge,size-edge,size-edge))
            if selected:
                for x in range(px(4),px(7)):
                    y=x+px(4);image.put(SIDEBAR,to=(x,y,x+edge+1,y+edge+1))
                for x in range(px(7),px(13)):
                    y=px(18)-x;image.put(SIDEBAR,to=(x,y,x+edge+1,y+edge+1))
            images.append(image)
        root._check_images=images
        style.element_create('Sync.Check.indicator','image',images[0],('selected',images[1]),width=size+px(8),height=size,sticky='w')
    style.layout('TCheckbutton',[('Checkbutton.padding',{'sticky':'nswe','children':[
        ('Sync.Check.indicator',{'side':'left','sticky':'w'}),('Checkbutton.label',{'side':'left','sticky':'w'})]})])
    style.configure('TCheckbutton',background=BG,foreground=TEXT,padding=(0,px(5)),indicatormargin=(0,0,px(8),0))
    style.map('TCheckbutton',background=[('focus',RAISED),('active',PANEL),('!active',BG)],foreground=[('disabled',MUTED),('!disabled',TEXT)])
    style.configure('TSeparator',background=BORDER)
    style.configure('Thin.Horizontal.TProgressbar',background=CYAN,troughcolor=PANEL,thickness=px(3),borderwidth=0,lightcolor=PANEL,darkcolor=PANEL)
    style.layout('Vertical.TScrollbar',[('Vertical.Scrollbar.trough',{'sticky':'ns','children':[
        ('Vertical.Scrollbar.thumb',{'sticky':'nswe','expand':'1'})]})])
    style.configure('Vertical.TScrollbar',background=BORDER,troughcolor=PANEL,borderwidth=0,
        width=px(10),arrowsize=px(10),bordercolor=PANEL,lightcolor=BORDER,darkcolor=BORDER)
    style.map('Vertical.TScrollbar',background=[('active','#53677E'),('!active',BORDER)])
    for key,value in [('background',PANEL),('foreground',TEXT),('selectBackground',RAISED),('selectForeground',TEXT),
        ('borderWidth',0),('selectBorderWidth',0),('highlightThickness',0),('font',(font,11))]:
        root.option_add('*TCombobox*Listbox.'+key,value)


def dark_titlebar(window):
    try:
        window.update_idletasks()
        hwnd=ctypes.windll.user32.GetParent(window.winfo_id())
        value=ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd,20,ctypes.byref(value),ctypes.sizeof(value))
    except (OSError,AttributeError):pass


def draw_ball(canvas,size):
    """Small original basketball mark; no hero or decorative content panel."""
    p=lambda value:value*size/22
    canvas.create_oval(p(2),p(2),p(20),p(20),outline=CYAN,width=max(1,p(1.2)))
    canvas.create_line(p(5),p(4),p(17),p(18),fill=CYAN,width=max(1,p(1)))
    canvas.create_line(p(4),p(17),p(18),p(5),fill=CYAN,width=max(1,p(1)))
    canvas.create_arc(p(-4),p(4),p(13),p(23),start=315,extent=150,style='arc',outline=CYAN,width=max(1,p(1)))
