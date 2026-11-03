"""Bilingual desktop utility; native game operations run in a worker."""
from __future__ import annotations

import contextlib
from datetime import datetime
import json
import os
from pathlib import Path
import queue
import threading
import traceback
import tkinter as tk
from tkinter import filedialog, ttk

from app_runtime import (APP_NAME,RESOURCES,VERSION,config_path,load_settings,path_setting,
                         recommended_data_dir,save_settings,validate_settings)
from dialogs import configure_dispatcher,show_dialog,themed_dialog
from i18n import language,localize,set_language,tr
from ui_theme import BG,PANEL,SIDEBAR,RAISED,BORDER,TEXT,MUTED,LIME,CYAN,configure_styles,dark_titlebar,enable_dpi_awareness,ui_scale,draw_ball


class ReadonlyCombobox(ttk.Combobox):
    """Closed selectors keep their value on wheel; popup lists scroll natively."""
    def __init__(self,parent,**options):
        options.setdefault('state','readonly')
        super().__init__(parent,**options)
        self.bind('<MouseWheel>',lambda event:'break')


class LogWriter:
    def __init__(self,messages,file):
        self.messages,self.file=messages,file
    def write(self,text):
        if text:
            self.messages.put(('log',localize(text)))
            self.file.write(text)
        return len(text)
    def flush(self):
        self.file.flush()


class Application(tk.Tk):
    def __init__(self,open_settings=False,auto_launch=False):
        enable_dpi_awareness()
        super().__init__()
        self.scale=ui_scale(self)
        self.px=lambda value:round(value*self.scale)
        self.settings=load_settings()
        set_language(os.environ.get('NBA_ROSTER_SYNC_LANGUAGE',self.settings.get('language','auto')))
        self.title(APP_NAME+' · '+VERSION)
        width=min(self.px(1060),self.winfo_screenwidth()-self.px(70))
        height=min(self.px(710),self.winfo_screenheight()-self.px(90))
        self.geometry(f'{width}x{height}+{max(0,(self.winfo_screenwidth()-width)//2)}+{max(0,(self.winfo_screenheight()-height)//2)}')
        self.minsize(self.px(900),self.px(590))
        self.configure(background=BG)
        self.iconbitmap(default=str(RESOURCES/'assets/app.ico'))
        self.messages=queue.Queue()
        self.busy=False
        self.log_history=''
        self._settings_wheel_tag='RosterSettingsWheel'+str(id(self))
        self._settings_wheel_delta=0
        self.setup_candidates=[]
        self.bind_class(self._settings_wheel_tag,'<MouseWheel>',self.scroll_settings)
        configure_dispatcher(self.dialog_from_worker)
        self.build_ui()
        self.protocol('WM_DELETE_WINDOW',self.close)
        dark_titlebar(self)
        self.after(80,self.consume)
        if open_settings or not self.configured():
            self.show_page('settings')
        elif auto_launch:
            self.after(300,lambda:self.update(True))

    def configured(self):
        return bool(self.settings.get('game_executable') and self.settings.get('sync_directory') and self.settings.get('manifest_name')
                    and Path(self.settings.get('baseline_directory',''),self.settings['manifest_name']).is_file())

    def build_ui(self):
        configure_styles(self)
        self.ui_font='Microsoft YaHei UI' if language()=='zh-CN' else 'Segoe UI'
        px=self.px
        self.job_buttons=[]
        self.shell=tk.Frame(self,background=BG)
        self.shell.pack(fill='both',expand=True)
        sidebar=tk.Frame(self.shell,background=SIDEBAR,width=px(184))
        sidebar.pack(side='left',fill='y')
        sidebar.pack_propagate(False)
        tk.Frame(self.shell,background=BORDER,width=px(1)).pack(side='left',fill='y')
        brand=tk.Frame(sidebar,background=SIDEBAR,height=px(60))
        brand.pack(fill='x',padx=px(16));brand.pack_propagate(False)
        ball=tk.Canvas(brand,width=px(22),height=px(22),background=SIDEBAR,highlightthickness=0)
        ball.pack(side='left',padx=(0,px(9)))
        draw_ball(ball,px(22))
        tk.Label(brand,text=APP_NAME,background=SIDEBAR,foreground=TEXT,font=(self.ui_font,11,'bold')).pack(side='left')
        self.nav={}
        for page,label in [('home','更新名单'),('settings','设置'),('recovery','维护')]:
            row=tk.Frame(sidebar,background=SIDEBAR,height=px(40))
            row.pack(fill='x',padx=px(8),pady=px(2));row.pack_propagate(False)
            marker=tk.Frame(row,background=SIDEBAR,width=px(3))
            marker.pack(side='left',fill='y',pady=px(10))
            button=tk.Button(row,text=tr(label),command=lambda name=page:self.show_page(name),anchor='w',
                background=SIDEBAR,foreground=MUTED,activebackground=RAISED,activeforeground=TEXT,
                font=(self.ui_font,11),relief='flat',borderwidth=0,highlightthickness=px(1),
                highlightbackground=SIDEBAR,highlightcolor=CYAN,padx=px(12),pady=0,cursor='hand2',takefocus=True)
            button.pack(side='left',fill='both',expand=True)
            button.bind('<Enter>',lambda e,name=page:self.paint_nav(name,hover=True))
            button.bind('<Leave>',lambda e,name=page:self.paint_nav(name))
            self.nav[page]=(row,marker,button)
            self.bind('<Control-Key-'+str(len(self.nav))+'>',lambda e,name=page:self.show_page(name))
        bottom=tk.Frame(sidebar,background=SIDEBAR)
        bottom.pack(side='bottom',fill='x',padx=px(16),pady=px(18))
        tk.Label(bottom,text=tr('语言'),background=SIDEBAR,foreground=MUTED,font=(self.ui_font,10)).pack(anchor='w',pady=(0,px(6)))
        self.language_choices={tr('跟随系统'):'auto','中文':'zh-CN','English':'en-US'}
        current=self.settings.get('language','auto')
        self.language_var=tk.StringVar(value=next((k for k,v in self.language_choices.items() if v==current),tr('跟随系统')))
        self.language_box=ReadonlyCombobox(bottom,textvariable=self.language_var,values=list(self.language_choices),width=14)
        self.language_box.pack(fill='x')
        self.language_box.bind('<<ComboboxSelected>>',self.change_language)
        tk.Label(bottom,text=VERSION,background=SIDEBAR,foreground=MUTED,font=(self.ui_font,10)).pack(anchor='w',pady=(px(12),0))
        workspace=ttk.Frame(self.shell,padding=(px(24),px(20)))
        workspace.pack(side='left',fill='both',expand=True)
        self.pages_host=ttk.Frame(workspace)
        self.pages_host.pack(fill='both',expand=True)
        self.pages_host.rowconfigure(0,weight=1);self.pages_host.columnconfigure(0,weight=1)
        self.pages={name:ttk.Frame(self.pages_host) for name in self.nav}
        for page in self.pages.values():page.grid(row=0,column=0,sticky='nsew')
        self.home=self.pages['home'];self.setup_scroll=self.pages['settings'];self.about=self.pages['recovery']
        self.make_home();self.make_settings();self.make_about()
        self.progress=ttk.Progressbar(workspace,mode='indeterminate',style='Thin.Horizontal.TProgressbar')
        tk.Frame(workspace,background=BORDER,height=px(1)).pack(fill='x',pady=(px(14),px(10)))
        footer=ttk.Frame(workspace);footer.pack(fill='x')
        self.status=tk.StringVar(value=tr('就绪'))
        ttk.Label(footer,textvariable=self.status,style='Muted.TLabel').pack(side='left')
        self.show_page('home')

    def paint_nav(self,page,hover=False):
        row,marker,button=self.nav[page]
        selected=page==getattr(self,'page_id','home')
        background=RAISED if selected or hover else SIDEBAR
        row.configure(background=background)
        marker.configure(background=LIME if selected else background)
        button.configure(background=background,highlightbackground=background,foreground=TEXT if selected or hover else MUTED)

    def show_page(self,page):
        self.page_id=page
        self._settings_wheel_delta=0
        self.pages[page].tkraise()
        for name in self.nav:self.paint_nav(name)

    def change_language(self,event=None):
        if self.busy:return
        choice=self.language_choices[self.language_var.get()]
        pending={k:v.get() for k,v in self.vars.items()}
        team_id=self.team_choices[self.team.get()]
        show,allow=self.show_schedule.get(),self.allow_missing.get()
        source,reimport,advanced=self.baseline_source.get(),self.reimport.get(),self.advanced_open
        page=self.page_id
        scroll_position=self.settings_canvas.yview()[0]
        updated=load_settings();updated['language']=choice;save_settings(updated)
        self.settings['language']=choice
        os.environ.pop('NBA_ROSTER_SYNC_LANGUAGE',None)
        set_language(choice)
        self.shell.destroy();self.build_ui()
        for key,value in pending.items():self.vars[key].set(value)
        self.read_manifests(quiet=True)
        self.baseline_source.set(source);self.reimport.set(reimport)
        if advanced:self.toggle_advanced()
        self.refresh_roster_choices()
        self.team.set(next(k for k,v in self.team_choices.items() if v==team_id))
        self.show_schedule.set(show);self.allow_missing.set(allow)
        self.show_page(page)
        self.settings_canvas.update_idletasks()
        self.settings_canvas.yview_moveto(scroll_position)

    def button(self,parent,text,command,**options):
        button=ttk.Button(parent,text=tr(text),command=command,**options)
        self.job_buttons.append(button)
        return button

    def page_header(self,parent,title):
        header=ttk.Frame(parent);header.pack(fill='x',pady=(0,self.px(20)))
        ttk.Label(header,text=tr(title),style='Page.TLabel').pack(side='left')
        return header

    def make_home(self):
        px=self.px
        header=self.page_header(self.home,'更新名单')
        self.button(header,'更新并启动',lambda:self.update(True),style='Primary.TButton').pack(side='right')
        self.button(header,'仅更新名单',lambda:self.update(False)).pack(side='right',padx=(px(10),px(10)))
        connection=ttk.Frame(self.home,style='Card.TFrame',padding=px(16))
        connection.pack(fill='x')
        self.summary=tk.StringVar()
        self.game_name=tk.StringVar()
        ttk.Label(connection,textvariable=self.game_name,style='CardStrong.TLabel').pack(anchor='w')
        summary=ttk.Label(connection,textvariable=self.summary,style='CardMuted.TLabel',justify='left')
        summary.pack(fill='x',pady=(px(8),0))
        summary.bind('<Configure>',lambda e:summary.configure(wraplength=max(1,e.width)))
        ttk.Label(connection,text=tr('仅支持 NBA 2K27 · Windows x64 · 快速比赛'),style='CardMuted.TLabel').pack(anchor='w',pady=(px(8),0))
        section=ttk.Frame(self.home);section.pack(fill='x',pady=(px(20),px(10)))
        ttk.Label(section,text=tr('上次更新'),style='Section.TLabel').pack(side='left')
        self.last_sync_text=tk.StringVar(value=tr('尚未同步'))
        ttk.Label(section,textvariable=self.last_sync_text,style='Muted.TLabel').pack(side='right')
        metrics=ttk.Frame(self.home,style='Card.TFrame',padding=px(16));metrics.pack(fill='x')
        self.metrics={}
        for slot,(key,label) in enumerate([('teams','已更新球队'),('players','已更新来源球员'),('injuries','伤病与停赛')]):
            metrics.columnconfigure(slot,weight=1,uniform='metric')
            cell=ttk.Frame(metrics,style='Card.TFrame')
            cell.grid(row=0,column=slot,sticky='ew',padx=(px(16) if slot else 0,0))
            ttk.Label(cell,text=tr(label),style='CardMuted.TLabel').pack(anchor='w')
            value=tk.StringVar(value='—');self.metrics[key]=value
            ttk.Label(cell,textvariable=value,style='Value.TLabel').pack(anchor='w',pady=(px(6),0))
        coverage=ttk.Frame(self.home);coverage.pack(fill='x',pady=(px(8),0))
        self.coverage_status=tk.StringVar(value=tr('尚无更新覆盖记录'))
        self.coverage_button=ttk.Button(coverage,text=tr('查看更新与回退'),command=self.show_coverage_details,style='Quiet.TButton',state='disabled')
        self.coverage_button.pack(side='right')
        coverage_label=ttk.Label(coverage,textvariable=self.coverage_status,style='Muted.TLabel')
        coverage_label.pack(side='left',fill='x',expand=True,padx=(0,px(8)))
        coverage_label.bind('<Configure>',lambda e:coverage_label.configure(wraplength=max(1,e.width)))
        logbar=ttk.Frame(self.home);logbar.pack(fill='x',pady=(px(16),px(8)))
        ttk.Label(logbar,text=tr('运行日志'),style='Section.TLabel').pack(side='left')
        self.button(logbar,'打开日志目录',self.open_data,style='Quiet.TButton').pack(side='right')
        console=tk.Frame(self.home,background=BORDER,padx=px(1),pady=px(1))
        console.pack(fill='both',expand=True)
        self.log=tk.Text(console,wrap='word',height=5,font=(self.ui_font,11),state='disabled',
            background=PANEL,foreground=TEXT,insertbackground=CYAN,selectbackground=RAISED,selectforeground=TEXT,
            relief='flat',borderwidth=0,highlightthickness=0,padx=px(12),pady=px(10))
        scroll=ttk.Scrollbar(console,orient='vertical',command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y');self.log.pack(side='left',fill='both',expand=True)
        self.empty_log=not bool(self.log_history)
        self.log.configure(state='normal')
        self.log.tag_configure('placeholder',foreground=MUTED)
        self.log.insert('end',localize(self.log_history) if self.log_history else tr('本次运行尚无日志。'),'placeholder' if self.empty_log else ())
        self.log.configure(state='disabled')
        self.refresh_summary()

    def refresh_summary(self):
        s=self.settings
        self.missing_players=[]
        self.fallback_teams=[]
        self.skipped_mapped=[]
        self.coverage_button.configure(state='disabled')
        if not self.configured():
            self.game_name.set(tr('尚未配置游戏'))
            self.summary.set(tr('请到设置中选择游戏和 SYNC 目录，并导入基准。'))
        else:
            mode='Steam' if s['launch_mode']=='steam' else tr('直接启动')
            self.game_name.set(Path(s['game_executable']).stem+'  ·  '+mode)
            self.summary.set(tr('名单目录：{path}',path=s['sync_directory']))
        state=path_setting(s,'data_directory')/'last_sync.json'
        if state.is_file():
            try:
                data=json.loads(state.read_text('utf-8'))
                self.missing_players=data.get('missing',[])
                self.fallback_teams=data.get('fallback_teams',[])
                self.skipped_mapped=data.get('skipped_mapped_players',[])
                if self.fallback_teams:
                    self.coverage_status.set(tr('上次更新：{teams} 队使用回退，{players} 名来源球员未匹配。',teams=len(self.fallback_teams),players=len(self.missing_players)))
                    self.coverage_button.configure(state='normal')
                elif self.missing_players:
                    self.coverage_status.set(tr('上次更新：{count} 名球员未匹配，已同步其余球员。',count=len(self.missing_players)))
                    self.coverage_button.configure(state='normal')
                else:self.coverage_status.set(tr('上次更新：已匹配全部来源球员。'))
                self.metrics['teams'].set(str(len(data['affected_teams']) if 'affected_teams' in data else data['team_count'])+' / 30')
                self.metrics['players'].set(f'{data["players"]} / {data["source_players"]}')
                self.metrics['injuries'].set(str(len(data['injuries'])))
                stamp=datetime.fromisoformat(data['fetched_at']).astimezone().strftime('%Y-%m-%d %H:%M')
                self.last_sync_text.set(stamp)
            except (OSError,KeyError,ValueError):pass

    def make_settings(self):
        px=self.px
        header=self.page_header(self.setup_scroll,'设置')
        self.button(header,'自动查找游戏',self.find_steam).pack(side='right')
        ttk.Label(self.setup_scroll,text=tr('仅支持 NBA 2K27 · Windows x64 · 快速比赛'),style='Muted.TLabel').pack(anchor='w',pady=(0,px(12)))
        savebar=ttk.Frame(self.setup_scroll);savebar.pack(side='bottom',fill='x',pady=(px(12),0))
        self.button(savebar,'保存并开始使用',self.save,style='Primary.TButton').pack(side='right')
        keys=('game_executable','sync_directory','manifest_name','launch_mode','steam_app_id','data_directory','cache_directory','baseline_directory','compatibility_profile')
        self.vars={key:tk.StringVar(value=str(self.settings.get(key,''))) for key in keys}
        self.baseline_source=tk.StringVar()
        self.reimport=tk.BooleanVar(value=False)
        self.advanced_open=False
        viewport=ttk.Frame(self.setup_scroll);viewport.pack(fill='both',expand=True)
        self.settings_canvas=tk.Canvas(viewport,highlightthickness=0,background=BG)
        canvas=self.settings_canvas
        scrollbar=ttk.Scrollbar(viewport,orient='vertical',command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True)
        self.setup=ttk.Frame(canvas,padding=(0,0,px(12),0))
        window=canvas.create_window(0,0,window=self.setup,anchor='nw')
        self.setup.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',lambda e:canvas.itemconfigure(window,width=e.width))
        self.setup.columnconfigure(1,weight=1)
        ttk.Label(self.setup,text=tr('游戏'),style='Section.TLabel').grid(row=0,column=0,columnspan=3,sticky='w',pady=(0,px(12)))
        ttk.Label(self.setup,text=tr('游戏程序')).grid(row=1,column=0,sticky='w',padx=(0,px(16)))
        ttk.Entry(self.setup,textvariable=self.vars['game_executable'],state='readonly').grid(row=1,column=1,sticky='ew')
        self.button(self.setup,'选择游戏',lambda:self.browse('game_executable','file')).grid(row=1,column=2,padx=(px(8),0))
        ttk.Label(self.setup,text=tr('使用的名单')).grid(row=2,column=0,sticky='w',pady=(px(14),px(6)))
        self.roster_choice=tk.StringVar()
        self.roster_box=ReadonlyCombobox(self.setup,textvariable=self.roster_choice)
        self.roster_box.grid(row=2,column=1,sticky='ew',pady=(px(14),px(6)))
        self.roster_box.bind('<<ComboboxSelected>>',self.select_roster)
        self.button(self.setup,'重新查找',self.detect_game).grid(row=2,column=2,padx=(px(8),0),pady=(px(14),px(6)))
        self.setup_status=tk.StringVar(value=tr('选择游戏程序后，工具会自动查找并校验已有名单。'))
        status=ttk.Label(self.setup,textvariable=self.setup_status,style='Muted.TLabel',justify='left')
        status.grid(row=3,column=0,columnspan=3,sticky='ew',pady=(px(4),px(14)))
        status.bind('<Configure>',lambda e:status.configure(wraplength=max(1,e.width)))
        ttk.Label(self.setup,text=tr('比赛提醒'),style='Section.TLabel').grid(row=4,column=0,columnspan=3,sticky='w',pady=(px(10),px(12)))
        teams=json.loads((RESOURCES/'nba_teams.json').read_text('utf-8'))
        from schedule_notice import TEAM_NAMES
        self.team_choices={(TEAM_NAMES.get(t['abbreviation'],t['name'])+' / '+t['name'] if language()=='zh-CN' else t['name']):t['id'] for t in teams}
        current=next((label for label,id in self.team_choices.items() if id==str(self.settings['schedule_team_id'])),next(iter(self.team_choices)))
        self.team=tk.StringVar(value=current)
        ttk.Label(self.setup,text=tr('赛程提醒球队')).grid(row=5,column=0,sticky='w',pady=px(6))
        ReadonlyCombobox(self.setup,textvariable=self.team,values=list(self.team_choices)).grid(row=5,column=1,sticky='ew')
        options=ttk.Frame(self.setup);options.grid(row=6,column=0,columnspan=3,sticky='w',pady=px(10))
        self.show_schedule=tk.BooleanVar(value=self.settings['show_schedule'])
        self.allow_missing=tk.BooleanVar(value=self.settings['allow_missing_players'])
        ttk.Checkbutton(options,text=tr('启动前置顶确认赛程'),variable=self.show_schedule).pack(anchor='w',pady=px(3))
        ttk.Checkbutton(options,text=tr('缺少球员时保留原队员并继续更新'),variable=self.allow_missing).pack(anchor='w',pady=px(3))
        hint=ttk.Label(self.setup,text=tr('无需创建游戏数据目录或安装额外名单包。首次保存会自动备份现有名单；缓存、恢复备份和版本适配由工具管理。'),style='Muted.TLabel',justify='left')
        hint.grid(row=7,column=0,columnspan=3,sticky='ew',pady=(px(4),px(12)))
        hint.bind('<Configure>',lambda e:hint.configure(wraplength=max(1,e.width)))
        self.advanced_button=self.button(self.setup,'高级设置…',self.toggle_advanced)
        self.advanced_button.grid(row=8,column=0,columnspan=3,sticky='w',pady=px(8))
        self.advanced=ttk.Frame(self.setup);self.advanced.grid(row=9,column=0,columnspan=3,sticky='ew');self.advanced.columnconfigure(1,weight=1)
        fields=[('sync_directory','游戏已有数据位置','dir'),('manifest_name','名单清单文件','manifest'),
                ('launch_mode','启动方式','mode'),('steam_app_id','Steam App ID','text'),
                ('data_directory','工具备份位置','dir'),('cache_directory','可清理缓存位置','dir'),
                ('compatibility_profile','版本适配配置','profile')]
        for row,(key,label,kind) in enumerate(fields):
            ttk.Label(self.advanced,text=tr(label)).grid(row=row,column=0,sticky='w',pady=px(6),padx=(0,px(16)))
            var=self.vars[key]
            if kind=='manifest':
                self.manifests=ReadonlyCombobox(self.advanced,textvariable=var)
                self.manifests.grid(row=row,column=1,sticky='ew')
                self.manifests.bind('<<ComboboxSelected>>',lambda e:self.refresh_roster_choices())
                self.button(self.advanced,'读取清单',self.read_manifests).grid(row=row,column=2,padx=(px(8),0))
            elif kind=='mode':
                ReadonlyCombobox(self.advanced,textvariable=var,values=('steam','direct'),width=16).grid(row=row,column=1,sticky='w')
            else:
                ttk.Entry(self.advanced,textvariable=var).grid(row=row,column=1,sticky='ew')
                if kind in ('dir','profile'):
                    self.button(self.advanced,'选择',lambda k=key,t=kind:self.browse(k,t)).grid(row=row,column=2,padx=(px(8),0))
        row=len(fields)
        ttk.Label(self.advanced,text=tr('从其他本机名单导入（可选）')).grid(row=row,column=0,sticky='w',pady=px(6),padx=(0,px(16)))
        ttk.Entry(self.advanced,textvariable=self.baseline_source).grid(row=row,column=1,sticky='ew')
        self.button(self.advanced,'选择',self.browse_baseline).grid(row=row,column=2,padx=(px(8),0))
        ttk.Checkbutton(self.advanced,text=tr('重新读取当前游戏名单并建立恢复备份'),variable=self.reimport).grid(row=row+1,column=0,columnspan=3,sticky='w',pady=px(10))
        detail=ttk.Label(self.advanced,text=tr('游戏数据位置必须已经包含名单，空文件夹无效。恢复备份是第一次导入的名单，普通保存保留它；只有主动重新导入或更换安装位置时才建立新备份，旧备份继续保留。'),style='Muted.TLabel',justify='left')
        detail.grid(row=row+2,column=0,columnspan=3,sticky='ew',pady=(px(4),px(12)))
        detail.bind('<Configure>',lambda e:detail.configure(wraplength=max(1,e.width)))
        self.advanced.grid_remove()
        if not self.setup_candidates and self.settings.get('manifest_name') and self.settings.get('sync_directory'):
            self.setup_candidates=[dict(path=self.settings['sync_directory'],manifest=self.settings['manifest_name'],account='',origin='configured')]
        self.read_manifests(quiet=True)
        self.refresh_roster_choices()
        self.bind_settings_wheel(viewport)

    def toggle_advanced(self):
        self.advanced_open=not self.advanced_open
        if self.advanced_open:self.advanced.grid()
        else:self.advanced.grid_remove()
        self.advanced_button.configure(text=tr('收起高级设置' if self.advanced_open else '高级设置…'))

    def browse_baseline(self):
        value=filedialog.askdirectory(parent=self,title=tr('选择已有的本机名单目录'))
        if value:self.baseline_source.set(value)

    def refresh_roster_choices(self):
        from game_setup import same_path
        self.roster_options={}
        for index,c in enumerate(self.setup_candidates):
            label=(tr('Steam 账号 {account}',account=c['account']) if c.get('account') else tr('本机游戏名单'))
            if len(self.setup_candidates)>1:
                saved=datetime.fromtimestamp(c['modified']).strftime('%Y-%m-%d %H:%M') if c.get('modified') else tr('现有配置')
                label=tr('{label} · 最近保存 {date} · {number}',label=label,date=saved,number=index+1)
            self.roster_options[label]=c
        self.roster_box['values']=list(self.roster_options)
        matched=next((label for label,c in self.roster_options.items() if same_path(c['path'],self.vars['sync_directory'].get()) and c['manifest']==self.vars['manifest_name'].get()),None)
        self.roster_choice.set(matched or tr('等待查找游戏名单'))
        if matched:self.setup_status.set(tr('已选择已有游戏名单。首次保存自动备份，之后可直接更新。'))

    def select_roster(self,event=None):
        if self.busy:return
        candidate=self.roster_options.get(self.roster_choice.get())
        if candidate:self.apply_roster(candidate)

    def apply_roster(self,candidate):
        from game_setup import automatic_storage,same_path
        same=(same_path(self.vars['game_executable'].get(),self.settings.get('game_executable')) and same_path(candidate['path'],self.settings.get('sync_directory')) and candidate['manifest']==self.settings.get('manifest_name'))
        self.vars['sync_directory'].set(candidate['path']);self.vars['manifest_name'].set(candidate['manifest'])
        if not same:
            defaults=automatic_storage(self.vars['game_executable'].get(),candidate['path'],candidate['manifest'])
            for key in ('data_directory','cache_directory'):
                if not self.vars[key].get() or self.vars[key].get() in (str(self.settings.get(key,'')),getattr(self,'setup_storage',{}).get(key)):
                    self.vars[key].set(defaults[key])
            self.setup_storage=defaults
            self.vars['baseline_directory'].set('')
        self.read_manifests(quiet=True);self.refresh_roster_choices()
        self.setup_status.set(tr('已找到并校验游戏名单。点击“保存并开始使用”即可。' if candidate.get('verified') else '已选择已有游戏名单。保存时会校验并建立恢复备份。'))

    def detect_game(self):
        executable=self.vars['game_executable'].get()
        if not executable:self.browse('game_executable','file');return
        self.setup_status.set(tr('正在查找并校验游戏已有名单…'))
        settings=dict(self.settings)
        for key in ('cache_directory','compatibility_profile'):settings[key]=self.vars[key].get().strip()
        def job():
            from game_setup import discover_game
            return ('detected',discover_game(executable,settings))
        self.start(job,tr('正在查找游戏名单'))

    def apply_detection(self,result):
        self.vars['game_executable'].set(result['executable']);self.vars['launch_mode'].set(result['launch_mode']);self.vars['steam_app_id'].set(result['app_id'])
        self.setup_candidates=result['candidates']
        self.vars['sync_directory'].set('');self.vars['manifest_name'].set('')
        self.refresh_roster_choices()
        if result['selected'] is not None:self.apply_roster(self.setup_candidates[result['selected']])
        elif self.setup_candidates:
            self.roster_choice.set(tr('找到多份名单，请选择正在使用的存档'))
            self.setup_status.set(tr('找到了多份兼容名单。请选择当前使用的存档；工具不会按修改时间擅自覆盖。'))
        else:
            self.setup_status.set(tr('尚未找到可用名单。请用当前 Windows 账号启动游戏、进入主菜单后退出，再点“重新查找”。无需新建文件夹。也可在高级设置中选择已有数据位置。'))

    def bind_settings_wheel(self,widget):
        # Only this viewport's existing controls receive the routing tag.
        # Tcl-created popup listboxes and every other page keep native bindings.
        widget.bindtags((self._settings_wheel_tag,)+widget.bindtags())
        for child in widget.winfo_children():self.bind_settings_wheel(child)

    def scroll_settings(self,event):
        if self.page_id!='settings':return
        if self.settings_canvas.winfo_height()<self.setup.winfo_reqheight():
            self._settings_wheel_delta+=event.delta
            steps=int(-self._settings_wheel_delta/120)
            self._settings_wheel_delta+=steps*120
            if steps:self.settings_canvas.yview_scroll(steps,'units')
        return 'break'

    def make_about(self):
        px=self.px
        header=self.page_header(self.about,'维护')
        self.button(header,'原生名单与回退说明',self.show_roster_data_help).pack(side='right')
        for title,description,action,command in [
            ('基准名单','恢复到导入时的名单。操作前请正常退出游戏。','恢复导入的基准名单',self.restore),
            ('诊断摘要','导出版本、路径可用性和最近更新状态，供排查使用。','导出诊断',self.export_diagnostics),
            ('高级配置',str(config_path()),'打开配置',self.open_config)]:
            card=ttk.Frame(self.about,style='Card.TFrame',padding=px(16));card.pack(fill='x',pady=(0,px(12)))
            self.button(card,action,command).pack(side='right',padx=(px(16),0))
            copy=ttk.Frame(card,style='Card.TFrame');copy.pack(side='left',fill='x',expand=True)
            ttk.Label(copy,text=tr(title),style='CardStrong.TLabel').pack(anchor='w')
            detail=ttk.Label(copy,text=tr(description),style='CardMuted.TLabel',justify='left')
            detail.pack(fill='x',pady=(px(6),0))
            detail.bind('<Configure>',lambda e,label=detail:label.configure(wraplength=max(1,e.width)))
        from usage_notice import open_rights_contact,show_notice
        about_header=ttk.Frame(self.about);about_header.pack(fill='x',pady=(px(12),px(8)))
        ttk.Label(about_header,text=tr('关于'),style='Section.TLabel').pack(side='left')
        self.button(about_header,'数据来源与风险',show_notice).pack(side='right')
        self.button(about_header,'权利人联系',open_rights_contact).pack(side='right',padx=(px(8),0))
        self.button(about_header,'撤回首次确认',self.reset_usage_consent).pack(side='right',padx=(px(8),px(8)))
        text=APP_NAME+' '+VERSION+'\n'+tr('仅支持 NBA 2K27 · Windows x64 · 快速比赛')+'\n'+tr('SYNC RDAT v9 是游戏名单格式，无需额外安装包。')+'\n'+tr('数据来源：ESPN 公共接口；非 2K 官方每日名单。')+'\n'+tr('独立第三方工具，与 NBA、2K、Valve、ESPN 无隶属关系。')+'\n'+tr('风险：ESPN 自动采集许可尚未取得；外部名单修改可能引发条款争议、下架或账号措施。')
        about=ttk.Label(self.about,text=text,style='Muted.TLabel',justify='left')
        about.pack(fill='x');about.bind('<Configure>',lambda e:about.configure(wraplength=max(1,e.width)))

    def reset_usage_consent(self):
        from usage_notice import revoke_consent
        revoke_consent()
        self.info('已撤回首次确认，下次获取数据或更新名单前会再次询问。')

    def show_roster_data_help(self):
        text=tr('工具直接使用游戏已有名单，无需额外补丁包。选择游戏程序后自动寻找名单；首次保存会自动备份，平时只需点击“仅更新名单”或“更新并启动”。\n\n缺少球员时保留本队真实队员补位，整队无法匹配或无法组成安全首发时保留整队原名单；相关转会暂缓，缺少的球员不会凭空创建。\n\n如果你已在游戏中安装其他有权使用的名单更新，在设置中重新查找，然后展开“高级设置”，勾选“重新读取当前游戏名单并建立恢复备份”，再保存。已有恢复备份继续保留。')
        if show_dialog(tr('原生名单与回退说明'),text,True,tr('前往设置')):
            self.show_page('settings')
            self.baseline_source.set('');self.reimport.set(True)
            self.settings_canvas.yview_moveto(0)

    def show_coverage_details(self):
        if not self.missing_players and not self.fallback_teams:return
        px=self.px
        dialog=tk.Toplevel(self);dialog.title(tr('上次更新与回退记录'))
        dialog.configure(background=BG);dialog.transient(self)
        width=min(px(710),self.winfo_screenwidth()-px(60));height=min(px(470),self.winfo_screenheight()-px(90))
        x=max(0,self.winfo_rootx()+(self.winfo_width()-width)//2);y=max(0,self.winfo_rooty()+(self.winfo_height()-height)//2)
        dialog.geometry(f'{width}x{height}+{x}+{y}');dialog.minsize(px(580),px(360))
        body=ttk.Frame(dialog,padding=px(20));body.pack(fill='both',expand=True)
        hint=ttk.Label(body,text=tr('未匹配球员不会凭空出现。回退保留原队员或整队旧数据，详细列于下方；暂缓的转会和伤病不会算作已更新。'),wraplength=width-px(40))
        hint.pack(fill='x',pady=(0,px(12)))
        actions=ttk.Frame(body);actions.pack(side='bottom',fill='x',pady=(px(12),0))
        def help_data():
            dialog.destroy();self.show_roster_data_help()
        ttk.Button(actions,text=tr('原生名单与回退说明'),command=help_data).pack(side='left')
        ttk.Button(actions,text=tr('关闭'),command=dialog.destroy).pack(side='right')
        listing=ttk.Frame(body);listing.pack(fill='both',expand=True)
        text=tk.Text(listing,wrap='word',font=(self.ui_font,11),background=PANEL,foreground=TEXT,
            selectbackground=RAISED,selectforeground=TEXT,relief='flat',highlightthickness=0,padx=px(12),pady=px(12))
        scrollbar=ttk.Scrollbar(listing,command=text.yview);text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right',fill='y');text.pack(side='left',fill='both',expand=True)
        for player in self.missing_players:text.insert('end',player['name']+'  /  '+player['team']+'\n')
        for fallback in self.fallback_teams:
            action={'preserve_team':'整队保留原名单','local_lineup':'按本地位置与原顺序补全轮换'}.get(fallback['mode'],'保留原队员补位')
            text.insert('end','\n'+fallback['team']+' — '+tr(action)+'\n')
            if fallback.get('missing_positions'):
                text.insert('end',tr('来源缺少位置：{positions}',positions=', '.join(p.upper() for p in fallback['missing_positions']))+'\n')
            text.insert('end',', '.join(fallback['retained_players'])+'\n')
        if self.skipped_mapped:
            text.insert('end','\n'+tr('因球队保留而暂缓的来源记录：')+'\n')
            for player in self.skipped_mapped:text.insert('end',player['source_name']+' / '+player['new_team']+'\n')
        text.configure(state='disabled');dialog.bind('<Escape>',lambda e:dialog.destroy())
        dark_titlebar(dialog);dialog.grab_set()

    def info(self,text):
        return show_dialog(APP_NAME,tr(text))

    def browse(self,key,kind):
        value=(filedialog.askdirectory(parent=self,title=tr('选择文件夹')) if kind=='dir' else
               filedialog.askopenfilename(parent=self,title=tr('选择兼容档案' if kind=='profile' else '选择游戏程序'),
               filetypes=[(tr('JSON 档案'),'*.json')] if kind=='profile' else [(tr('游戏程序'),'*.exe')]))
        if value:
            self.vars[key].set(value)
            if key=='sync_directory':self.read_manifests()
            elif key=='game_executable':self.detect_game()

    def read_manifests(self,quiet=False):
        from baseline_tools import available_manifests
        folder=self.vars['sync_directory'].get()
        values=available_manifests(folder) if folder else []
        self.manifests['values']=values
        if self.vars['manifest_name'].get() not in values:self.vars['manifest_name'].set(values[0] if len(values)==1 else '')
        if not quiet:
            self.setup_candidates=[dict(path=folder,manifest=name,account='',origin='manual') for name in values]
            self.refresh_roster_choices()
            if not values:self.info('该位置没有游戏名单。请选择游戏已经生成的数据文件夹，无需创建新目录。')

    def save(self):
        s=dict(self.settings)
        s.update({key:var.get().strip() for key,var in self.vars.items()})
        s.update(schedule_team_id=self.team_choices[self.team.get()],show_schedule=self.show_schedule.get(),allow_missing_players=self.allow_missing.get())
        from game_setup import same_path
        source=self.baseline_source.get().strip()
        same=(all(same_path(s.get(key),self.settings.get(key)) for key in ('game_executable','sync_directory','data_directory'))
              and s['manifest_name']==self.settings.get('manifest_name') and s['compatibility_profile']==self.settings.get('compatibility_profile'))
        needs_import=bool(source or self.reimport.get() or not same or not (Path(s['baseline_directory'])/s['manifest_name']).is_file())
        if not s['baseline_directory']:s['baseline_directory']=str(Path(s['data_directory'])/'Baseline')
        def job():
            from baseline_tools import import_baseline
            validate_settings(s)
            if needs_import:import_baseline(s,source or s['sync_directory'])
            save_settings(s)
            print(tr('设置已保存，恢复备份已就绪。'),flush=True)
            return ('saved',s)
        self.start(job,tr('保存设置并准备恢复备份'))

    def find_steam(self):
        def job():
            from game_setup import installed_games
            return ('steam',installed_games())
        self.start(job,tr('读取 Steam 安装信息'))

    def choose_steam(self,games):
        if not games:
            self.setup_status.set(tr('未发现 Steam 安装。点击“选择游戏”选中 NBA2K27.exe 后，会继续自动寻找本机名单。'));return
        if len(games)==1:
            self.vars['game_executable'].set(games[0]['executable']);self.detect_game();return
        choices=[(game['name']+' / '+game['executable'],game) for game in games]
        dialog=tk.Toplevel(self);dialog.title(tr('选择游戏安装'));dialog.configure(background=BG)
        dialog.geometry(f'{self.px(780)}x{self.px(190)}');dialog.transient(self);dialog.grab_set();dark_titlebar(dialog)
        selected=tk.StringVar(value=choices[0][0])
        ttk.Label(dialog,text=tr('请选择要使用的游戏安装，名单位置随后自动查找。')).pack(anchor='w',padx=self.px(18),pady=self.px(18))
        ReadonlyCombobox(dialog,textvariable=selected,values=[c[0] for c in choices]).pack(fill='x',padx=self.px(18))
        def apply():
            _,game=next(c for c in choices if c[0]==selected.get())
            self.vars['game_executable'].set(game['executable']);dialog.destroy();self.detect_game()
        ttk.Button(dialog,text=tr('使用所选安装'),style='Primary.TButton',command=apply).pack(anchor='e',padx=self.px(18),pady=self.px(18))

    def update(self,start_game):
        if not self.configured():
            self.show_page('settings');self.setup_status.set(tr('请先选择游戏并点击“保存并开始使用”。'));return
        self.show_page('home')
        def job():
            from launch_nba import run
            result=run(start_game);return ('cancelled' if result==2 else 'updated',None)
        self.start(job,tr('同步名单并等待赛程确认' if start_game else '同步名单，保持游戏关闭'))

    def restore(self):
        if show_dialog(APP_NAME,tr('将游戏清单恢复为导入时的基准。请先正常退出游戏。\n个人赛季存档保持原样。是否恢复？'),True,tr('恢复')):
            def job():
                from baseline_tools import restore_baseline
                from usage_notice import UsageConsentDeclined
                try:result=restore_baseline()
                except UsageConsentDeclined:return ('cancelled',None)
                print(json.dumps(result,ensure_ascii=False,indent=2),flush=True);return ('restored',None)
            self.start(job,tr('恢复基准名单'))

    def export_diagnostics(self):
        from app_main import diagnostic_summary
        path=filedialog.asksaveasfilename(parent=self,defaultextension='.json',initialfile='Roster-Beacon-diagnostics.json',filetypes=[('JSON','*.json')])
        if path:
            Path(path).write_text(json.dumps(diagnostic_summary(),ensure_ascii=False,indent=2),encoding='utf-8')
            self.info('已导出脱敏摘要，未包含游戏文件或本机绝对路径。')

    def open_data(self):
        path=path_setting(load_settings(),'data_directory');path.mkdir(parents=True,exist_ok=True);os.startfile(str(path))

    def open_config(self):
        path=config_path()
        if not path.is_file():save_settings(self.settings)
        os.startfile(str(path))

    def dialog_from_worker(self,title,text,confirm,accept_label):
        request=dict(title=title,text=text,confirm=confirm,accept_label=accept_label,event=threading.Event(),result=False)
        self.messages.put(('dialog',request));request['event'].wait();return request['result']

    def start(self,job,description):
        if self.busy:return
        self.busy=True;self.status.set(description);self.language_box.configure(state='disabled')
        for button in self.job_buttons:button.configure(state='disabled')
        self.progress.pack(fill='x',before=self.pages_host,pady=(0,self.px(8)));self.progress.start(12)
        def worker():
            try:
                root=path_setting(load_settings(),'data_directory');root.mkdir(parents=True,exist_ok=True)
                log=root/'app.log'
                if log.is_file() and log.stat().st_size>2*1024*1024:log.replace(root/'app.previous.log')
                with log.open('a',encoding='utf-8',buffering=1) as stream:
                    writer=LogWriter(self.messages,stream)
                    with contextlib.redirect_stdout(writer),contextlib.redirect_stderr(writer):
                        try:result=job()
                        except Exception:traceback.print_exc();raise
                self.messages.put(('done',result))
            except Exception as error:self.messages.put(('error',localize(error)))
        threading.Thread(target=worker,name='roster-operation',daemon=False).start()

    def consume(self):
        try:
            while True:
                kind,data=self.messages.get_nowait()
                if kind=='log':
                    self.log_history+=data
                    self.log.configure(state='normal')
                    if self.empty_log:self.log.delete('1.0','end');self.empty_log=False
                    self.log.insert('end',data);self.log.see('end');self.log.configure(state='disabled')
                elif kind=='dialog':
                    try:data['result']=themed_dialog(self,data['title'],data['text'],data['confirm'],data['accept_label'])
                    finally:data['event'].set()
                else:
                    self.busy=False;self.progress.stop();self.progress.pack_forget();self.language_box.configure(state='readonly')
                    for button in self.job_buttons:button.configure(state='normal')
                    self.status.set(tr('操作失败，已停止启动游戏' if kind=='error' else '操作完成'))
                    self.refresh_summary()
                    if kind=='error':show_dialog(APP_NAME,data)
                    else:
                        action,value=data
                        if action=='saved':
                            self.settings=value;self.vars['baseline_directory'].set(value['baseline_directory'])
                            self.baseline_source.set('');self.reimport.set(False);self.refresh_summary();self.show_page('home')
                            self.status.set(tr('设置完成，可以更新名单或更新并启动游戏'))
                        elif action=='steam':self.choose_steam(value)
                        elif action=='detected':self.apply_detection(value)
                        elif action=='restored':self.info('已恢复导入的基准名单。')
                        elif action=='cancelled':self.status.set(tr('已取消联网获取，名单和游戏保持原样'))
        except queue.Empty:pass
        self.after(80,self.consume)

    def close(self):
        if self.busy:self.info('操作正在进行，请等待结果后关闭窗口。')
        else:self.destroy()
