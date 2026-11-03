"""Produce an explicit, read-only matching plan; never modifies a roster."""

from i18n import localize
from collections import defaultdict
import json
from pathlib import Path
import re
import unicodedata
from roster_file import Roster, NULL_POINTER
from app_runtime import RESOURCES, load_settings, path_setting, resource_setting

ROOT=RESOURCES

def normalize(value):
    value=unicodedata.normalize('NFKD',value).encode('ascii','ignore').decode().lower()
    value=re.sub(r'(?:[\s,.]+(?:jr|sr|ii|iii|iv|v)\.?)$','',value)
    return re.sub('[^a-z0-9]','',value)

ALIASES={normalize(a):normalize(b) for a,b in [
    ('Nic Claxton','Nicolas Claxton'),('Ronald Holland II','Ron Holland'),
    ('Bones Hyland',"Nah'Shon Hyland"),('Yang Hansen','Hansen Yang'),
    ('Mo Bamba','Mohamed Bamba'),('Svi Mykhailiuk','Sviatoslav Mykhailiuk'),
    ('Bub Carrington','Carlton Carrington'),('Alex Sarr','Alexandre Sarr')]}

def make_plan(path, snapshot):
    roster=Roster(path)
    players=[roster.player(i) for i in range(roster.players.count)]
    teams=json.loads(resource_setting(load_settings(), 'team_map_file', 'team_map.json').read_text('utf-8'))
    if len(teams)!=30 or {t['index'] for t in teams}!=set(range(30)):
        raise ValueError(localize('球队映射必须完整覆盖 30 支 NBA 球队'))
    by_team={normalize(t['name']):t['index'] for t in teams}
    by_team[normalize('LA Clippers')]=next(t['index'] for t in teams if t['abbreviation']=='LAC')
    eligible=set()
    for team in teams:
        for key in ['CorePlayer','HardshipPlayer','TwoWayPlayer','EuroStashPlayer']:
            eligible.update(v>>32 for v in roster.teams.pointers(team['index'],key) if v!=NULL_POINTER)
    fa=roster.free_agents.pointers(0,0x9FB57F53)
    eligible.update(v>>32 for v in fa if v!=NULL_POINTER)
    by_name=defaultdict(list)
    for p in players:
        if p['name'].strip():by_name[normalize(p['name'])].append(p)
    mapped=[]
    missing=[]
    for team in snapshot['rosters']:
        target=by_team[normalize(team['team'])]
        for athlete in team['athletes']:
            key=normalize(athlete['fullName']);key=ALIASES.get(key,key)
            candidates=by_name[key]
            preferred=[p for p in candidates if p['index'] in eligible]
            if preferred:candidates=preferred
            else:candidates=[p for p in candidates if p['team_index'] is None]
            if len(candidates)!=1:
                missing.append(dict(name=athlete['fullName'],team=team['team'],source_id=athlete['id'],team_index=target,
                                    reason='游戏中没有唯一、姓名一致的现役或未分配记录'))
                continue
            p=candidates[0]
            mapped.append(dict(name=p['name'],source_name=athlete['fullName'],source_id=athlete['id'],
                               index=p['index'],uid=p['uid'],old_team_index=p['team_index'],
                               new_team_index=target,new_team=team['team']))
    if len({p['index'] for p in mapped})!=len(mapped):
        raise ValueError(localize('多个来源球员匹配到同一游戏记录，停止更新'))
    transfers=[p for p in mapped if p['old_team_index']!=p['new_team_index']]
    team_plan=[dict(team_index=by_team[normalize(t['team'])],source_team_id=str(t['team_id']),
                    team=t['team'],abbreviation=t['abbreviation'],source_players=len(t['athletes']))
               for t in snapshot['rosters']]
    if len(team_plan)!=30 or {t['team_index'] for t in team_plan}!=set(range(30)):
        raise ValueError(localize('来源没有完整覆盖 30 支 NBA 球队'))
    return dict(mode='READ_ONLY_PREVIEW',source=snapshot['source'],fetched_at=snapshot['fetched_at'],teams=team_plan,
                roster=str(path),source_players=sum(len(t['athletes']) for t in snapshot['rosters']),
                matched=len(mapped),unmatched=len(missing),transfers=transfers,mapping=mapped,missing=missing,
                game_file_modified=False)

if __name__=='__main__':
    from fetch_source import CACHE_ROOT, SNAPSHOT_PATH
    source=json.loads(SNAPSHOT_PATH.read_text('utf-8'))
    import tempfile
    from sync_nba import source_roster
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=CACHE_ROOT) as temporary:
        path=Path(temporary)/'source.RDAT'
        path.write_bytes(source_roster()[0])
        plan=make_plan(path,source)
    output=path_setting(load_settings(),'data_directory')
    output.mkdir(parents=True,exist_ok=True)
    (output/'sync_preview.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:plan[k] for k in ['mode','source_players','matched','unmatched','game_file_modified']},ensure_ascii=False))
    print('Transfers:',len(plan['transfers']))
    print('Missing:',', '.join(p['name'] for p in plan['missing']))
