# 报价、天气与携带清单

首次调用前按 [环境准备与用户接力](channel-setup.md) 检查依赖、浏览器与授权；只提示缺失步骤，完成后恢复原查询。

## FlyAI 只读接入

先读取官方当前 Skill 与子命令帮助：https://github.com/alibaba-flyai/flyai-skill/tree/main/skills/flyai 。按可用环境使用 FlyAI，不要求所有用户安装。已验证 CLI 1.0.16 可用以下查询（日期是维护测试示例，不是默认旅程）：

```bash
npx --yes --package @fly-ai/flyai-cli@1.0.16 flyai search-hotel --help
npx --yes --package @fly-ai/flyai-cli@1.0.16 flyai search-hotel --dest-name 杭州 --poi-name 西湖 --check-in-date 2026-10-01 --check-out-date 2026-10-03 --hotel-bed-types twin --sort rate_desc
npx --yes --package @fly-ai/flyai-cli@1.0.16 flyai search-train --origin 上海 --destination 杭州 --dep-date 2026-10-01 --seat-class-name 二等座 --dep-hour-start 8 --dep-hour-end 11
```

只读查询，不下单。保留实际查询参数、时间、结果及 systemMessage。筛选前核对出发/到达站与日程，不能把“上海”搜索结果中的任意车站当上海虹桥。按旅行节奏限定合理时段，不直接选返回的第一趟凌晨车。

本次本机曾遇到 Node `UNABLE_TO_GET_ISSUER_CERT_LOCALLY`；使用系统已有 CA 文件 `NODE_EXTRA_CA_CERTS=/etc/ssl/cert.pem` 后查询成功。这是本机修复记录，不能通用于所有系统；禁止用 `NODE_TLS_REJECT_UNAUTHORIZED=0` 掩盖问题。

早期体验模式响应酒店/火车价格曾含 `¥5xx`、`7x`，不是精确成交价。不得解析为 5 元/7 元，也不擅自还原具体金额。缺房型/是否含早/退改/余票时标条件未全、价格未知，提供候选原链接。酒店按房数×晚数，车票按人数×程数，不能重复乘人数。只有来源明确给出区间时才录入区间；自拟金额必须标 `estimate` 并解释假设。点评人均仅作餐饮参考价，团购与普通菜单不能混算。未查到餐饮信息就保留未知。

## 天气与穿衣

日期必须对上，记录获取日/地点/时区。可用官方气象或 Open-Meteo（https://open-meteo.com/en/docs）查询每日最低/最高温、降水概率，注明是远期预报而非保证。天气格点不是景点实测温度。超出支持区间或返回 null 则未知，提供条件建议并安排出发前复查。

穿衣由天气和活动一起推导，明确是建议：凉爽早晚分层、步行穿已穿合脚的鞋；有雨带折叠伞及电子设备防水袋；暴晒带帽子和个人适用防晒。怕冷/老人小孩等需求采用用户信息，不自行推断健康状况。提醒旅行证件、预约凭证、充电器等，不采集身份证号/验证码。药品仅提醒个人平时使用的用品，不自行开药。

晴雨两套游览安排需考虑室外暴露、步行距离与开放情况；关闭或拥挤时选择就近替代，不默认生成拍照指导。

## 价格页面有数字但带登录提示

若真实日期查询页展示车次和数字，同时提示登录核验或显示抢票，可以作为 reference 记录页面数字与冲突条件，不标为可购买 quote。明确座席、车站、时间、日期、查询时间。小计旁保留未报价项目，不能把参考小计写成全程总预算。

## 景区门票

景点确定后优先用FlyAI查询门票，职责和日期限制见channel-playbook.md。已核对官方Skill的search-poi参考：结果可含ticketInfo.price、priceDate、ticketName与jumpUrl；示例price为null，不能据此承诺每次有报价。CLI 1.0.16帮助确认无日期筛选参数。

```bash
npx --yes --package @fly-ai/flyai-cli@1.0.16 flyai search-poi --city-name 杭州 --keyword 雷峰塔
npx --yes --package @fly-ai/flyai-cli@1.0.16 flyai keyword-search --query '杭州 雷峰塔 2026年10月1日 成人单门票'
```

上述为查询用法，非本轮已执行的真实门票查询。回填costs时关联对应景点activity_id，category使用景点类别，quantity按适用票种人数，conditions记录使用日期、票种、包含/不含项目、退改与未核实条件。票种不同分行；联票只计一次。priceDate不匹配时不得写成游玩日精确报价。没查到不等于免费。

依据：https://github.com/alibaba-flyai/flyai-skill/tree/main/skills/flyai ，本机CLI帮助核对于2026-09-23。
