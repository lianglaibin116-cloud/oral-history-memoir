# Oral History Memoir · 口述回忆录成书

将访谈录音、校对转写和家庭资料，整理成有来源依据的家庭回忆录。

An open-source agent skill for evidence-based family memoirs: consent, interviews, speaker review, source-linked writing, editorial review, and print delivery. The workflow references are primarily in Chinese; the skill entry point is in English.

本项目来自“岁月留声”的口述回忆录工作流，面向家庭记录者、访谈编辑和使用 AI 辅助成书的团队。核心原则是尊重讲述人意愿、保留来源、适度润色、不虚构。

## 能做什么

- 规划访谈、录音、多人转写及人工说话人确认。
- 创建授权清单、事实台账、来源登记和标准工作目录。
- 引导代理根据已核对材料组织章节，保留不确定事实与补访问题。
- 检查空事实台账、缺少来源、内部占位符和原始 Speaker 标签。
- 指导 Word/PDF 审校、适老排版、样书确认和交付归档。

这是一套 Skill、参考资料和两个命令行工具。它不内置语音识别模型、自动写书服务、图形界面或 Word/PDF 排版引擎。使用者需要自行选择转写和文档工具。

## 开始使用

获取仓库：

```bash
git clone https://github.com/lianglaibin116-cloud/oral-history-memoir.git
cd oral-history-memoir
```

在支持本地 Skill 的代理中，将这个包含 `SKILL.md` 的目录添加到该代理的技能目录。对于已经配置使用 `~/.codex/skills` 的 Codex 环境，可将仓库克隆到其下的 `oral-history-memoir` 子目录；目标目录已有同名 Skill 时先比较版本，不要覆盖本地修改。重新加载技能后调用：

```text
使用 $oral-history-memoir，检查我提供的访谈素材，先建立人物表、时间线、事实台账和待补访清单。成书用于家庭收藏，允许适度润色，但不要补写没有来源的细节。
```

也可以直接让支持读取本地文件的代理阅读 [SKILL.md](SKILL.md)，按当前任务加载其中的参考资料。不同代理的安装入口可能不同，请遵循对应客户端的安装方式。

## 独立运行工具

建议 Python 3.10 或以上。两个工具仅使用 Python 标准库，没有必需的第三方依赖，也不会主动联网或上传文件。

以下命令在仓库根目录执行。把客户项目放在仓库外，避免提交真实资料。

```bash
python3 scripts/scaffold_project.py ../memoir-workspaces/MEM-DEMO-001 \
  --project-id MEM-DEMO-001 --title "家庭回忆录"

python3 scripts/audit_project.py ../memoir-workspaces/MEM-DEMO-001 \
  --phase setup --json
```

初始化工具生成9个工作目录，以及项目元数据、空白授权清单、说话人映射表、事实台账、来源登记、质量检查单、印刷规格和留存计划。默认拒绝在非空目录内初始化。`--force` 会覆盖同名模板，仅在确认已填内容可以替换时使用。

准备终稿后的文本检查：

```bash
python3 scripts/audit_project.py ../memoir-workspaces/MEM-DEMO-001 \
  --phase final \
  --final ../memoir-workspaces/MEM-DEMO-001/07-production/manuscript.docx \
  --json
```

`--phase` 可选 `setup`、`transcription`、`draft`、`final`。发现错误时返回退出码1，否则返回0。`--json` 提供结构化检查结果。

## 工作流

授权与立项 → 访谈与录音 → 原始转写 → 人工校对说话人 → 事实台账与补访 → 分章写作 → 事实与隐私审校 → 排版与样书 → 确认后交付。

关键决定由人完成：持续同意、事实冲突、第三方敏感内容、终稿批准和印刷样书批准。

## 目录

| 文件 | 用途 |
| --- | --- |
| [SKILL.md](SKILL.md) | 代理入口与阶段规则 |
| [agents/openai.yaml](agents/openai.yaml) | 界面名称与默认调用提示词 |
| [references/workflow.md](references/workflow.md) | 完整工作流和阶段产物 |
| [references/interview-and-transcription.md](references/interview-and-transcription.md) | 访谈、录音与说话人校对 |
| [references/editorial-and-evidence.md](references/editorial-and-evidence.md) | 来源、事实和写作规范 |
| [references/production-and-delivery.md](references/production-and-delivery.md) | 排版、打样与交付 |
| [references/commercial-and-consent.md](references/commercial-and-consent.md) | 同意、使用范围与数据处理 |
| [assets/memoir-transcript.schema.json](assets/memoir-transcript.schema.json) | 结构化转写数据格式 |
| [scripts/](scripts/) | 项目初始化和可检测风险检查 |
| [tests/test_tools.py](tests/test_tools.py) | 使用临时合成材料的回归测试 |

## 检查工具的边界

- `setup` 通过只代表初始目录结构检查通过，不代表授权已签署或可接单。
- 终稿文本检查支持 `.docx`、`.md`、`.txt`。PDF不支持直接检查，须另行提取文字并逐页查看。
- DOCX检查主要读取正文XML，不覆盖页眉、页脚、批注、修订或隐藏文字审查。
- 字数指标是汉字数量和非空白字符数量，包含文档正文中提取到的目录等内容，不等同于合同约定的净正文字数。
- 事实台账检查字段和状态，不会验证音频真实性、来源文件内容或每条正文与事实的对应关系。
- 该审计器不验证转写JSON Schema。另行校验格式后，仍需检查说话人引用、编号唯一性、时间范围和真实音频。
- `pass` 不等于终稿、法律合规或印刷放行。事实、授权、隐私、页面布局和实体样书仍需人工审核。

## 测试

```bash
python3 -B -m unittest discover -s tests -v
```

测试只在系统临时目录创建合成数据，不使用真实采访、客户资料或外部服务。

## 参与贡献

欢迎修正文档、改善审计逻辑、补充方言校对经验或提供英文参考文档。请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，提交问题时仅使用合成或充分去标识化的材料。

## 开源许可

本仓库的代码与文档采用 [MIT License](LICENSE)，允许在保留许可与版权声明的条件下使用、修改和商业再分发。许可证原文见 [Open Source Initiative](https://opensource.org/license/mit)。

许可证仅覆盖本仓库提供的内容，不授予任何真实人物的姓名、肖像、声音、客户资料或第三方软件、字体、图片、模型的权利，也不代表使用者获得“岁月留声”品牌背书。项目不包含真实客户录音、书稿、商业合同、报价表或网站建设材料。
