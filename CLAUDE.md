# 简历优化项目约定

- 主流程入口为 `/resume-workflow`，流程定义位于 `.claude/skills/resume-workflow/SKILL.md`。用户以自然语言请求完整流程时，告知此入口。
- 主代理负责输入选择、目录创建、用户确认、结果复核和任务状态记录；jd-analyst 负责截图转录与 JD 分析，jd-optimize 负责证据匹配与修改提案，resume-builder 负责落实已确认的建议并生成新版简历。
- 默认简历输入位于项目根目录 input/；多份文件必须由用户选择。JD 截图目录通过 scripts/select-jd-folder.sh 选择，或使用用户明确提供的路径。
- 输出全部位于项目根目录 tmp/ 内本次任务的独立目录。这里的 tmp/ 不是系统 /tmp/。保留原始输入和既有任务结果。
- 每个任务目录用 manifest.json 记录阶段与产物，tmp/index.md 汇总所有任务；两者只通过 scripts/update-manifest.py 修改。中断后通过 `/resume-workflow` 继续。
- input/facts.md 是跨任务的候选人事实库，只记录用户明确确认的事实，只追加不改写；由主代理维护，子代理只读。
- 简历原文转录须以 scripts/extract-resume-text.sh 的确定性提取文本为基线，经 scripts/check-transcription.py 校验后才能作为匹配和差异依据。
- 不编造或夸大 JD 要求、候选人的经历、能力及量化数据；区分原文证据、合理推断与用户补充事实。
- 简历修改提案须经用户确认后再生成新版。新版在任务目录内生成 LaTeX、PDF 与 Markdown，并展示与原简历的内容差异和源码差异。
- 简历的默认 LaTeX 源文件为 src/LLM-Resume-Template/resume-zh.tex（模板目录是一个独立的 git 仓库）。流程不直接修改 src/；写回需用户明确选择，覆盖前先检查 git 状态。编译统一使用 scripts/build-resume-pdf.sh。
- 调用子代理时显式传递输入与输出的绝对路径，不依赖其自动继承主会话信息。
