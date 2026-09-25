# Agent与当前C版交接

唯一分发接口见 [规划工作包](planning-handoff.md)。先validate，再用render.py生成新目录。所有字段由工作包回填，不修改开发目录的DAYS、POIS或AGENT_ROUTES常量。旧预览接口仅留开发记录。

通勤必须准确关联相邻活动与POI；未知不估成真路线。地点改变后更新坐标、活动、路线与费用，再增加revision。网页调整导出后按trip_id/base_revision检查冲突，不直接覆盖用户已订安排。
