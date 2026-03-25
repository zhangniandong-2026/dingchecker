# 文档索引

本目录存放 DingChecker 的使用说明、环境配置和历史改造记录。

当前仓库的默认主链已经是：

`DingTalk / AI 听记 -> 结构化 JSON -> HTML 报告`

因此阅读文档时，建议优先关注和 `JSON / HTML / Chrome CDP / google-genai` 相关的内容。

## 推荐优先阅读

- [使用指南](/Users/zhangniandong/repos/dingchecker/docs/使用指南.md)
- [AI_ANALYSIS_SETUP.md](/Users/zhangniandong/repos/dingchecker/docs/AI_ANALYSIS_SETUP.md)
- [代理配置说明.md](/Users/zhangniandong/repos/dingchecker/docs/代理配置说明.md)
- [MEETING_STANDARDS_3PLUS1.md](/Users/zhangniandong/repos/dingchecker/docs/MEETING_STANDARDS_3PLUS1.md)

## 和当前版本强相关的主题

- 晨会评估标准与“3+1”模板
- Gemini / Google Gen AI SDK 配置
- Chrome 远程调试与钉钉登录态复用
- HTML 报告与结构化 JSON 输出

## 说明

本目录中部分文档保留了历史改造记录和阶段性方案，用于追溯问题背景。

如果你只想快速了解“现在怎么跑”，优先看：

1. 根目录 [README.md](/Users/zhangniandong/repos/dingchecker/README.md)
2. [skill/README_GITHUB.md](/Users/zhangniandong/repos/dingchecker/skill/README_GITHUB.md)
3. [使用指南](/Users/zhangniandong/repos/dingchecker/docs/使用指南.md)

## 当前已知边界

- 依赖 Chrome CDP 和已登录钉钉会话
- 推荐 Python `3.10+`
- 默认产物是 `HTML + JSON`
- `TXT / PDF` 已降级为兼容产物
- “单人发言超过 2 分钟”提醒能力已接入，但依赖转写页时间轴可提取性
