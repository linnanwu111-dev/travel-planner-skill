# 研究留存与交付检查

结构校验只证明字段合法，不能证明做过查询。跨会话、压缩或更换Agent后，不能靠压缩摘要恢复“已核实”状态。

## 边查边留存

在 plan.json 同目录私有保存 evidence/ 和 research-log.json，不只记在对话里。真实打开的来源用 `sources[].evidence_path` 指向本目录内的文本摘录、脱敏接口返回或截图；保留查询时间、具体分店/票种/日期条件、对应原始URL。去掉Cookie、Key及个人订单信息，禁止把模型生成的概述伪装成原始返回。`evidence_path` 不导出到网页。

搜索摘要记 snippet，不改成 read；媒体转载不标为官方来源。原始证据丢失先重查，做不到就降低状态和相关事实的确定性。餐饮均价没有可复核证据时标 unknown，若用户同意按预算额度安排则标 estimate 并记录依据，不写成平台参考价。没有真实路线返回，不按站数编造“已核实”的时间/票价。

## 渠道记录

research-log.json 对应当前 revision，示意结构如下（示意路径不是证据）：

```json
{
  "revision": 1,
  "channels": {
    "web_images": {"status": "read", "evidence_path": "evidence/image-search.txt"},
    "xiaohongshu": {"status": "not_needed", "reason": "无用户收藏，公开资料已覆盖体验问题"},
    "dianping": {"status": "read", "evidence_path": "evidence/restaurant.txt"},
    "flyai": {"status": "not_needed", "reason": "票房已订，无待查收费景点；成交金额等待用户补充"},
    "amap": {"status": "alternative", "reason": "用户选择暂不配置API，改查地图网页", "evidence_path": "evidence/map-web.txt"}
  },
  "image_exceptions": {}
}
```

`not_needed` 必须解释实际为何不需要；`alternative` 必须记录替代来源及原因。缺工具/登录/Key时先按 channel-setup.md 检查和引导，用户明确暂不配置、拒绝、或平台风险限制后才以替代来源继续，不把“未配置”写成“无需查询”。等待配置可继续独立任务。

配图优先执行 place-images.md。封面和每个主要游览地点应有 permitted 素材；确实未找到可用图时，`image_exceptions` 用 `cover` 或地点ID作键，值含 `reason` 和 `evidence_path`，记录实际查找失败与向用户说明的内容。不得用空记录绕过搜索，不为凑图冒用不明许可图片。

## 构建与实测

先运行 `python3 <skill>/scripts/delivery_check.py <plan.json>`。它只检查留存文件存在和覆盖情况，不能鉴定内容真实；Agent仍须核对原始内容是否支持字段。confirmed 非演示工作包有缺项时，渲染器拒绝正式输出。review 草案可渲染，但会输出检查缺项，不能借改状态宣称正式完成。

在生成目录运行 `python3 serve.py`，默认只监听 127.0.0.1:8766；端口占用用 `--port 8767`。在HTTP页面实测切日、全部地图/当日地图、图片、独立天气与穿衣卡、费用编辑保存、勾选刷新、导航弹层、导出及手机宽度。在私有 `browser-check.md` 记录实测环境、结果和截图路径，未测项如实写未测。不能把单纯代码检查算成点击成功。

已有托管地图时，file:// 与HTTP页面均加载HTTPS签名地图，需网络连接；以实际图片成功显示验收。没有托管地图的旧瓦片模式下，直接 file:// 阅读不请求在线底图；HTTP仍可能被瓦片服务拒绝。遇到错误停止加载底图、保留地点连线和导航；遇到返回正常PNG的拦截图，使用“底图显示异常”按钮隐藏，并记录为底图未通过。不能以连线存在代替真实地理底图验收，不伪造Referer或身份绕过限制。正式交付仍需明确实际底图可用性。

票房已订不等于已知成交价，用户未给金额可继续保留待查并允许手动填写。不要为了完成预算去查当前报价冒充用户实际支付额。

## 最终入口不能沿用本地验收

发给用户的平台预览或发布链接必须单独验收；完整目录在 localhost 正常，不证明单文件附件预览能加载 assets/ 和 media/。入口或资源打包方式变化后按 deploy.md 重测。browser-check.md 分别记录本地、平台预览、正式链接的结果及未测项；费用/清单“显示正常”不能写成“编辑保存通过”。单文件预览资源丢失时，按 deploy.md 保留目录版并制作自包含版，或使用完整站点托管，不交付裸模板。
