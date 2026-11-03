"""Download a consistent ESPN snapshot. Never edits game files."""

from i18n import localize
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import urllib.request
from app_runtime import load_settings, path_setting
from usage_notice import ensure_usage_consent

CACHE_ROOT = path_setting(load_settings(), 'cache_directory')
SNAPSHOT_PATH = CACHE_ROOT / 'espn_snapshot.json'
BASE = load_settings()['api_base'].rstrip('/')
POSITIONS = ('pg', 'sg', 'sf', 'pf', 'c')

def get_json(url):
    ensure_usage_consent(url)
    request = urllib.request.Request(url,headers={'User-Agent':'NBA-Roster-Sync/1.0','Accept':'application/json'})
    with urllib.request.urlopen(request, timeout=int(load_settings()['request_timeout'])) as response:
        if response.status != 200:
            raise ValueError(localize(f'名单来源返回 HTTP {response.status}'))
        return json.load(response)

def fetch():
    global CACHE_ROOT, SNAPSHOT_PATH, BASE
    settings = load_settings()
    CACHE_ROOT = path_setting(settings, 'cache_directory')
    SNAPSHOT_PATH = CACHE_ROOT/'espn_snapshot.json'
    BASE = settings['api_base'].rstrip('/')
    now = datetime.now(timezone.utc)
    teams = [entry['team'] for sport in get_json(BASE+'/teams?limit=100')['sports']
             for league in sport['leagues'] for entry in league['teams']]
    if len(teams)!=30 or len({t['id'] for t in teams})!=30:
        raise ValueError(localize('未取得完整的 30 支 NBA 球队'))
    expected_year = int(settings.get('season_year') or now.year + int(now.month >= 7))
    def roster(team):
        url = BASE+'/teams/'+team['id']+'/roster'
        data = get_json(url)
        if data.get('season',{}).get('year') != expected_year:
            raise ValueError(localize(f"{team['displayName']} 返回的不是当前赛季名单"))
        athletes=data['athletes']
        if not 5 <= len(athletes) <= 30:
            raise ValueError(localize(f"{team['displayName']} 名单人数异常"))
        depth_url = BASE+'/teams/'+team['id']+'/depthcharts'
        depth = get_json(depth_url)
        if depth.get('status') != 'success' or str(depth.get('team', {}).get('id')) != str(team['id']):
            raise ValueError(localize(f"{team['displayName']} 出场顺序来源返回失败或球队不符"))
        if depth.get('season', {}).get('year') != expected_year:
            raise ValueError(localize(f"{team['displayName']} 出场顺序不是当前赛季"))
        charts = depth.get('depthchart') or []
        if len(charts) != 1:
            raise ValueError(localize(f"{team['displayName']} 缺少唯一的球队深度表"))
        positions = charts[0].get('positions', {})
        order = {p: [dict(id=str(a['id']), name=a['displayName'])
                     for a in positions.get(p, {}).get('athletes', [])] for p in POSITIONS}
        if any(not values or len({a['id'] for a in values}) != len(values) for values in order.values()):
            raise ValueError(localize(f"{team['displayName']} 出场顺序缺少位置或同位置球员重复"))
        return dict(source=url,team=team['displayName'],abbreviation=team['abbreviation'],
                    team_id=team['id'],season=data['season'],athletes=athletes,
                    depth_chart=dict(source=depth_url,timestamp=depth.get('timestamp'),positions=order))
    with ThreadPoolExecutor(max_workers=max(1, min(12, int(settings['network_workers'])))) as pool:
        rosters=list(pool.map(roster, teams))
    ids=[a['id'] for t in rosters for a in t['athletes']]
    if len(ids)!=len(set(ids)):
        raise ValueError(localize('来源同时把一位球员列在不同球队，暂不生成更新'))
    injuries=get_json(BASE+'/injuries')
    stamp=datetime.fromisoformat(injuries['timestamp'].replace('Z','+00:00'))
    if abs((now-stamp).total_seconds())>24*3600 or injuries.get('status')!='success':
        raise ValueError(localize('伤病数据源没有返回最近 24 小时的完整结果'))
    snapshot=dict(fetched_at=now.isoformat(),source='ESPN public NBA endpoints; not official 2K roster',
                  rosters=rosters,injuries=injuries)
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    target=SNAPSHOT_PATH
    temporary=target.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding='utf-8')
    temporary.replace(target)
    return snapshot

if __name__=='__main__':
    source=fetch()
    print(json.dumps(dict(teams=len(source['rosters']),players=sum(len(t['athletes']) for t in source['rosters']),
                          fetched_at=source['fetched_at']),ensure_ascii=False))
