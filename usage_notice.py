"""Local, revocable first-use acknowledgement before data access or roster edits."""
from datetime import datetime, timezone
import json
import threading
from urllib.parse import urlsplit

from app_runtime import config_path, load_settings
from dialogs import show_dialog
from i18n import tr

NOTICE_REVISION = '2026-11-02.1'
RIGHTS_CONTACT = 'https://github.com/c01-in/roster-beacon/issues/new?template=rights_concern.yml'
_lock = threading.Lock()


class UsageConsentDeclined(RuntimeError):
    pass


def source_base(settings):
    base = str(settings['api_base']).strip().rstrip('/')
    parsed = urlsplit(base)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError(tr('数据来源必须是有效的 HTTPS 地址，且不包含登录凭据。'))
    return base


def consent_path():
    path = config_path()
    return path.with_name(path.stem+'.usage-consent.json')


def notice_text(settings=None):
    settings = settings or load_settings()
    return tr('默认来源：ESPN；当前接口：{source}',source=source_base(settings))+'\n\n'+tr(
        '请求由本机直接发出，获取名单、伤病、出场顺序及赛程，并可更新本机游戏名单。仅使用本地缓存时不发起数据请求。工具与 ESPN、NBA、2K 无隶属关系。')+'\n\n'+tr(
        '数据采集：ESPN 条款限制未经许可的自动获取，本项目尚未取得相应许可。游戏修改：2K 条款限制外部修改，可能产生条款争议、下架要求或账号措施。')+'\n\n'+tr(
        '继续表示你已了解这些说明，并自愿选择本工具执行获取和更新；此确认不代表网站或游戏厂商授权。取消将结束本次操作，不会写入名单或启动游戏。')+'\n\n'+tr(
        '权利人可通过公开仓库的 Rights concern 表单联系维护者。收到请求后，我们会优先暂停相关分发或功能、核查并及时下架或修正。该处理流程不承诺免除责任。')+'\n'+tr(
        '权利人联系：维护 → 关于 → 权利人联系。')


def show_notice():
    show_dialog(tr('数据来源与使用说明'), notice_text())


def open_rights_contact():
    import webbrowser
    webbrowser.open(RIGHTS_CONTACT)


def revoke_consent():
    with _lock:
        consent_path().unlink(missing_ok=True)


def ensure_usage_consent(requested_url=None):
    with _lock:
        settings = load_settings()
        base = source_base(settings)
        if requested_url is not None and requested_url != base and not requested_url.startswith(base+'/'):
            raise ValueError(tr('请求地址与已配置的数据来源不符，已停止联网。'))
        path = consent_path()
        expected = dict(notice_revision=NOTICE_REVISION, api_base=base,
                        compatibility_profile=settings['compatibility_profile'])
        try:
            accepted = json.loads(path.read_text('utf-8'))
        except (OSError, ValueError):
            accepted = {}
        if isinstance(accepted, dict) and all(accepted.get(k) == v for k, v in expected.items()) and accepted.get('accepted_at'):
            return
        if not show_dialog(tr('首次使用：数据来源与使用说明'), notice_text(settings), True, tr('我已了解，自愿继续')):
            raise UsageConsentDeclined(tr('已取消本次操作，名单保持原样，本工具未启动游戏。'))
        record = dict(**expected, accepted_at=datetime.now(timezone.utc).isoformat())
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        temporary.replace(path)
