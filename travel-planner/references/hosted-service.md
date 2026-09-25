# 托管查询服务（优先使用）

当前备案期间的受控联调入口：https://124.221.232.250 （HTTPS IP专用证书，自动续期）。正式域名保留为https://www.xiaotouai.online，备案接入通过后再切回。此IP入口用于继续测试，不作为已完成备案的正式发布承诺。高德与FlyAI上游密钥留在服务器。Agent查询，页面展示结果；不让用户为了这些查询重复安装FlyAI或申请上游Key。

## 一次性访问准备

先检查 `~/.travel-planner/service.json` 是否存在（不输出token），查询 `/health` 只证明网络通。已有凭证直接查询。无凭证时告知用户领取旅行服务访问凭证，在本机运行 `python3 <skill>/scripts/service.py configure` 隐藏输入；不要把维护者凭证写入安装包。当前为限额内测服务，其他电脑/用户仍需自己的访问凭证。

HTTP 401凭证无效；429限额/并发满，停止连续重试；上游失败记录实际原因，不编造结果。服务不能访问时先报告，不把“有服务URL”当成查询过；按用户选择再用自有Key方式接力。小红书/点评仍由用户授权的浏览器读取。

## 查询与留存

将查询条件写入私有工作目录 request.json，然后运行：

```bash
python3 <skill>/scripts/service.py query hotels --input request.json --out evidence/hotels.json
```

类型和JSON字段：
- places：`{"city":"长沙","keyword":"橘子洲"}`
- routes：`{"origin":"经度,纬度","destination":"经度,纬度","city":"长沙","mode":"transit"}`；mode支持walk/car/transit，坐标必须GCJ02。
- trains：`{"origin":"上海","destination":"长沙","date":"2026-10-01","seat":"二等座"}`
- hotels：`{"city":"长沙","check_in":"2026-10-01","check_out":"2026-10-03","keyword":"全季酒店","bed":"twin","max_price":"600"}`

脚本内部使用curl，认证头通过标准输入传入，不写到命令参数或返回文件。返回 `queried_at/conditions/result`。来源记录 evidence_path 指向这个实际返回文件，分别标明amap或flyai。核对结果是否匹配日期、车站、酒店分店和房型；酒店列表价缺计价单位时不能直接乘晚数冒充总价，床位不能当双人整间。路线耗时是查询参考，国庆需留缓冲。

## 地图到当前C版页面

地点确认后，保留坐标真实的crs字段。高德返回GCJ02；已有WGS84由脚本按随包coordtransform公式转换，不直接改标签。按本地旅行时区提取每日地点；跨城远端车站不纳入目的地地图。生成地图数据包：

```bash
python3 <skill>/scripts/service.py prepare-maps plan.json --out plan-with-maps.json
python3 <skill>/scripts/render.py plan-with-maps.json --out 新攻略目录
```

此步骤生成每天和全部总览的专用地图链接。页面自动优先显示它们，不请求OSM；无需在浏览器放查询凭证。图片为高德真实静态底图，带地点标记和游览顺序连线，不代表实际道路路径。支持当日/全部切换、按钮缩放和拖动后更新底图，暂不支持双指缩放和点击标记弹窗；实际导航仍走每个活动的导航按钮。

新生成链接有效至返程后第90天结束（北京时间，以返回的expires_at为准），分享链接的人可查看对应地图，但不能凭它发起任意查询。不要把地图图片或底图批量打包缓存进Skill。到期重新prepare-maps；新版prepare-maps把行程地点和已核实候选坐标加入签名许可范围。网页切换这些候选或调整行程范围内车站/时间后，可用签名链接请求新布局与真实底图，自动更新标记、连线、视野；不携带服务凭证，也不能用签名查询任意新坐标。通勤费用与耗时仍需重查。旧链接不具备候选许可时须重新prepare-maps；新增名称缺坐标时保留其余已知地点地图并提示待核。旧链接不会自动延长，需要重新prepare-maps并发布网页；正文、预算与普通本地素材不随地图链接到期。

浏览器验收需要实测 HTTPS图片加载、当日/全部切换、长路线是否裁出视野、未知坐标、修改地点失效、图链接失效提示。TLS健康检查不能代替地图验收。

连接失败诊断：service.py仅在HTTPS连接失败后，对公开HTTP /health发送一次无凭证、无行程数据的诊断请求，不跟随重定向；若实际返回DNSPod备案拦截地址则提示维护者处理备案接入。否则原因保持未知。不能把诊断HTTP当业务降级通道，也不能因维护者域名受阻要求用户反复更换上游Key。

客户端默认使用当前IP联调入口；维护者确认域名恢复后，可设置环境变量TRAVEL_SERVICE_URL=https://www.xiaotouai.online。仅允许这两个已配置HTTPS入口，不降级HTTP，不跳过证书验证。服务器生成地图地址也必须同步切换，并重新prepare-maps/发布旧网页；单改客户端不会迁移旧网页中的域名链接。IP TLS证书约6天有效，由服务器每6小时检查续期；这与行程地图签名的返程后90天保留期是两回事。
