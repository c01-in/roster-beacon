"""Windows GUI entry point and explicit command-line operations."""
import argparse
import json
import os
from pathlib import Path
import platform
import sys
import traceback

from app_runtime import APP_NAME, VERSION, config_path, load_settings, path_setting
from i18n import language,localize,set_language,tr


def diagnostic_summary():
    s = load_settings()
    result = dict(application=APP_NAME, version=VERSION, system=platform.platform(),
                  python=platform.python_version(), launch_mode=s['launch_mode'],
                  profile=Path(s['compatibility_profile']).name, schedule_team=s['schedule_team_id'],language=language())
    result['paths'] = {key: dict(configured=bool(s.get(key)), exists=Path(s[key]).exists() if s.get(key) else False)
                       for key in ('game_executable','sync_directory','data_directory','cache_directory','baseline_directory')}
    state = path_setting(s, 'data_directory')/'last_sync.json'
    if state.is_file():
        data = json.loads(state.read_text('utf-8'))
        result['last_update'] = {key: data.get(key) for key in ('fetched_at','scope','team_count','players','source_players','missing_count','coverage')}
    return result


def main():
    parser = argparse.ArgumentParser(description=APP_NAME+' '+VERSION)
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument('--language',choices=('auto','zh-CN','en-US'),help=tr('本次启动使用的界面语言'))
    parser.add_argument('--settings', action='store_true', help=tr('打开设置'))
    parser.add_argument('--launch', action='store_true', help=tr('打开进度界面，同步成功并确认赛程后启动游戏'))
    parser.add_argument('--update-only', action='store_true', help=tr('仅同步，保持游戏关闭'))
    parser.add_argument('--restore', action='store_true', help=tr('恢复导入的基准清单，游戏必须关闭'))
    parser.add_argument('--diagnose', action='store_true', help=tr('输出不含本机绝对路径的诊断摘要'))
    parser.add_argument('--import-baseline', metavar='SYNC_DIRECTORY', help=tr('从原生 SYNC 目录导入基准'))
    args = parser.parse_args()
    if args.language:
        os.environ['NBA_ROSTER_SYNC_LANGUAGE']=args.language
        set_language(args.language)
    if os.name != 'nt':
        parser.error(tr('本工具仅支持 Windows'))
    if args.diagnose:
        print(json.dumps(diagnostic_summary(),ensure_ascii=False,indent=2))
        return 0
    if args.update_only:
        from launch_nba import run
        return run(False)
    if args.restore:
        from baseline_tools import restore_baseline
        from usage_notice import UsageConsentDeclined
        try:result=restore_baseline()
        except UsageConsentDeclined as error:
            print(str(error),file=sys.stderr)
            return 2
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    if args.import_baseline:
        from app_runtime import save_settings, validate_settings
        from baseline_tools import import_baseline
        s = validate_settings()
        details = import_baseline(s, args.import_baseline)
        save_settings(s)
        print(json.dumps(details,ensure_ascii=False,indent=2))
        return 0
    from app_ui import Application
    Application(open_settings=args.settings, auto_launch=args.launch).mainloop()
    return 0


if __name__ == '__main__':
    # Frozen windowed builds have no stdout. Keep command-line diagnostics useful.
    if sys.stdout is None or sys.stderr is None:
        root = path_setting(load_settings(), 'data_directory')
        root.mkdir(parents=True, exist_ok=True)
        stream = (root/'app.log').open('a',encoding='utf-8',buffering=1)
        sys.stdout = sys.stdout or stream
        sys.stderr = sys.stderr or stream
    try:
        sys.exit(main())
    except Exception as error:
        traceback.print_exc()
        if getattr(sys, 'frozen', False) and not sys.executable.lower().endswith('-cli.exe'):
            from schedule_notice import message_box
            message_box(localize(error)+'\n\n'+tr('已停止操作，详细信息见数据目录中的 app.log。'),APP_NAME,False)
        sys.exit(1)
