# 旅后纪念（会话内）

页面仅展示返回会话和“复制旅后任务”。不收原图、不增加生图接口、不把照片同步 TREK。

用户上传真实旅行照片并提出改图后，先看图、确认可用图片工具，复用已给出的数量与风格，默认从一张开始。可以原创建议旅行海报或自然修图；不声称已安装第三方 Skill。使用当前环境的图像工具和相应技能，不复制其他环境的私有路径。照片可能由图片服务处理并消耗额度，不宣称本地离线生图。

已核对的候选：
- [surreal-pop-collage](https://github.com/2998980-hue/surreal-pop-collage)：2026-09-22 读取原始 SKILL.md 和 LICENSE，MIT。首版保留可识别主体、来自照片的色彩和单一超现实元素这一风格方向，下面是简要改编指导；许可见 [第三方许可](../THIRD_PARTY_NOTICES.md)。
- [photo-painting](https://github.com/1499374741-arch/photo-painting)：实际Skill名为 `photo-editorial-poster`，不是仓库名。2026-09-23核对：每张照片独立制作3:4竖版海报，上半摄影、下半极简手绘。仓库未附许可证，不捆绑源码或规范提示词。
- [travel-memory-card-duo](https://github.com/carolinaaafy/travel-memory-card-duo)：前期讨论提示存在再分发/商用限制，同样未启用；不承诺双产物和透明贴纸已可用。

## 波普纪念制作

看原图后选出必须保留的主体、可改造的背景和原生色彩。保留主体的可识别特征，使用明亮平涂色块，让一个源自旅行场景的物件产生超现实尺度；不遮挡人脸。具体元素随照片变化，不套固定鲸鱼或红日。调用实际图片编辑能力，将原图作为参考输入。

检查主体是否仍可辨认、画面是否符合要求、是否出现多余肢体/乱码。需要文字时先确保工具能正确处理，失败则单独排版；只交付真实生成文件。工具不可用时提供创作方案，说明未生成图片。原会话丢失时，新会话提供摘要与照片也可继续。

## 已完成的维护测试边界

2026-09-22 使用有 Unsplash 许可的杭州风景照，实际查看原图并调用内置 imagegen 进行旅行纪念卡编辑，成功交付 PNG 并人工查看。可证明风景参考图编辑链路已跑通；用户真人照片、多人身份、九宫格一致性尚未实测。用户未指定时先完成一张，不宣称已自动发朋友圈。

## 三个风格入口（2026-09-22复核）

页面最后应准确对应 surreal-pop-collage、photo-editorial-poster（仓库photo-painting）、travel-memory-card-duo，而不是自然修图等泛称。点击仅复制会话任务，并携带skill标识；显示示例不代表已安装或已执行。

- surreal-pop-collage 当前仓库没有实际示例图片，C7使用本次imagegen原创风格演示，非作者示例。
- photo-painting 当前仓库没有示例图，页面使用本项目生成的虚构旅行场景示意 `photo-painting-preview.png`，不冒充作者示例或用户照片处理结果。示意图下保留仓库作者署名。实际调用前检查 `photo-editorial-poster` 是否可用；读取其 SKILL.md 和 references/original-prompt.md，遵守原规范逐张制作与检查，不凭仓库名猜调用名。
- travel-memory-card-duo README有两张GitHub附件示例；LICENSE.md仅许可个人非商业，禁止再分发/打包。当前私有本地预览仅链接作者托管示例与原仓库，未下载镜像或捆绑Skill；公开发布/安装包不能直接携带这些第三方素材。

三个风格都需要输入照片后另行实际制作、检查，不能用演示图冒充用户成品。

C8按用户要求去掉“原作者与示例”链接，示例图下以纯文本保留作者和GitHub仓库名。作者署名保留不等于授予额外使用许可。

复制任务必须携带完整仓库名及GitHub URL，区分仓库名与实际Skill名。当前映射：2998980-hue/surreal-pop-collage → surreal-pop-collage；1499374741-arch/photo-painting → photo-editorial-poster（子目录photo-editorial-poster/）；carolinaaafy/travel-memory-card-duo → travel-memory-card-duo。先核对已安装来源，缺失才从指定仓库获取，不按简称猜测安装来源。
