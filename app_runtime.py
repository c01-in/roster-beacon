"""Per-computer configuration and paths, shared by source and frozen builds."""
from __future__ import annotations

from i18n import localize

import json
import os
from pathlib import Path
import sys

APP_NAME = 'Roster Beacon'
APP_SLUG = 'Roster-Beacon'
VERSION = '1.0.0-rc9'
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
RESOURCES = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))


def config_path():
    override = os.environ.get('NBA_ROSTER_SYNC_CONFIG')
    if override:
        return Path(override).expanduser().resolve()
    local = APP_DIR/'settings.local.json'
    if local.is_file():
        return local
    return Path(os.environ.get('APPDATA', Path.home()/'AppData/Roaming'))/'NBA-Roster-Sync/settings.json'


def recommended_data_dir():
    for drive in ('E:', 'D:'):
        if Path(drive+'/').is_dir():
            return Path(drive+'/Dev/Projects/NBA-Roster-Sync-Data')
    return Path(os.environ.get('LOCALAPPDATA', Path.home()/'AppData/Local'))/'NBA-Roster-Sync/Data'


def load_settings():
    result = json.loads((RESOURCES/'settings.example.json').read_text('utf-8'))
    path = config_path()
    if path.is_file():
        result.update(json.loads(path.read_text('utf-8-sig')))
    if not result.get('data_directory'):
        result['data_directory'] = str(recommended_data_dir())
    if not result.get('cache_directory'):
        if Path('E:/').is_dir():
            result['cache_directory'] = r'E:\Cache\NBA-Roster-Sync'
        else:
            result['cache_directory'] = str(Path(os.environ.get('LOCALAPPDATA', Path.home()/'AppData/Local'))/'NBA-Roster-Sync/Cache')
    if not result.get('baseline_directory'):
        result['baseline_directory'] = str(Path(result['data_directory'])/'Baseline')
    return result


def save_settings(settings):
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(settings, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    temporary.replace(path)


def path_setting(settings, name):
    value = os.path.expandvars(str(settings.get(name, ''))).strip()
    if not value:
        raise ValueError(localize('请先设置 '+name))
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError(localize(name+' 必须是绝对路径'))
    return path


def resource_setting(settings, name, fallback):
    value = settings.get(name)
    return Path(value).expanduser().resolve() if value else RESOURCES/fallback


def load_profile(settings=None):
    settings = settings or load_settings()
    value = settings.get('compatibility_profile', 'nba2k27-rdat-v9')
    path = Path(value) if str(value).lower().endswith('.json') else RESOURCES/'profiles'/(value+'.json')
    profile = json.loads(path.read_text('utf-8'))
    if profile.get('format') != 'sync-rdat-v9':
        raise ValueError(localize('该兼容档案的名单容器格式尚未实现'))
    if set(profile.get('record_bits', {})) != {'PlayerData','TeamData','FreeAgentData'} or len(profile.get('team_names', [])) != 30:
        raise ValueError(localize('兼容档案必须包含三张表布局和 30 支 NBA 球队名称'))
    return profile


def validate_settings(settings=None):
    s = settings or load_settings()
    if os.name != 'nt':
        raise RuntimeError(localize('本工具仅支持 Windows'))
    exe = path_setting(s, 'game_executable')
    if not exe.is_file() or exe.suffix.lower() != '.exe':
        raise ValueError(localize('请选择已安装游戏的 EXE'))
    if s.get('launch_mode') not in ('direct', 'steam'):
        raise ValueError(localize('启动方式必须是 direct 或 steam'))
    if s['launch_mode'] == 'steam' and not str(s.get('steam_app_id', '')).isdigit():
        raise ValueError(localize('Steam 启动需要正确的 App ID'))
    if not path_setting(s, 'sync_directory').is_dir():
        raise ValueError(localize('游戏 SYNC 目录不存在，请先在游戏里生成数据后选择该目录'))
    name = s.get('manifest_name', '')
    if not name or Path(name).name != name or not name.startswith('manifest_') or not name.endswith('.bin'):
        raise ValueError(localize('请选择名单使用的原生 manifest_*.bin 清单'))
    for field in ('data_directory', 'cache_directory', 'baseline_directory'):
        path_setting(s, field)
    if not str(s.get('schedule_team_id', '')).isdigit():
        raise ValueError(localize('提醒球队 ID 必须为数字'))
    if not str(s.get('api_base', '')).startswith('https://'):
        raise ValueError(localize('数据接口必须使用 HTTPS'))
    load_profile(s)
    if not 1 <= int(s['request_timeout']) <= 120 or not 1 <= int(s['network_workers']) <= 12:
        raise ValueError(localize('网络超时应为 1–120 秒，并行数应为 1–12'))
    return s
