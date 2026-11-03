# 第三方组件与资料

**[English](../../THIRD_PARTY_NOTICES.md)** | **简体中文**

MIT 只覆盖贡献者拥有权利的原创表达。[实际实现核查](../legal/IMPLEMENTATION-REVIEW.md)已记录固定版本比对：检查的公开模块未发现复制上游实现；共用的 157 项伤病标识及顺序已从本机游戏的原生枚举独立核实。格式研究致谢与兼容事实单独记录；后续实际引入第三方实现时仍须确认对应权利。ESPN 自动采集条款和外部修改游戏的合同条款仍需单独处理，旧名单包继续排除。rc5 已移除未使用的加密存档分支和密钥。详情见[审阅记录](../legal/RISK-REVIEW.md)。

Python HTTPS 仍使用 OpenSSL，本机为 3.0.16；对应 Apache-2.0 许可和归属另行附带。Python 合并许可证本身已包含 Tcl 等条款。实际分发的其他运行库仍须保留适用许可。

- 本项目源码采用 MIT 许可，见 `LICENSE`。游戏文件、游戏数据、NBA/球队商标及 ESPN 内容不适用本项目许可。
- 侧栏的小篮球与应用图标为本项目原创矢量图形，以 MIT 许可随源码公开；来源及渲染方式见 `assets/README.md`。未使用外部照片、球队标志或嵌入字体。
- Windows 二进制包含 Python（PSF 许可）、Tk/Tcl（各自开源许可）、psutil（BSD-3-Clause）及 PyInstaller 生成的启动器（GPL 许可附带分发例外）。打包脚本会收集本机发行版许可到 `licenses` 和依赖元数据中。
- `psutil`：https://github.com/giampaolo/psutil ，`PyInstaller`：https://github.com/pyinstaller/pyinstaller 。
- 容器格式和完整性算法参考： https://github.com/u5ur/2K-Unpack-Save 。早期只读内存诊断参考： https://github.com/discobisco/2k26-Editor 。公开版不包含内存诊断工具，运行过程不注入、不修改游戏内存。
- 数据来源： https://site.api.espn.com/apis/site/v2/sports/basketball/nba 。发布包不附带 ESPN 抓取缓存、游戏名单包、游戏模型或个人存档。
- 本项目与 NBA、2K、Valve、ESPN 无隶属关系；名称用于描述兼容对象和数据来源。
