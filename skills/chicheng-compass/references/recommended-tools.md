# 推荐小工具

以下工具按需选用，不是 Compass 的必装依赖。用户自行决定是否安装及用于哪个项目；这里只提供来源与选择建议，不执行安装、修改客户端配置或初始化代码索引。

## 原始仓库

| 工具 | 原始仓库 | Git 地址 |
| --- | --- | --- |
| Matt Pocock Skills | [mattpocock/skills](https://github.com/mattpocock/skills) | `https://github.com/mattpocock/skills.git` |
| OpenSpec | [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) | `https://github.com/Fission-AI/OpenSpec.git` |
| CodeGraph | [colbymchenry/codegraph](https://github.com/colbymchenry/codegraph) | `https://github.com/colbymchenry/codegraph.git` |

## Matt Pocock Skills：澄清需求与设计

适合在需求、范围或设计尚不清楚时，通过连续追问逐步形成共识。Compass 的个人约束和项目知识可作为讨论背景。

- [grill-me 目录](https://github.com/mattpocock/skills/tree/main/skills/productivity/grill-me)。
- [grill-me 源文件](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md)。
- [grilling 目录](https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling)。

`tree/main/skills/productivity/grill-me` 是有效的子目录浏览地址，不是独立的 Git 仓库。获取源码应使用上表中的整个仓库地址，再选择需要的 Skill。

当前 `grill-me` 是手动调用入口，其正文只委托给 `grilling`。安装时一并选取 `grill-me` 和 `grilling`，并按客户端能力确认能加载被委托的 Skill；不要仅复制入口文件就认为完整流程已经具备。具体安装方式参考 [原仓库说明](https://github.com/mattpocock/skills#readme)。

## OpenSpec：规范驱动的需求与变更流程

适合将需求、设计与实施任务组织成可持续维护的规范和变更流程。它支持 Codex、Claude Code 等开发工具，适合需要明确需求依据和实施路径的任务。

Compass 负责项目背景与长期知识，OpenSpec 负责具体需求及变更过程；可以按需将其文档作为 `read` 的阅读来源或 `sync` 的分析材料，不因推荐它而自动接入项目。

安装、版本要求和客户端接入方式见 [官方 README](https://github.com/Fission-AI/OpenSpec#readme) 与 [官方文档](https://openspec.dev/docs)。

## CodeGraph：代码结构与关系查询

这里特指 `colbymchenry/codegraph`。适合定位符号、依赖、调用链和改动影响，辅助核验项目知识涉及的实现事实。

Compass 保留高维项目知识，CodeGraph 提供代码结构层的辅助。没有它时仍可使用 Agent 扫描或其他工具；选择安装工具和为某个项目建立索引是两个独立步骤。

安装及项目索引方式见 [官方 README](https://github.com/colbymchenry/codegraph#readme)。是否接入客户端、是否创建 `.codegraph/` 由用户选择，不由 Compass 自动执行。
