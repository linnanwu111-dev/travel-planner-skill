# 规划工作包与当前页面的交接

`plan.json` 是会话工作包（planning_version=1），不是旧生成器的trip.json，也不是宣称已有完整v3生成器。保留资料与决定，避免每轮从聊天重建。校验命令：`python3 scripts/planning.py validate plan.json`；`assess brief.json` 判断入口与下一步；`export plan.json --out page-packet.json` 导出页面可用的结构化包。export只导出数据。生成当前C版使用 `python3 scripts/render.py plan.json --out 新目录`，拒绝覆盖已有输出。

## 最小结构

完整可运行示例见 examples/planning-demo.json（明确演示，不可作为真实出游证据）。金额以分存储，时间带时区，未知用null；ID跨版本稳定，删除节点才移除ID。

- 根：planning_version、revision、status（research/review/confirmed）、demo、brief、decisions、pending、sources、places、activities、transfers、costs、media、weather、packing。
- brief：入口的原始links、已有draft、固定fixed；origin/destination、start_date/end_date、travelers、currency、timezone。另存preferences、assumptions、预算口径与房间/票种要求。fixed存具体事件、用户确认的已订状态和时间，不存订单号。
- decisions：id、revision、scope、choice、confirmed（用户是否确认）。confirmed状态必须有当前revision的scope=itinerary确认；不是让Agent伪造确认。
- pending：id、scope、question、blocking。未确认的餐厅可保留为地点未知的活动，不能静默从地图和预算中消失。
- sources：id、kind（official/community/user/demo）、status（read/snippet/unavailable/user_provided/demo）、title、url或material、checked_at、supports（实际支持什么）。原始私有材料不打包。
- places：id、name、city、address、selection（candidate/selected/booked）、coordinates（lat/lng/crs/source_ids）或null、source_ids。已选地点需要位置才能声明路线完整；候选报价不能自动将selection变成booked。
- activities：id、kind（journey/hotel/meal/place/stay/rest）、start/end（ISO8601含时区）、place_id或null、title、fixed、source_ids；journey另存departure_place_id、arrival_place_id、booking_state。跨午夜保留真实完整时间，展示时拆日，不能截断而丢失日期。
- transfers：id、from_activity_id、to_activity_id、from_place_id、to_place_id、status（ready/unknown/stale）、recommended（方案id或null）、options、source_ids、checked_at。ready每个option含id、mode（walk/bus/car）、duration_minutes、distance_meters、price_cents或null、basis、lines、reason；不能把网约车等待隐藏在驾车时间中。
- costs：id、activity_id或transfer_id（二选一）、category、unit、quantity、low_cents/high_cents、status（quote/reference/estimate/actual/unknown）、paid_cents、source_ids、conditions、checked_at。统一币种；unknown上下限null但既有支付可留，退款另作确认记录。预算只按此表加总，活动仅引用费用ID，不再次累计。
- media：id、role（cover/place）、place_id或null、path或url、kind（photo/illustration）、use_status（permitted/reference_only/unknown）、credit、source_ids。reference_only/unknown只供Agent参考，不导出为背景。路径须在工作包目录内，不能越界；远程URL可失效，正式交付前验证可用性。
- weather：date、city、timezone、status（forecast/unknown/historical）、low/high、rain_probability、checked_at、source_ids。导出以城市+日期匹配，历史不冒充未来。
- packing：id、label（短名）、reason、source_ids；建议原因可含日期，label不堆日期串。

## 进入C版页面的映射

| 工作包 | 页面字段 / 行为 |
|---|---|
| brief | 标题、日期、人数、城市；抵离与预算上下文 |
| places | POIS、候选列表；所有选中地点预填准确坐标，底图统一WGS84 |
| activities | DAYS.locations，按日期时间排序；晚餐和stay独立，返店关联同日酒店 |
| journey endpoints | 车票卡保留两端；目的地日地图不画出发城市远端点 |
| transfers | AGENT_ROUTES：端点、适用日期、选定方案、时长/距离/费、查询日期；修改地点后失效 |
| costs | 活动/转场的费用小字；右侧按日/分类/人均汇总；不把已付再加成成本 |
| media permitted | 紧凑城市封面与卡片背景，原图入口；地图点位去重，popup可有多次访问 |
| weather+packing | 按出游日显示，随预报推导衣物雨具；勾选ID稳定 |
| decisions+pending | 交付状态/缺项摘要；数据保留来源状态，不把平台采集日志堆进卡片 |

## 当前生成器与修改交接

`render.py` 已将工作包接入 `assets/current/template.html`，不使用开发目录固定杭州数据；输出本地HTML、组件、公开数据包和可用图片。支持任意天数、日期、城市、人数、活动及逐段预算；跨午夜活动在相关日期显示，费用只在开始日期计一次。工作包可选 `days:[{date,title}]` 设置每日标题。

活动可选 `vehicle:train/plane`、`description`、`candidate_place_ids`（该活动的明确候选地点，不把所有候选混在一起）。天气可带clothing/carry。trip_id建议由Agent生成并跨修订保留；未给时按旅行基本信息生成隔离标识。

页面选择修改以稳定地点ID关联多个到访；改变地点后相关通勤和费用失效，既有支付记录保留。新增名称没有核实坐标时导航降级为地点搜索，不自动把旧坐标带过去。页面支持导出trip-changes.json，含trip_id、base_revision与用户修改；Agent须比对版本后合并，补来源与重新确认，而非直接作为新plan.json生成。

网页中的手动调整是补充。车票时间与端点、全新餐厅/酒店名称消歧、候选报价条件，由Agent按工作包核实后重新生成；页面不自带FlyAI/OpenCLI或密钥。历史trip.py与V1/V2模板留在开发仓库，不进当前分发包。

真实采集是否成功独立于渲染成功，三种真人会话需在目标项目验收。工作包样例与本地测试不作为真实数据证明。

## 酒店入住与住宿费用

入住或抵店放行李节点使用 `kind: hotel`，关联具体酒店 `place_id`；晚间返店用 `stay`。退房、取行李和酒店早餐按真实活动区分，不能因为地点相同就全部改为住宿。到酒店的交通放在相邻转场，不与住宿费用混写。

每个入住节点必须关联 `category: 住宿` 的费用记录；价格未知用 `status: unknown`、空上下限和明确的间夜数量，不填0或猜价。已查报价保留来源、日期、单位及房型/晚数条件。相同住宿订单只计一次：跨晚按一条总间夜费用或不重叠的分晚明细表示，晚间返店不另计一笔住宿。

修复已有数据时，把原住宿费用的 `activity_id` 移至对应入住节点，保留费用ID、金额、数量、来源和状态，不复制新记录。若同一酒店多次入住，应按日期和订单条件确认对应节点，不能仅按酒店名自动合并。校验器拒绝住宿费用挂到非hotel节点，以及hotel缺住宿费用；它不能仅凭名称证明活动分类或报价真实。

交付时在实际发布页核对：入住卡显示“住宿”和对应参考价/实付/待查；卡片金额与费用总览一致，跨日返店没有重复计费。单文件转换后重新检查这些数据关联。
