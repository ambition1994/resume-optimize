# Resume Optimize

基于 [Claude Code](https://claude.com/claude-code) 子代理的 JD 定向简历优化工作流：读取招聘需求（JD）截图，对照你的真实简历逐项匹配，生成可核验的修改提案，经你确认后输出新版 LaTeX / PDF / Markdown 简历及差异对比。

核心原则：**不编造、不夸大**。每条建议都标注依据来自简历原文、合理推断还是你亲自补充的事实；未经确认的经历和数据不会进入新版简历。

## 工作流程

```
JD 截图 ──► jd-analyst ──► JD 转录 + 结构化分析 ──► 用户确认
                                                      │
简历 PDF ──► 确定性文本提取 ──► jd-optimize ──► 匹配报告 + 修改提案 ──► 用户逐条确认
                     │                                                    │
                     └── check-transcription 校验转录 ──┘                 ▼
                                                     resume-builder ──► 新版 tex / PDF / md + diff
```

| 角色 | 职责 |
|---|---|
| 主代理（`/resume-workflow`） | 选择输入、创建任务目录、征求确认、复核结果、记录任务状态 |
| `jd-analyst` | 转录 JD 截图，提取岗位要求与硬性门槛 |
| `jd-optimize` | 将 JD 要求映射到简历证据，给出匹配结论与修改提案 |
| `resume-builder` | 只落实已接受的建议，生成新版简历并报告落实情况 |

## 特性

- **可追溯**：JD 原文转录与分析分开保存，简历转录以 `pdftotext` 的确定性提取结果为基线做自动校验，避免 LLM 漏转或改字。
- **人工把关**：JD 分析、修改提案、新版简历三个节点都需要用户确认，建议按编号逐条接受或拒绝。
- **事实库**：`input/facts.md` 跨任务记录你确认过的补充事实（只追加不改写），下次匹配同类岗位时自动复用。
- **可续跑**：每个任务目录有 `manifest.json` 记录阶段与产物，`tmp/index.md` 汇总所有任务；中断后再次运行 `/resume-workflow` 即可继续。
- **不破坏原件**：所有产物写入 `tmp/` 下的独立任务目录，不直接修改 `src/` 中的简历源文件；写回需显式选择。

## 目录结构

```
.
├── .claude/
│   ├── agents/              # jd-analyst / jd-optimize / resume-builder 子代理定义
│   └── skills/resume-workflow/SKILL.md   # 主流程编排
├── scripts/
│   ├── select-jd-folder.sh      # macOS 文件夹选择框，选取 JD 截图目录
│   ├── extract-resume-text.sh   # 确定性提取简历文本
│   ├── check-transcription.py   # 校验 LLM 转录与提取文本的一致性
│   ├── update-manifest.py       # 维护 manifest.json 与 tmp/index.md
│   └── build-resume-pdf.sh      # 在任务目录内编译 LaTeX 简历
├── src/LLM-Resume-Template/  # LaTeX 简历模板（resume-zh.tex 为虚构示例）
├── input/                    # 放置你的简历 PDF 与事实库（已 gitignore）
├── tmp/                      # 任务输出目录（已 gitignore）
└── CLAUDE.md                 # 项目约定
```

## 环境要求

- [Claude Code](https://claude.com/claude-code)
- macOS（`select-jd-folder.sh` 使用 AppleScript；其他系统可直接向主代理提供截图目录路径）
- TeX Live（需要 `latexmk`、`xelatex`）
- poppler（需要 `pdftotext`、`pdfinfo`），例如 `brew install poppler`
- Python 3

## 快速开始

1. 克隆仓库并进入目录。
2. 将你的简历写入 `src/LLM-Resume-Template/resume-zh.tex`（替换其中的虚构示例），编译出 PDF 后放入 `input/`。
3. 将目标岗位的 JD 截图放进任意一个文件夹。
4. 在项目根目录启动 Claude Code，运行：

   ```
   /resume-workflow
   ```

   按提示选择截图目录和简历，依次确认 JD 分析、修改提案和新版简历。产物位于 `tmp/jd-XXXXXX/`。

如需使用特定的 Python 虚拟环境，修改 `.claude/skills/resume-workflow/SKILL.md` 中 `<PY>` 的定义即可。

## 隐私

`input/`、`tmp/`、`output/` 中的简历、截图、事实库和所有任务产物均已加入 `.gitignore`，不会被提交。提交前仍建议用 `git status` 检查一遍。

## 致谢

LaTeX 简历模板来自 [adongwanai/LLM-Resume-Template](https://github.com/adongwanai/LLM-Resume-Template)，其样式基于 Weitian LI 的 resume 模板（CC BY 4.0），版权归原作者所有。

## License

本项目自有代码（`.claude/`、`scripts/` 等）采用 [MIT License](LICENSE)。`src/LLM-Resume-Template/` 下的模板文件不在此列，遵循其原作者的 CC BY 4.0 协议。
