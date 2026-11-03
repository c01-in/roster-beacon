"""Reconcile all 30 NBA teams, using authentic existing player records only."""

from i18n import localize
from collections import defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

from preview_sync import ALIASES, make_plan, normalize
from roster_file import NULL_POINTER, read_bits
from fetch_source import POSITIONS
from app_runtime import RESOURCES, load_settings, resource_setting

ROOT = RESOURCES
GROUPS = ['CorePlayer', 'HardshipPlayer', 'TwoWayPlayer', 'EuroStashPlayer']
COUNTS = ['NumberOfCorePlayers', 'NumberOfHardshipPlayers',
          'NumberOfTwoWayPlayers', 'NumberOfEuroStashPlayers']
SPECIAL_LINEUPS = [2415860247, 1120151782, 2837980651, 2849756436,
                   935612124, 4211773776, 3451166509, 4157446490]
INJURY_STATUSES = {'out': 4, 'suspension': 4, 'day-to-day': 2, 'questionable': 2, 'doubtful': 3,
                   'probable': 1, 'healthy': 0, 'active': 0}


def members(roster, team, group):
    return [v >> 32 for v in roster.teams.pointers(team, group) if v != NULL_POINTER]


def injury_values(report, types, now):
    if report is None:
        return dict(type=0, status=0, duration=0, side=None)
    status = report['status'].strip().lower()
    if status not in INJURY_STATUSES:
        raise ValueError(localize(f'未知伤病状态 {report["status"]}，保留原名单'))
    details = report.get('details', {})
    areas = {'ankle': 'ANKLE', 'knee': 'KNEE', 'foot': 'FOOT', 'hand': 'HAND',
             'wrist': 'WRIST', 'back': 'BACK', 'lower back': 'BACK',
             'hamstring': 'THIGH', 'thigh': 'THIGH', 'quad': 'THIGH',
             'calf': 'LEG', 'lower leg': 'LEG', 'leg': 'LEG', 'hip': 'HIP',
             'groin': 'HIP', 'shoulder': 'SHOULDER', 'elbow': 'ELBOW',
             'finger': 'FINGER', 'toe': 'TOE', 'neck': 'NECK', 'head': 'HEAD',
             'illness': 'ILLNESS', 'rib': 'RIB', 'ribs': 'RIB', 'abdomen': 'ABDOMEN'}
    area = areas.get(details.get('type', '').lower())
    kind = ('UNKNOWN_ILLNESS' if area == 'ILLNESS' else f'UNKNOWN_{area}_INJURY') if area else 'NO_INJURY'
    if status == 'suspension':
        kind = 'SUSPENSION'
    days = 0
    if details.get('returnDate'):
        days = max(0, (datetime.fromisoformat(details['returnDate'][:10]).date() - now.date()).days)
    return dict(type=types.index(kind), status=INJURY_STATUSES[status],
                duration=min(days*1440, (1 << 20)-1), side=details.get('side'))


def canonical_name(name):
    key = normalize(name)
    return ALIASES.get(key, key)


def injury_state(report):
    status = report['status'].strip().lower()
    # Suspension and injury-related Out both exclude play, but carry distinct types.
    return INJURY_STATUSES[status], status == 'suspension'


def injury_time(report, name):
    """Require an explicit status and timestamp before selecting a source."""
    if str(report.get('status', '')).strip().lower() not in INJURY_STATUSES:
        raise ValueError(localize('未知或缺少伤病状态：'+name))
    try:
        stamp = datetime.fromisoformat(report['date'].replace('Z', '+00:00'))
        if stamp.tzinfo is None:
            raise ValueError('missing timezone')
        return stamp
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise ValueError(localize('伤病报告日期无效：'+name)) from error


def injury_reports(snapshot):
    """Use ESPN athlete IDs across teams so transfers retain injury reports."""
    athletes = {str(a['id']): a for team in snapshot['rosters'] for a in team['athletes']}
    names = defaultdict(list)
    for athlete_id, athlete in athletes.items():
        names[canonical_name(athlete['fullName'])].append(athlete_id)
    reports, skipped, group_ids = {}, [], set()
    for group in snapshot['injuries']['injuries']:
        group_id = str(group['id'])
        if group_id in group_ids:
            raise ValueError(localize('伤病来源返回重复球队分组'))
        group_ids.add(group_id)
        for report in group['injuries']:
            athlete = report['athlete']
            athlete_id = athlete.get('id')
            if not athlete_id:
                ids = set()
                for link in athlete.get('links', []):
                    match = re.search(r'/nba/player/(?:[^/]*/)*id/(\d+)', link.get('href', ''))
                    if match:
                        ids.add(match.group(1))
                if len(ids) > 1:
                    raise ValueError(localize('同一伤病报告指向多个球员 ID'))
                athlete_id = next(iter(ids), None)
            if not athlete_id:
                matches = names[canonical_name(athlete['displayName'])]
                if len(matches) != 1:
                    raise ValueError(localize('伤病报告缺少可唯一匹配的球员 ID：'+athlete['displayName']))
                athlete_id = matches[0]
            athlete_id = str(athlete_id)
            if athlete_id not in athletes:
                skipped.append(dict(name=athlete['displayName'], source_id=athlete_id,
                                    reason='伤病报告中的球员不在当前 30 队名单中'))
                continue
            if athlete_id in reports:
                raise ValueError(localize('同一球员有重复伤病报告：'+athlete['displayName']))
            reports[athlete_id] = report
    for athlete_id, athlete in athletes.items():
        summaries = athlete.get('injuries') or []
        if not summaries:
            continue
        name = athlete['fullName']
        dated = [(injury_time(r, name), r) for r in summaries]
        latest = max(stamp for stamp, _ in dated)
        candidates = [r for stamp, r in dated if stamp == latest]
        if len({injury_state(r) for r in candidates}) != 1:
            raise ValueError(localize('同一时间的伤病状态冲突：'+name))
        summary = candidates[0]
        detailed = reports.get(athlete_id)
        if detailed is not None:
            detailed_time = injury_time(detailed, name)
            same_status = injury_state(summary) == injury_state(detailed)
            if latest == detailed_time and not same_status:
                raise ValueError(localize('同一时间的伤病状态冲突：'+name))
            if latest <= detailed_time or same_status:
                continue
        # A current roster summary is real source data, even when the aggregate
        # feed omits it. Never invent an injury site or reuse older details.
        reports[athlete_id] = dict(
            athlete=dict(id=athlete_id, displayName=name),
            status=summary['status'], date=summary['date'],
            details=summary.get('details') or {},
            _sync_source='team_roster',
            _sync_warning=('伤病汇总缺少该球员，采用球队名单的伤病状态' if detailed is None
                           else '球队名单状态更新，采用较新的伤病状态'))
    return reports, skipped


class LineupUnavailable(ValueError):
    """Valid inputs cannot form a playable local lineup; not a source/schema error."""


def record_fingerprint(table, index):
    raw=read_bits(table.data,index*table.stride,table.stride)
    return hashlib.sha256(raw.to_bytes((table.stride+7)//8,'big')).hexdigest()


def depth_lineup(eligible, desired, depth, roster=None, previous_order=()):
    """Use local roles only for retained teammates or missing source positions."""
    ranks = {p: {a['id']: rank for rank, a in enumerate(depth['positions'][p])} for p in POSITIONS}
    # Five-slot assignment preserves as many available listed starters as possible.
    # Processing each player once prevents a multi-position player taking two slots.
    local_rank={index:rank for rank,index in enumerate(previous_order)}
    local_roles=defaultdict(set)
    if roster is not None:
        # Infer role slots from the game's own original starting five. Do not
        # assume an undocumented numeric PG/SG/SF/PF/C position enum.
        for slot,index in enumerate(previous_order[:5]):
            local_roles[roster.players.get(index,'Position',3)].add(slot)
    missing_positions={p for p in POSITIONS if not depth['positions'][p]}
    states = {0: ((0, 0, 0, 0), (None,)*5)}
    for index in eligible:
        player=desired.get(index)
        athlete_id = str(player['source_id']) if player else None
        local_position=roster.players.get(index,'Position',3) if roster is not None else None
        updated = dict(states)
        for mask, (cost, chosen) in states.items():
            for slot, position in enumerate(POSITIONS):
                rank = ranks[position].get(athlete_id) if player else None
                local_role = rank is None and (player is None or position in missing_positions)
                if local_role and slot in local_roles[local_position]:
                    rank = local_rank.get(index,1000)
                if mask & (1 << slot) or rank is None:
                    continue
                target = mask | (1 << slot)
                value = (cost[0]+int(player is None),cost[1]+int(local_role),cost[2]+int(rank!=0),cost[3]+rank)
                if target not in updated or value < updated[target][0]:
                    players = list(chosen)
                    players[slot] = index
                    updated[target] = value, tuple(players)
        states = updated
    if 31 not in states:
        raise LineupUnavailable(localize('球队深度表无法组成五个位置的可出场首发，停止更新'))
    starters = list(states[31][1])
    def bench_key(index):
        if index not in desired:return (1001,local_rank.get(index,1000))
        athlete_id = str(desired[index]['source_id'])
        return min(((ranks[p][athlete_id], slot) for slot, p in enumerate(POSITIONS)
                    if athlete_id in ranks[p]), default=(1000, local_rank.get(index,1000)))
    bench = sorted((i for i in eligible if i not in starters), key=bench_key)
    return (starters + bench)[:15]


def rebuild_lineups(roster, team, eligible, pointer, desired, depth, lineup=None):
    if len(eligible) < 5:
        raise ValueError(localize(f'球队 {team} 可出场球员少于 5 人，停止更新'))
    if lineup is None:lineup = depth_lineup(eligible, desired, depth)
    roster.teams.set_pointers(team, 'LineupPlayer', [pointer(i) for i in lineup])
    roster.teams.set(team, 'NumberOfLineupPlayers', len(lineup), 4)
    for field in SPECIAL_LINEUPS:
        before = members(roster, team, field)
        chosen = [i for i in before if i in eligible]
        for old in before:
            if len(chosen) == 5:
                break
            position = roster.players.get(old, 'Position', 3)
            candidates = [i for i in eligible if i not in chosen]
            same = [i for i in candidates if roster.players.get(i, 'Position', 3) == position]
            chosen.append((same or candidates)[0])
        chosen += [i for i in eligible if i not in chosen][:5-len(chosen)]
        roster.teams.set_pointers(team, field, [pointer(i) for i in chosen[:5]])
    return lineup


def plan_team_rosters(roster, plan, owner, category, original_groups, source_values, depths, allow_fallback):
    """Resolve every team's ownership and lineup before changing any records."""
    source_desired={p['index']:p for p in plan['mapping']}
    original={t:[i for g in GROUPS for i in original_groups[t][g]] for t in range(30)}
    order={t:list(dict.fromkeys(members(roster,t,'LineupPlayer')+original[t])) for t in range(30)}
    by_team={t['team_index']:t for t in plan['teams']}
    frozen={}
    if allow_fallback:
        for team in range(30):
            if not any(p['new_team_index']==team for p in source_desired.values()):
                frozen[team]='no_source_players_matched'
    while True:
        # A preserved team's original players cannot also be transferred elsewhere.
        # Incoming moves to a preserved team keep their old owner (or remain free).
        desired={i:p for i,p in source_desired.items()
                 if owner.get(i) not in frozen and p['new_team_index'] not in frozen}
        wanted={t:set(original[t]) if t in frozen else set() for t in range(30)}
        for i,player in desired.items():wanted[player['new_team_index']].add(i)
        for i,player in source_desired.items():
            if player['new_team_index'] in frozen and i in owner:wanted[owner[i]].add(i)
        reserved=set().union(*wanted.values())
        groups={};lineups={};eligible_by_team={};new_frozen={}
        def available(index):
            if index in desired:return source_values[index]['status']!=4
            player=roster.player(index)
            return player['injury1']['status']!=4 and player['injury2']['status']!=4
        for team in range(30):
            if team in frozen:
                groups[team]={g:list(original_groups[team][g]) for g in GROUPS}
                lineups[team]=members(roster,team,'LineupPlayer')
                continue
            pool=[i for i in order[team] if i in set(original[team]) and i not in reserved]
            healthy=[i for i in sorted(wanted[team]) if available(i)]
            healthy_pool=[i for i in pool if available(i)]
            depth=depths[by_team[team]['source_team_id']]
            try:
                candidates=healthy+healthy_pool if allow_fallback else healthy
                starters=depth_lineup(candidates,desired,depth,roster,order[team])[:5]
            except LineupUnavailable:
                if not allow_fallback:raise
                new_frozen[team]='no_safe_five_position_lineup';continue
            selected=set(wanted[team])|set(starters)
            if allow_fallback:
                goal=min(23,max(5,by_team[team]['source_players']))
                for i in healthy_pool+[i for i in pool if i not in healthy_pool]:
                    if len(selected)>=goal:break
                    selected.add(i)
            proposed={g:[i for i in original_groups[team][g] if i in selected] for g in GROUPS}
            kept=set().union(*map(set,proposed.values()))
            for i in sorted(selected-kept):proposed[category.get(i,'CorePlayer')].append(i)
            if not 5<=len(selected)<=23 or any(len(proposed[g])>roster.teams.field(g).count for g in GROUPS):
                if not allow_fallback:raise ValueError(localize('球队成员数量或分类容量不足，停止更新'))
                new_frozen[team]='roster_capacity_conflict';continue
            groups[team]=proposed;wanted[team]=selected
            eligible=[i for g in GROUPS for i in proposed[g] if available(i)]
            lineups[team]=depth_lineup(eligible,desired,depth,roster,order[team])
            eligible_by_team[team]=eligible
        if new_frozen:
            # Monotonic: each retry protects at least one additional team, at most 30.
            frozen.update(new_frozen);continue
        assigned=[i for t in range(30) for g in GROUPS for i in groups[t][g]]
        if len(assigned)!=len(set(assigned)):
            raise ValueError(localize('回退规划出现跨队重复球员，停止更新'))
        return desired,groups,lineups,eligible_by_team,frozen


def update_roster(roster, snapshot):
    settings=load_settings()
    if settings.get('scope')!='NBA_ALL_30_TEAMS' or type(settings.get('allow_missing_players')) is not bool:
        raise ValueError(localize('同步设置无效，停止更新'))
    plan=make_plan(roster.container.path,snapshot)
    if plan['missing'] and not settings['allow_missing_players']:
        raise ValueError(localize('基础名单缺少球员：'+', '.join(p['name'] for p in plan['missing'])))
    source_desired={p['index']:p for p in plan['mapping']}
    if len(source_desired)!=plan['matched']:
        raise ValueError(localize('多个来源球员匹配到同一游戏记录'))
    original_groups={};owner={};category={};tags=set()
    for team in range(30):
        original_groups[team]={g:members(roster,team,g) for g in GROUPS}
        baseline_members=[i for g in GROUPS for i in original_groups[team][g]]
        baseline_lineup=members(roster,team,'LineupPlayer')
        if len(baseline_lineup)<5 or len(baseline_lineup)!=len(set(baseline_lineup)) or not set(baseline_lineup)<=set(baseline_members) or roster.teams.get(team,'NumberOfLineupPlayers',4)!=len(baseline_lineup):
            raise ValueError(localize('基础名单原有出场阵容无效，停止更新'))
        for group,count in zip(GROUPS,COUNTS):
            if roster.teams.get(team,count)!=len(original_groups[team][group]):
                raise ValueError(localize('基础名单成员数量与成员数组不一致，停止更新'))
            for raw in roster.teams.pointers(team,group):
                if raw==NULL_POINTER:continue
                index=raw>>32
                if index in owner:raise ValueError(localize('基础名单同一球员重复占用 NBA 球队名额'))
                if roster.player(index)['team_index']!=team:
                    raise ValueError(localize('基础名单球员所属球队与成员数组不一致'))
                owner[index],category[index]=team,group;tags.add(raw&0xffffffff)
    if len(tags)!=1:raise ValueError(localize('基础名单指针格式不一致'))
    tag=tags.pop();pointer=lambda index:(index<<32)|tag
    original_free={v>>32:v for v in roster.free_agents.pointers(0,0x9FB57F53) if v!=NULL_POINTER}
    free=list(original_free)
    if len(free)!=len(set(free)) or set(free)&owner.keys():
        raise ValueError(localize('基础自由球员名单重复或与球队成员冲突'))
    if len(original_free)!=len([v for v in roster.free_agents.pointers(0,0x9FB57F53) if v!=NULL_POINTER]) or roster.free_agents.get(0,0xA32E5A01,16)!=len(free):
        raise ValueError(localize('基础自由球员名单重复或数量不符，停止更新'))
    reports,skipped_reports=injury_reports(snapshot)
    types=json.loads(resource_setting(settings,'injury_types_file','injury_types.json').read_text('utf-8'))
    now=datetime.fromisoformat(snapshot['fetched_at'])
    source_values={i:injury_values(reports.get(str(p['source_id'])),types,now) for i,p in source_desired.items()}
    depths={str(t['team_id']):t.get('depth_chart') for t in snapshot['rosters']}
    for team in plan['teams']:
        depth=depths[team['source_team_id']]
        if (not depth or not any(depth.get('positions',{}).get(p) for p in POSITIONS)
                or (not settings['allow_missing_players'] and any(not depth.get('positions',{}).get(p) for p in POSITIONS))):
            raise ValueError(localize(team['team']+' 缺少出场顺序来源，请联网重新更新'))
    desired,groups,lineups,eligible,frozen=plan_team_rosters(
        roster,plan,owner,category,original_groups,source_values,depths,settings['allow_missing_players'])
    final_owner={i:t for t in range(30) for g in GROUPS for i in groups[t][g]}
    retained=set(final_owner)-desired.keys()
    preserved=dict(teams={str(t):record_fingerprint(roster.teams,t) for t in frozen},
                   players={str(i):record_fingerprint(roster.players,i) for i in retained})
    expected_injuries={i:roster.player(i)['injury1'] for i in final_owner}
    expected_secondary={i:roster.player(i)['injury2'] for i in final_owner}
    changes=[]
    for index in sorted(owner.keys()|desired.keys()):
        old=owner.get(index);target=final_owner.get(index)
        if old==target:continue
        for field in ['CurrentTeam_Internal','ContractTeam_Internal']:
            roster.players.set(index,field,NULL_POINTER if target is None else pointer(target),64)
        changes.append(dict(name=roster.player(index)['name'],uid=roster.player(index)['uid'],old_team=old,new_team=target))
    free=[i for i in free if i not in final_owner]
    free.extend(i for i in sorted(owner) if i not in final_owner and i not in free)
    if free!=list(original_free):
        roster.free_agents.set_pointers(0,0x9FB57F53,[original_free.get(i,pointer(i)) for i in free])
        roster.free_agents.set(0,0xA32E5A01,len(free),16)
    injury_log=[]
    for index,player in desired.items():
        values=source_values[index];report=reports.get(str(player['source_id']))
        expected_injuries[index]={k:values[k] for k in ['type','status','duration']}
        expected_secondary[index]=dict(type=0,status=0,duration=0)
        for key,field,bits in [('type','InjuryType1',8),('status','InjuryStatus1',3),('duration',1956514736,20)]:
            roster.players.set(index,field,values[key],bits)
        for field,bits in [('InjuryType2',8),('InjuryStatus2',3),(3986119178,20)]:roster.players.set(index,field,0,bits)
        if report:
            injury_log.append(dict(name=player['source_name'],source_id=player['source_id'],team=player['new_team'],
                team_index=player['new_team_index'],source_status=report['status'],report_date=report['date'],
                report_source=report.get('_sync_source','injuries'),details=report.get('details'),game_values=values))
    for player in plan['missing']:
        if str(player['source_id']) in reports:
            skipped_reports.append(dict(name=player['name'],source_id=player['source_id'],reason='本地没有真实球员记录，无法写入伤病'))
    skipped_mapped=[dict(**player,reason='team_preservation') for i,player in source_desired.items() if i not in desired]
    for player in skipped_mapped:
        if str(player['source_id']) in reports:
            skipped_reports.append(dict(name=player['source_name'],source_id=player['source_id'],reason='球队回退保留原名单，本次未写入该球员伤病'))
    summaries=[];fallbacks=[]
    for team_plan in sorted(plan['teams'],key=lambda t:t['team_index']):
        team=team_plan['team_index'];depth=depths[team_plan['source_team_id']]
        if team not in frozen:
            for group,count in zip(GROUPS,COUNTS):
                roster.teams.set_pointers(team,group,[pointer(i) for i in groups[team][group]])
                roster.teams.set(team,count,len(groups[team][group]))
            rebuild_lineups(roster,team,eligible[team],pointer,desired,depth,lineup=lineups[team])
        all_members=[i for g in GROUPS for i in groups[team][g]]
        local=[i for i in all_members if i not in desired]
        missing_positions=[p for p in POSITIONS if not depth['positions'].get(p)]
        if local or team in frozen or missing_positions:
            fallbacks.append(dict(team=team_plan['team'],team_index=team,
                mode='preserve_team' if team in frozen else ('local_lineup' if missing_positions else 'retain_teammates'),
                reason=frozen.get(team,'source_depth_positions_incomplete' if missing_positions else 'missing_players_or_protected_transfer'),
                missing_positions=missing_positions,retained_players=[roster.player(i)['name'] for i in local]))
        summaries.append(dict(**team_plan,matched=sum(i in desired for i in all_members),
            missing=[p for p in plan['missing'] if p['team_index']==team],player_indices=all_members,
            preserved=team in frozen,retained_indices=local,active_players=len(lineups[team]),lineup_indices=lineups[team],
            lineup=[desired[i]['source_name'] if i in desired else roster.player(i)['name'] for i in lineups[team]],
            lineup_source='preserved_local_baseline' if team in frozen else ('source_depth_with_local_positions' if missing_positions else ('source_depth_with_local_fallback' if local else depth['source'])),
            lineup_timestamp=None if team in frozen else depth.get('timestamp'),injury_reports=sum(p['team_index']==team for p in injury_log)))
    team_fields={str(i):{field:roster.players.get(i,field,64) for field in ['CurrentTeam_Internal','ContractTeam_Internal']} for i in final_owner}
    result=dict(scope='NBA_ALL_30_TEAMS',team_count=30,source_players=plan['source_players'],players=len(desired),
        matched_players=plan['matched'],roster_players=len(final_owner),coverage='partial' if plan['missing'] or fallbacks else 'complete',
        missing=plan['missing'],missing_count=len(plan['missing']),teams=summaries,transfers=changes,injuries=injury_log,
        fallback_teams=fallbacks,preserved_team_count=len(frozen),retained_player_count=len(retained),skipped_mapped_players=skipped_mapped,
        source_injury_reports=len(reports),skipped_injury_reports=skipped_reports,fetched_at=snapshot['fetched_at'],
        source_warnings=[dict(source_id=ident,name=r['athlete']['displayName'],status=r['status'],date=r['date'],reason=r['_sync_warning'])
                         for ident,r in reports.items() if '_sync_warning' in r]
            +[dict(source_id=t['team_id'],name=t['team'],status='partial_depth',date=t['depth_chart'].get('timestamp'),
                   reason='来源深度表缺少位置，使用本地位置回退；无法安全补全时保留整队')
              for t in snapshot['rosters'] if any(not t['depth_chart']['positions'].get(p) for p in POSITIONS)]
            +[dict(source_id=t['team_id'],name=t['team'],status='deduplicated_depth',date=t['depth_chart'].get('timestamp'),
                   reason='来源同位置重复球员已去重，保留首次出现顺序')
              for t in snapshot['rosters'] if t['depth_chart'].get('deduplicated_positions')],source=snapshot['source'],
        affected_teams=[t for t in range(30) if t not in frozen],preserved_records=preserved,expected_team_fields=team_fields,
        expected_injuries={str(i):v for i,v in expected_injuries.items()},expected_secondary_injuries={str(i):v for i,v in expected_secondary.items()})
    validate_roster(roster,result)
    return result


def validate_roster(roster,report):
    assigned=set()
    for team in report['teams']:
        index=team['team_index'];actual=[i for group in GROUPS for i in members(roster,index,group)]
        if actual!=team['player_indices'] or assigned.intersection(actual) or len(actual)!=len(set(actual)):
            raise ValueError(localize('回读校验：球员重复或球队成员不一致'))
        assigned.update(actual)
        for group,count in zip(GROUPS,COUNTS):
            if roster.teams.get(index,count)!=len(members(roster,index,group)):
                raise ValueError(localize('回读校验：球队人数字段不一致'))
        for player in actual:
            record=roster.player(player)
            fields={field:roster.players.get(player,field,64) for field in ['CurrentTeam_Internal','ContractTeam_Internal']}
            if record['team_index']!=index or fields!=report['expected_team_fields'][str(player)]:
                raise ValueError(localize('回读校验：球员所属球队不一致'))
            if record['injury1']!=report['expected_injuries'][str(player)]:
                raise ValueError(localize('回读校验：球员伤病字段不一致'))
            if record['injury2']!=report['expected_secondary_injuries'][str(player)]:
                raise ValueError(localize('回读校验：第二伤病槽与预期不一致'))
        active=members(roster,index,'LineupPlayer')
        if active!=team['lineup_indices']:
            raise ValueError(localize('回读校验：出场顺序与本次来源排序不一致'))
        if roster.teams.get(index,'NumberOfLineupPlayers',4)!=len(active) or len(active)<5:
            raise ValueError(localize('回读校验：活跃阵容人数不一致'))
        for values in [active]+[members(roster,index,k) for k in SPECIAL_LINEUPS]:
            if len(values)!=len(set(values)) or not set(values)<=set(actual):
                raise ValueError(localize('回读校验：阵容包含重复或非本队球员'))
            if not team['preserved'] and any(roster.player(i)['injury1']['status']==4 or roster.player(i)['injury2']['status']==4 for i in values):
                raise ValueError(localize('回读校验：Out 球员仍在活跃或专项阵容中'))
    for table,expected in [('teams',report['preserved_records']['teams']),('players',report['preserved_records']['players'])]:
        for index,digest in expected.items():
            if record_fingerprint(getattr(roster,table),int(index))!=digest:
                raise ValueError(localize('回读校验：回退保留的原始记录发生改变'))
    free=[v>>32 for v in roster.free_agents.pointers(0,0x9FB57F53) if v!=NULL_POINTER]
    if assigned.intersection(free) or len(free)!=len(set(free)):
        raise ValueError(localize('回读校验：自由球员与球队成员重复'))
    if roster.free_agents.get(0,0xA32E5A01,16)!=len(free):
        raise ValueError(localize('回读校验：自由球员人数不一致'))
    if len(assigned)!=report['roster_players'] or len(report['teams'])!=30 or len({t['team_index'] for t in report['teams']})!=30:
        raise ValueError(localize('回读校验：没有覆盖全部 30 队的可匹配球员'))
