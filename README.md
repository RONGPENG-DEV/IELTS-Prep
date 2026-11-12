# IELTS-Prep

本仓库集成五个英语学习技能，检出后无需重新下载技能源码。Codex 可通过 `.agents/skills/` 发现它们；若客户端未自动发现，可让助手先读取根目录 `AGENTS.md` 和对应技能的 `SKILL.md`。

| 技能 | 用途 | 示例请求 |
|---|---|---|
| language-learning | 学习规划 | 用 language-learning 制定 B1 英语学习计划 |
| english-coach | 对话纠错 | 用 english-coach 陪我聊英语并纠错 |
| english-practice | 中文采访、生成口语稿 | 用 english-practice 采访我，生成英语口语稿 |
| shadowing-practice | 影子跟读 | 用 shadowing-practice 安排 10 分钟跟读 |
| immersion-reader | 生成沉浸阅读网页 | 用 immersion-reader 把这篇文章做成阅读课 |

首次使用需要 Python 3.10+：

```bash
bash scripts/setup-skills.sh
```

这会建立项目 `.venv`、安装阅读工具依赖，并在用户目录补齐口语模板；不会覆盖已有模板或学习记录。纯对话技能不需要 Python 依赖。

验证与示例：

```bash
python3 vendor/english-skill/shadowing-practice/scripts/validate_skill.py --format json
python3 vendor/english-skill/shadowing-practice/scripts/run_skill.py --request 'B1 影子跟读' --level B1 --minutes 10 --format json
cd vendor/english-immersion-reader
../../.venv/bin/python -m pytest -q
../../.venv/bin/python src/build_page.py examples/demo/segments.json --out lessons/demo
```

在线语音合成尚未验证，且上游脚本会清除代理变量，需适配云环境代理后使用。浏览器 UI 测试未纳入安装验证。技能安装不代表可以直接听取或评价你的发音。

源码保留于 `vendor/`，`.agents/skills/` 使用仓库内部的相对链接，不依赖之前的 `/workspace/skill-sources`。上游版本见 `vendor/sources.json`，许可见各来源的 LICENSE（如有）；来源如下：

- https://github.com/SkillMedev/skills/tree/main/skills/language-learning
- https://github.com/tianmind-studio/english-coach
- https://github.com/zhuya624-cell/english-practice-skill
- https://github.com/nexaforgelab/english-skill/tree/main/shadowing-practice
- https://github.com/rayw-lab/english-immersion-reader

学习记录、生成课件、虚拟环境不会提交。新机器需要重新运行安装脚本；当前实例的安装不等于环境已发布。
