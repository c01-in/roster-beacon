"""Update first, then confirm the schedule and launch through Steam or EXE."""
import argparse
from datetime import datetime
import json
import os
import subprocess
import sys

import sync_nba as sync
from app_runtime import validate_settings
from operations import operation_lock
from schedule_notice import confirm_schedule
from i18n import localize,tr
from usage_notice import UsageConsentDeclined


def check_installed():
    entries = sync.manifest_entries((sync.DEST/sync.MANIFEST).read_bytes())
    name, size = entries[sync.ROSTER_PATH]
    data = (sync.DEST/name).read_bytes()
    if len(data) != size or sync.guid(data) != name:
        raise ValueError(localize('已安装的名单校验失败，已停止启动'))


def run(start_game=True):
    settings = validate_settings()
    sync.configure()
    with operation_lock():
        if sync.game_running():
            raise RuntimeError(localize('游戏正在运行，请先正常退出；本次保持游戏和名单原样'))
        status = dict(time=datetime.now().astimezone().isoformat(), game_launched=False)
        status_path = sync.ROOT/'启动状态.txt'
        try:
            print(tr('正在同步全部 30 队的名单、伤病和出场顺序……'), flush=True)
            result = sync.synchronize()
            check_installed()
            status.update(update='success_with_fallback' if result.get('fallback_teams') else ('success_with_missing' if result['missing'] else 'success'),
                          scope=result['scope'], teams=result['team_count'], players=result['players'],
                          source_players=result['source_players'], missing=result['missing'],
                          injury_reports=len(result['injuries']), fetched_at=result['fetched_at'],
                          source_warnings=result['source_warnings'],fallback_teams=result.get('fallback_teams',[]),
                          preserved_team_count=result.get('preserved_team_count',0),teams_updated=len(result.get('affected_teams',[])))
            print(tr('更新成功：{teams} 队，球员 {players}/{source}，伤病 {injuries} 条。',teams=result['team_count'],players=result['players'],source=result['source_players'],injuries=len(result['injuries'])),flush=True)
            for player in result['missing']:
                print(tr('资料缺少：{player}',player=player['team']+' / '+player['name']),flush=True)
            for fallback in result.get('fallback_teams',[]):
                action=tr('整队保留原名单' if fallback['mode']=='preserve_team' else '保留原队员补位')
                print(tr('回退提示：{team}，{action}。',team=fallback['team'],action=action),flush=True)
            for warning in result['source_warnings']:
                print(tr('来源提示：{warning}',warning=warning['name']+' / '+localize(warning['reason'])),flush=True)
            if start_game:
                if settings.get('show_schedule', True):
                    accepted, reminder = confirm_schedule(sync.ROOT)
                    status.update(schedule_notice=reminder, schedule_confirmed=accepted)
                    if not accepted:
                        status['launch'] = 'cancelled_by_user'
                        sync.atomic_write(status_path, json.dumps(status,ensure_ascii=False,indent=2).encode('utf-8'))
                        return 0
                if sync.game_running():
                    raise RuntimeError(localize('等待确认期间游戏已被启动，本次保持原样'))
                check_installed()
                sync.atomic_write(status_path, json.dumps(status,ensure_ascii=False,indent=2).encode('utf-8'))
                if settings['launch_mode'] == 'steam':
                    os.startfile('steam://rungameid/'+str(settings['steam_app_id']))
                    status['launch'] = 'steam_request_sent'
                else:
                    subprocess.Popen([str(sync.GAME)], cwd=str(sync.GAME.parent), close_fds=True)
                    status['launch'] = 'process_started'
                status['game_launched'] = True
            sync.atomic_write(status_path, json.dumps(status,ensure_ascii=False,indent=2).encode('utf-8'))
            return 0
        except UsageConsentDeclined as error:
            status.update(update='cancelled_by_user', launch='cancelled_by_user')
            sync.atomic_write(status_path, json.dumps(status,ensure_ascii=False,indent=2).encode('utf-8'))
            print(str(error),flush=True)
            return 2
        except Exception as error:
            status.update(update=status.get('update', 'failed_blocked_launch'), launch='blocked', error=str(error))
            sync.atomic_write(status_path, json.dumps(status,ensure_ascii=False,indent=2).encode('utf-8'))
            print(tr('已停止启动游戏：{error}',error=localize(error)),file=sys.stderr,flush=True)
            raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--update-only', action='store_true', help=tr('更新名单并记录结果，保持游戏关闭'))
    args = parser.parse_args()
    try:
        return run(start_game=not args.update_only)
    except Exception as error:
        print(localize(error),file=sys.stderr)
        if not args.update_only:
            from schedule_notice import message_box
            from app_runtime import APP_NAME
            message_box(str(error), APP_NAME+' · '+tr('已停止启动游戏'), False)
        return 1


if __name__ == '__main__':
    sys.exit(main())
