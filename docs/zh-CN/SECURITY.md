# 安全与隐私

**[English](../../SECURITY.md)** | **简体中文**

当前只接受未加密 NBA 2K27 SYNC 名单，加密存档会拒绝。HTTPS 数据来源可以看到 IP 等正常连接信息，工具没有应用遥测服务。公开私密反馈入口尚未配置时，通过维护者提供的私密渠道报告敏感问题。

程序不请求 Steam 密码、2K 登录信息或 API 密钥。不注入进程、不改 EXE、驱动、反作弊或 Steam Cloud 配置。

配置和日志可能包含本机文件路径。公开反馈优先使用界面导出的脱敏诊断摘要；提交源码前确认 settings.local.json、数据目录、基准、备份与缓存未包含在内。

使用者提供自己的原生名单文件；程序验证清单、长度、MD5、容器节点及布局后修改目标。对未知格式与外部更改停止写入。不要从不可信来源导入兼容档案或名单。

本版本不运行后台更新服务或远程下载可执行代码，未配置自动发布或自动升级。

敏感安全问题请通过 [GitHub 私密漏洞报告](https://github.com/c01-in/roster-beacon/security/advisories/new)提交。非机密的权利或下架问题可用 [Rights concern 表单](https://github.com/c01-in/roster-beacon/issues/new?template=rights_concern.yml)。公开 issue 请勿包含个人信息、凭据或游戏文件。
