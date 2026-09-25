# 小红书资料接入

职责为用户收藏解读和少量关键体验补查；默认图片采集改走 [公开网页配图](place-images.md)。不要为每个景点反复搜索笔记或下载图片。公开资料足够时无需主动访问小红书。

用户曾在 MediaCrawler 登录/采集时遭遇风险警告。本 Skill 不以 MediaCrawler 为默认依赖，不自动安装爬虫，不用切账号、代理、复制 Cookie、私有 API 重放来恢复被拦的采集。更换工具不能证明无账号风险。

## 默认路径

1. 用户给分享文字/截图：直接分析可见内容。逐条保留材料名与原帖链接；截图正文不完整就记录缺失，不推断被截断部分。图文笔记须看图片中的路线表/地点标注，不能只读配文。无法识别的小字列待确认。
2. 用户给 URL（含 xhslink 短链）：用现有可用浏览器打开，让浏览器处理跳转；不猜帖子 ID 或丢弃访问所需参数。读得到标题和正文才记 `read`，只有搜索摘要记 `snippet`，只见登录界面或空页面记 `unavailable`。
3. 主动调研：先用通用网页搜索找候选，如“城市 区域 国庆 路线 年份”“城市 地点 游玩 体验”。`site:xiaohongshu.com` 只是发现链接，不是读过正文。用户已授权可用的常用浏览器时，可以正常浏览少量结果并精读最相关条目。不要建立新的自动化登录环境来复用原账号。
4. OpenCLI 是可选增强：环境本来可用时先检查实际帮助和连接，之后只用搜索、详情读取。没有环境就说明缺口，不把安装扩展变成所有用户的前置任务。

普通扫码登录可暂停并请用户在同一官方页面完成，确认后继续。验证码、频繁操作、访问拒绝或风控提示立即停机，不换工具继续撞。具体节奏、人工接力及状态记录见 [浏览器调研](browser-research.md)。

## 可复用的 OpenCLI 操作

2026-09-22 已读 [官方 adapter 文档](https://github.com/jackwener/OpenCLI/blob/main/docs/adapters/browser/xiaohongshu.md)。下面为文档示例，不代表当前机器已安装/已连通。执行前验证当前版本的参数：

```bash
opencli --version
opencli doctor
opencli xiaohongshu search --help
opencli xiaohongshu note --help
```

通过后按实际帮助使用只读命令：

```bash
opencli xiaohongshu search '杭州 西湖 游玩' --limit 3 -f json
opencli xiaohongshu note '从结果或用户分享中取得的完整真实URL'
```

官方说明详情读取需要完整带访问参数的 URL，裸 ID 不可靠。访问参数只用于当前读取，不写进公开攻略或日志；发布时优先使用用户原始分享短链，或已验证可用的公开链接。若无可公开且可用链接，保留标题/材料引用与复制搜索词，并明确原帖无法直接分享。

借鉴 `hiyeshu/trip-map-builder` 的“先筛选，再精读”与按地区选餐厅思路；不复用其硬编码本机路径、调试端口、拦截接口和提取 token 代码。库里的“更稳定”是作者经验，不是本项目验证结果。

## 分析产物

逐条提取：城市/地点/地址线索、路线先后、建议时段、排队和预约、餐饮区、体验限制、发布日期、可见热度与单位、来源状态。未知值保留未知，不编造评分。

将事实映射进 `trip.sources` 与 `places.source_ids`；图片参考用规划工作包 `media.source_ids` 单独追溯。跨帖去重后按地理区域合并，不把多个作者的“单日路线”直接串成一天。用户必去点与帖子冲突时解释取舍。不默认生成拍照机位指导；素材有来源不等于取得公开使用许可。

## 候选工具取舍

| 工具 | 已核对内容 | 首版决定 |
|---|---|---|
| OpenCLI | 需要已登录 Chrome 和 Browser Bridge；有 search/note | 本项目9/22已做小样本连接验证；每次仍须检查当前会话 |
| xpzouying/xiaohongshu-mcp | 需要登录，单独浏览器/服务方案 | 不默认引入；没有更低风控的独立证据 |
| xpzouying/x-mcp | 扩展加第三方账号/Token；README 主要是发布 | 不采用为调研依赖，搜索正文能力待核验 |
| RedSkill | 安装地址本轮读取失败 | 未核验，不运行远程安装脚本 |
| MediaCrawler | 用户报告过风险警告 | 默认停用 |

官方来源：
- https://github.com/jackwener/OpenCLI/blob/main/docs/adapters/browser/xiaohongshu.md
- https://github.com/jackwener/OpenCLI/blob/main/docs/adapters/browser/dianping.md
- https://github.com/xpzouying/xiaohongshu-mcp
- https://github.com/xpzouying/x-mcp
- https://raw.githubusercontent.com/hiyeshu/trip-map-builder/main/references/xhs-research.md
