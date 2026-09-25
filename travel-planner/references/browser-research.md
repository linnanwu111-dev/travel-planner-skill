# 小红书与点评：人工登录、少量读取、可追溯结果

首次调用前按 [环境准备与用户接力](channel-setup.md) 检查依赖、浏览器与授权；只提示缺失步骤，完成后恢复原查询。

本流程供旅行调研使用；不执行发布、点赞、收藏、关注、私信或账号数据导出。

## 工具连接与人工接力

优先复用已登录的常用 Chrome。检查 OpenCLI 版本、doctor 和具体命令帮助。OpenCLI 不是官方数据接口，支持 adapter 不等于已登录或不触发风控。

普通登录页：暂停该平台操作，展示官方页面给用户扫码。用户确认完成后，在同一浏览器核验登录态，再继续。不要让用户在聊天里提供密码、Cookie、令牌或完整会话参数。普通登录与验证码、风险警告、频次限制必须分开记录。

风险/验证码/拒绝访问：停止该平台采集，保留已读材料并说明提示；不换账号、网络或浏览器继续撞，不循环重试，不用指纹伪装或验证码自动解答。人工处理完成不自动视为授权重新采集，恢复时重新确认状态。

FlyAI 是独立 CLI/API 通道。网页扫码与 API Key 权限不是同一件事；体验模式掩码价必须保留未知。正式 Key 只在用户本机的 FlyAI 配置中设置，不让用户发到聊天或写入可分享攻略。

## 采样节奏

- 同一平台串行，仅一个进行中的操作。首轮一个关键词、最多3条结果，精选最多3篇详情；不抓全站、评论全集和用户历史。
- 两次操作间随机等待15–30秒，页面就绪后再进行下一步。此数值是本项目保守采样设置，不是平台公布的安全阈值，也不保证不触发风控。
- 只做任务需要的页面点击、阅读和滚动，不增加伪造人类行为的随机动作。
- 同一帖子已有有效证据就复用，避免重复读取；跨日价格与时效信息需重新确认。
- 单平台每日最多2次搜索、3次详情；不足时先交付当前证据与缺项，不重建状态目录绕过计数。

维护一个固定的本地私有状态目录（不放在网页输出/安装包），每次操作前调用：

```bash
python3 <skill>/scripts/research_gate.py --state-dir <固定私有状态目录> --platform xiaohongshu search
```

仅 `allowed=true` 才执行读取；`pacing` 返回等待秒数时等待后重查。操作后必须 report：

```bash
python3 <skill>/scripts/research_gate.py --state-dir <固定私有状态目录> --platform xiaohongshu report --outcome success
```

支持 login_required、verification_required、risk_blocked、rate_limited、access_denied、technical_error、empty_result。普通登录经用户确认完成后调用 login-completed；其他停机状态不会自动解除。脚本只控制节奏和状态，不解析浏览器页面，调用者必须检查真实页面结果。持久化只存计数、时间和状态，不存身份信息。

## 小红书

根据本机帮助使用 `opencli xiaohongshu search '<城市 景点 拍照>' --limit 3 -f json` 和 `note '<真实完整URL>'`。访问参数只用于当前浏览器读取，不输出到聊天、公开日志、分享文件。搜索前排不等于推荐质量，详情需核对城市、具体地点、发布日期和原文。遇普通登录走人工接力，不先发API请求试探。原帖图片可分析不等于可再发布；网页配图优先自有、明确许可或可合规引用素材，保留出处在数据中。

## 大众点评

`opencli dianping search '<区域 午餐>' --city 杭州 --limit 3 -f json`，然后对精选店用 `shop '<真实shop_id>' -f json`。评分、人均、地址、营业时间和评价数只写实际返回/页面可见值；缺字段为null。登录/验证见上。餐厅由行程区域决定，不为评分绕远。每顿1个主选和1个备选，点评硬信息与小红书体验分别引用。

## 证据与验收

记录来源、查询时间、搜索条件、读取状态、事实、未知字段。原帖标题/正文/图片分别标记是否读到。完整验收至少有1条实际搜索结果与1篇实际详情（点评为店铺详情）；doctor通过、网页打开或脚本退出0都不能代替。

参考：
- https://github.com/jackwener/OpenCLI/tree/main/clis/xiaohongshu
- https://github.com/jackwener/OpenCLI/tree/main/clis/dianping
- https://github.com/DeliciousBuding/xiaohongshu-skill/blob/main/README_EN.md （参考停机和人工验证；未安装运行）
- https://github.com/jackwener/xiaohongshu-cli/blob/main/SKILL.md （参考串行和间隔；不使用其Cookie提取、签名和自动重试）

## 已验证的适配器注意事项（2026-09-22）

OpenCLI 上游 note 命令使用的 readXhsDetailPage 默认 retryOnBlock=true，会在安全限制后再开一次页面。本项目不得直接沿用该默认行为：详情使用 browser open 单次打开搜索返回的真实链接，再在原页面读取可见 DOM；或在明确支持的适配器中设置 retryOnBlock=false。遇阻立即报告并停止，不用随机等待后自动重试。搜索摘要与详情可能不同，本次点评搜索评分4、详情4.4，分别保留，展示更具体的详情值并标注查询时间。轮播图DOM可能有克隆节点，应以可见分页核对张数，不能直接用img节点计数。
