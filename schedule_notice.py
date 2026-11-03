"""Show a persistent Windows confirmation with the selected team's fixtures."""
from datetime import datetime, timezone

from fetch_source import BASE, get_json
from app_runtime import load_settings
from dialogs import show_dialog
from i18n import language,localize,tr
from usage_notice import UsageConsentDeclined

TEAM_NAMES = dict(ATL='老鹰', BOS='凯尔特人', BKN='篮网', CHA='黄蜂', CHI='公牛',
                 CLE='骑士', DAL='独行侠', DEN='掘金', DET='活塞', GS='勇士', GSW='勇士',
                 HOU='火箭', IND='步行者', LAC='快船', LAL='湖人', MEM='灰熊', MIA='热火',
                 MIL='雄鹿', MIN='森林狼', NO='鹈鹕', NOP='鹈鹕', NY='尼克斯', NYK='尼克斯',
                 OKC='雷霆', ORL='魔术', PHI='76人', PHX='太阳', POR='开拓者', SAC='国王',
                 SA='马刺', SAS='马刺', TOR='猛龙', UTAH='爵士', UTA='爵士', WSH='奇才', WAS='奇才')


def message_box(text, title, confirm=True):
    return show_dialog(title,text,confirm,tr('启动游戏') if confirm else None)


def schedule_text(root=None):
    settings = load_settings()
    team_id = str(settings.get('schedule_team_id', '13'))
    if not team_id.isdecimal():
        raise ValueError(tr('赛程球队设置无效'))
    source = settings['api_base'].rstrip('/')+'/teams/'+team_id+'/schedule'
    data = get_json(source)
    if data.get('status') != 'success' or str(data.get('team', {}).get('id')) != team_id:
        raise ValueError(tr('赛程来源返回失败或球队不符'))
    team = data['team']
    name = TEAM_NAMES.get(team['abbreviation'], team['displayName']) if language()=='zh-CN' else team['displayName']
    now = datetime.now(timezone.utc)
    fixtures = []
    for event in data.get('events', []):
        competition = event['competitions'][0]
        competitors = competition['competitors']
        own = next((c for c in competitors if str(c['team']['id']) == team_id), None)
        opponent = next((c for c in competitors if str(c['team']['id']) != team_id), None)
        if own is None or opponent is None:
            raise ValueError(tr('赛程比赛缺少主客队信息'))
        stamp = datetime.fromisoformat(event['date'].replace('Z', '+00:00'))
        status = competition['status']['type']
        other = opponent['team']
        fixtures.append(dict(id=event['id'], date=event['date'], stamp=stamp,
                             completed=status['completed'], state=status['state'],
                             opponent=(TEAM_NAMES.get(other['abbreviation'], other['displayName']) if language()=='zh-CN' else other['displayName']),
                             venue=tr('主场' if own['homeAway'] == 'home' else '客场')))
    def pick(values, latest=False):
        return (max if latest else min)(values, key=lambda f: f['stamp']) if values else None
    previous = pick([f for f in fixtures if f['completed'] and f['stamp'] <= now], True)
    live = pick([f for f in fixtures if not f['completed'] and f['state'] == 'in'])
    upcoming = pick([f for f in fixtures if not f['completed'] and f['state'] == 'pre' and f['stamp'] >= now])
    def line(label, fixture):
        if fixture is None:
            return tr(label)+': '+tr('来源暂未提供比赛安排')
        local = fixture['stamp'].astimezone()
        week=tr(['星期一','星期二','星期三','星期四','星期五','星期六','星期日'][local.weekday()])
        return (f'{tr(label)}: {local:%Y-%m-%d} {week} {local:%H:%M}\n'
                f'    {name} ({fixture["venue"]}) {tr("对阵")} {fixture["opponent"]}')
    lines = [name+' / '+tr('最近赛程'), '', line('上一场', previous)]
    if live:
        lines += ['', line('正在进行', live)]
    lines += ['', line('下一场', upcoming), '', tr('日期与时间按电脑本地时区显示。'),
              tr('可在快速比赛中选择对应对手与主客场进行模拟。'), '',
              tr('点“启动游戏”继续；点“取消”结束本次启动。')]
    details = dict(team_id=team_id, team=name, source=source,
                   previous=None if previous is None else {k:v for k,v in previous.items() if k!='stamp'},
                   upcoming=None if upcoming is None else {k:v for k,v in upcoming.items() if k!='stamp'})
    return '\n'.join(lines), details


def confirm_schedule(root):
    try:
        text, details = schedule_text(root)
    except UsageConsentDeclined:
        raise
    except Exception as error:
        raise RuntimeError(tr('赛程获取失败，已停止启动游戏。')+'\n\n'+localize(error)) from error
    return message_box(text, details['team']+' / '+tr('赛程提醒')), details
