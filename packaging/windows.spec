from pathlib import Path
from PyInstaller.utils.hooks import copy_metadata

ROOT = Path(SPECPATH).parent
files = ['settings.example.json', 'team_map.json', 'injury_types.json', 'nba_teams.json',
         'LICENSE', 'THIRD_PARTY_NOTICES.md', 'README.md', 'README.zh-CN.md', 'CHANGELOG.md']
datas = [(str(ROOT/name), '.') for name in files]
datas += [(str(ROOT/'profiles'), 'profiles'), (str(ROOT/'docs'), 'docs'), (str(ROOT/'assets'), 'assets')]
datas += [(str(ROOT/'locales'), 'locales')]
datas += copy_metadata('psutil')
a = Analysis([str(ROOT/'app_main.py')], pathex=[str(ROOT)], binaries=[], datas=datas,
             hiddenimports=['app_ui', 'tkinter', 'tkinter.ttk', 'psutil._psutil_windows'],
             excludes=['pytest', 'unittest', 'numpy', 'pandas', 'IPython', 'matplotlib'],
             noarchive=False)
pyz = PYZ(a.pure)
common = dict(exclude_binaries=True, debug=False, strip=False, upx=False,
              manifest=str(ROOT/'packaging/windows.manifest'),
              icon=str(ROOT/'assets/app.ico'))
gui = EXE(pyz, a.scripts, [], name='Roster-Beacon', console=False, **common)
cli = EXE(pyz, a.scripts, [], name='Roster-Beacon-cli', console=True, **common)
coll = COLLECT(gui, cli, a.binaries, a.datas, strip=False, upx=False, name='Roster-Beacon')
