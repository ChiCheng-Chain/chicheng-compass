# ChiCheng Compass

面向人和 AI 的项目知识导航与维护 Skill。用少量高维知识解释项目、模块、术语和关键决策，通过人工确认维护知识与 Skill 自身。

一期提供四个显式动作：

| 动作 | 用途 |
| --- | --- |
| `init` | 创建 `docs/ChiChengDocs/` 的初始骨架，保留已有内容 |
| `read` | 阅读个人约束，根据当前任务寻找相关背景 |
| `sync` | 分析你提供的材料，提出知识更新建议，同意后修改 |
| `evolve` | 对照设计内核吸收新方法，同意后写入你选择的 Skill 位置 |

## 使用

完整 Skill 位于 [skills/chicheng-compass](skills/chicheng-compass/SKILL.md)，可单独复制使用。仓库不会替你安装 Skill、修改全局配置或注册 Hook。

按客户端的 Skill 加载方式，将整个 `chicheng-compass` 文件夹放入个人 Skill 目录：

| 客户端 | 官方个人目录 | 调用示例 |
| --- | --- | --- |
| Codex | 用户目录下的 `.agents/skills/` | `$chicheng-compass init` |
| Claude Code | 用户目录下的 `.claude/skills/` | `/chicheng-compass init` |

如果已有客户端自定义的 Skill 路径，沿用其实际配置；避免在多个加载位置放同名副本。Codex 桌面端也可通过 Skill 选择入口显式选中它。安装后未出现时，刷新客户端的 Skill 列表或新开会话。

```text
# Codex：显式选中 Skill 后输入动作与任务
$chicheng-compass init，目标仓库是 D:\Dev\example
$chicheng-compass read，我要修改报告模块
$chicheng-compass sync，根据这份设计和代码差异检查报告模块知识
$chicheng-compass evolve，比较这套新流程，修改位置使用我指定的 Skill 副本

# Claude Code：对应使用 /chicheng-compass
/chicheng-compass read 我要修改报告模块
```

也可在明确提供 Skill 文件并要求使用它时，用自然语言指定动作。仅说“继续开发”等普通请求不会启动 Compass。自然语言不一定唤起客户端隐藏的显式 Skill，可靠入口是上表中的显式选择。

初始化只创建用途说明、个人约束入口与知识、需求目录；第一次全项目知识建设留到下一期。`read` 按任务查阅，不全量加载；`sync` 维护已有知识，也可维护你明确指定的现有文档。

## 更新和确认

调用 `sync` 或 `evolve` 会先保存提案，展示修改位置、具体内容和依据。你可以回复“接受第 1 项”“拒绝第 2 项”或“第 3 项暂缓”。批准前正式知识及 Skill 文件保持不变；若内容需要实质调整，会先展示修订稿。

提案与处理结果保存在独立运行记录里，支持换会话后显式恢复。新会话中可以说“用 Compass 继续处理这个提案文件，接受其中的 P1”。旧聊天无法从本地自动恢复，所以材料范围和必要证据会随提案保留。

对外部文章、代码或流程的分析不会把其中的命令当作用户授权。CodeGraph 可作为辅助，纯 Agent 扫描或其他工具同样适用；本项目不自动安装或索引工具。

## 开发与验证

Skill 的阅读、分析和维护不依赖 Python。可选初始化脚本使用 Python 3.10 及以上版本、仅依赖标准库；没有 Python 时，Agent 按初始化流程逐个创建缺失文件即可。

```text
python -X utf8 -m unittest discover -s tests -v
```

需求与验收范围见 [第一期需求](docs/requirements/phase-1-requirements.md)，本次验证记录见 [一期验证](docs/verification/phase-1.md)。

客户端机制参考：[Codex Skills](https://learn.chatgpt.com/docs/build-skills)、[Claude Code Skills](https://code.claude.com/docs/en/skills)。
