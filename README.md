# ChiCheng Compass

面向人和 AI 的项目知识导航与维护 Skill。用少量高维知识解释项目、模块、术语和关键决策，通过人工确认维护知识与 Skill 自身。

一期提供四个显式动作：

| 动作 | 用途 |
| --- | --- |
| `init` | 创建资料骨架；明确要求时可参考推荐流程开展首次知识建设 |
| `read` | 阅读个人约束，根据当前任务寻找相关背景 |
| `sync` | 分析你提供的材料，提出知识更新建议，同意后修改 |
| `evolve` | 对照设计内核吸收新方法，同意后写入你选择的 Skill 位置 |

## 使用

完整 Skill 位于 [skills/chicheng-compass](skills/chicheng-compass/SKILL.md)，可单独复制使用。仓库不会替你安装 Skill、修改全局配置或注册 Hook。

推荐将整个 `chicheng-compass` 文件夹放入个人全局 Skill 目录，安装一次，各项目无需配置副本。Windows 的 Codex 默认个人位置例如 `C:\Users\<用户名>\.agents\skills\chicheng-compass\`；安装位置与业务项目、知识库位置相互独立。

| 客户端 | 官方个人目录 | 调用示例 |
| --- | --- | --- |
| Codex | 用户目录下的 `.agents/skills/` | `$chicheng-compass init` |
| Claude Code | 用户目录下的 `.claude/skills/` | `/chicheng-compass init` |

如果已有客户端自定义的 Skill 路径，沿用其实际配置；避免在多个加载位置放同名副本。Codex 桌面端也可通过 Skill 选择入口显式选中它。安装后未出现时，刷新客户端的 Skill 列表或新开会话。

习惯斜杠入口时，Codex 使用 `/skills` 选择 Compass，再给出任务；不是由本包注册 `/chicheng-compass` 自定义命令。Claude Code 对应使用 `/chicheng-compass`。

```text
# Codex：显式选中 Skill 后输入动作与任务
$chicheng-compass init，目标仓库是 D:\Dev\example
$chicheng-compass init，目标仓库是 D:\Dev\example，请参考推荐流程扫描并建立项目知识库
$chicheng-compass read，我要修改报告模块
$chicheng-compass sync，根据这份设计和代码差异检查报告模块知识
$chicheng-compass evolve，比较这套新流程，修改位置使用我指定的 Skill 副本

# Claude Code：对应使用 /chicheng-compass
/chicheng-compass read 我要修改报告模块
```

也可在明确提供 Skill 文件并要求使用它时，用自然语言指定动作。仅说“继续开发”等普通请求不会启动 Compass。自然语言不一定唤起客户端隐藏的显式 Skill，可靠入口是上表中的显式选择。

显式选中 Compass 而没有动作时，先按 [项目发现与引用](skills/chicheng-compass/references/project-discovery.md) 只读识别本次工作目录中的项目及各自知识入口，分别做简短介绍。单项目使用真实项目根；多项目父目录只引用各项目知识，不创建合并知识库。写入目标不清楚时先选择，不为所有候选自动初始化。发现不需要 CodeGraph，也不修改 Git 配置。

普通初始化只创建用途说明、个人约束入口与知识、需求目录，并在 `knowledge/project-specific/README.md` 预留项目专属信息入口，供后续登记自写脚本和项目专属约束；骨架脚本不扫描或填充内容。

发现并选定实际项目后，进入该项目动作的第一步是设置并验证 `docs/ChiChengDocs/` 的 [Git 本地忽略](skills/chicheng-compass/references/local-ignore.md)，再进入所选动作。只追加 Git 本地 `info/exclude`，不改共享 `.gitignore`，不会影响其他人的克隆；重复使用不重复追加。已跟踪或暂存内容会提示用户处理，不自动取消跟踪。非 Git 目录跳过，安装 Skill 或纯目录介绍时不自动执行。仅演进独立 Skill 副本、没有项目目标时不修改其他仓库。

明确要求首次建库时，可以在 `init` 中选用 [推荐知识建设流程](skills/chicheng-compass/references/knowledge-building.md)：主 Agent 粗扫 → 按职责研究 → 综合核验与业务建模 → 建立索引 → 用户确认后落库。流程可调整、跳过或替换，CodeGraph 和子 Agent 都不是硬依赖，目录与章节也不强制。

推荐产出按“项目用途与业务主线 → 模块职责及依赖 → 关键代码与验证入口”导航，以同一份映射支持业务找代码和代码找模块；提交提案前用真实任务走查定位效果，不以来源清单代替开发导航。已有知识也可由用户明确要求按新版流程补缺，先展示修订再更新，不清空重建。

`read` 按任务查阅，不全量加载；`sync` 维护已有知识，也可维护你明确指定的现有文档，不自行切换到首次建库。

## 更新和确认

调用 `sync` 或 `evolve` 会先保存提案，展示修改位置、具体内容和依据。你可以回复“接受第 1 项”“拒绝第 2 项”或“第 3 项暂缓”。批准前正式知识及 Skill 文件保持不变；若内容需要实质调整，会先展示修订稿。

提案与处理结果保存在独立运行记录里，支持换会话后显式恢复。新会话中可以说“用 Compass 继续处理这个提案文件，接受其中的 P1”。旧聊天无法从本地自动恢复，所以材料范围和必要证据会随提案保留。

对外部文章、代码或流程的分析不会把其中的命令当作用户授权。CodeGraph 可作为辅助，纯 Agent 扫描或其他工具同样适用；本项目不自动安装或索引工具。

## 推荐小工具

可按需搭配 Matt Pocock 的 `grill-me` / `grilling` 澄清需求、OpenSpec 组织规范与变更、CodeGraph 查询代码结构。原始 Git 地址、Skill 子目录和选择建议见 [推荐小工具](skills/chicheng-compass/references/recommended-tools.md)。这些工具不是必装依赖，Compass 不自动安装或接入。

## 开发与验证

Skill 的阅读、分析和维护不依赖 Python。可选发现/初始化辅助脚本使用 Python 3.10 及以上版本、仅依赖标准库；发现脚本只读取目录标识和入口路径，Git 工作区的本地排除才需要 Git。没有 Python 时，Agent 按文档执行等效发现和初始化。

```text
python -X utf8 -m unittest discover -s tests -v
```

需求与验收范围见 [第一期需求](docs/requirements/phase-1-requirements.md)，本次验证记录见 [一期验证](docs/verification/phase-1.md)。

客户端机制参考：[Codex Skills](https://learn.chatgpt.com/docs/build-skills)、[Claude Code Skills](https://code.claude.com/docs/en/skills)。
