#!/usr/bin/env python3
"""Shared runtime helpers for the English learning skill collection.

The individual skills are prompt-first resources. This module gives every skill
the same deterministic scaffold for session planning, validation, profile
loading, and optional persistence through english_agent_core.py.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ENHANCEMENT_START = "<!-- ENGLISH_SKILL_ENHANCEMENT_START -->"
ENHANCEMENT_END = "<!-- ENGLISH_SKILL_ENHANCEMENT_END -->"


CATEGORY_LIBRARY: Dict[str, Dict[str, Any]] = {
    "词汇/语法": {
        "keywords": [
            "vocabulary", "word", "phrasal-verb", "grammar", "synonym",
            "complex-sentence", "root", "affix",
        ],
        "capabilities": [
            "诊断词汇或语法目标",
            "输出规则讲解、例句和迁移练习",
            "把错词、错句和薄弱规则加入复习队列",
        ],
        "workflow_phases": ["画像校准", "规则拆解", "语境输入", "控制练习", "自由输出", "即时反馈", "复习安排"],
        "assessment_dimensions": ["准确性", "搭配自然度", "主动调用能力", "迁移能力"],
        "review_item_types": ["word", "phrase", "grammar_pattern"],
        "sample_requests": ["帮我学习和科技发展有关的词汇，并设计复习。"],
        "output_labels": ["学习目标", "核心讲解", "例句演练", "输出任务", "复习计划"],
    },
    "发音/语音": {
        "keywords": [
            "pronunciation", "phonetic", "stress-rhythm", "linking",
            "shadowing", "speech-imitation",
        ],
        "capabilities": [
            "拆解目标音、音节、重音和连读",
            "生成跟读、影子练习和录音反馈清单",
            "记录发音问题并安排高频复习",
        ],
        "workflow_phases": ["目标音定位", "口腔动作说明", "最小对立练习", "句子跟读", "录音自检", "纠错建议", "复习安排"],
        "assessment_dimensions": ["音素准确度", "重音节奏", "连读弱读", "可懂度"],
        "review_item_types": ["pronunciation", "sentence", "minimal_pair"],
        "sample_requests": ["我想练习 th 音和句子重音。"],
        "output_labels": ["发音目标", "动作要点", "跟读材料", "自检标准", "复习计划"],
    },
    "听力": {
        "keywords": ["listening", "blind-listening", "podcast", "number-practice"],
        "capabilities": [
            "按水平选择听力任务和听前预测",
            "拆解听力障碍：词汇、连读、语速、口音、背景知识",
            "把听错内容加入复听和复习队列",
        ],
        "workflow_phases": ["材料分级", "听前预测", "第一遍抓主旨", "第二遍抓细节", "错点诊断", "精听复盘", "复听安排"],
        "assessment_dimensions": ["主旨理解", "细节捕捉", "语音辨识", "推断能力"],
        "review_item_types": ["listening_clip", "heard_phrase", "number_expression"],
        "sample_requests": ["给我做一次 B1 难度的盲听训练。"],
        "output_labels": ["材料信息", "听前任务", "听后问题", "错点分析", "复听计划"],
    },
    "口语/对话": {
        "keywords": [
            "speaking", "dialogue", "small-talk", "role-play", "quick-qa",
            "expression", "debate", "storytelling", "meeting", "workplace",
            "oral", "situation", "confidence", "topic-practice", "presentation",
            "paraphrase-practice",
        ],
        "capabilities": [
            "搭建真实场景并持续扮演对话角色",
            "提供地道表达、追问和即时纠错",
            "追踪卡顿、错句和高价值表达",
        ],
        "workflow_phases": ["场景设定", "表达输入", "角色对话", "追问扩展", "表达升级", "反馈纠错", "复练安排"],
        "assessment_dimensions": ["流利度", "语法准确性", "表达自然度", "互动能力"],
        "review_item_types": ["spoken_sentence", "useful_expression", "error_pattern"],
        "sample_requests": ["请和我练习一次面试英语对话。"],
        "output_labels": ["场景", "关键表达", "对话任务", "反馈标准", "复练计划"],
    },
    "阅读": {
        "keywords": ["reading", "level-reading", "daily-reading", "reading-accelerator"],
        "capabilities": [
            "按水平选择阅读材料和阅读任务",
            "拆解长难句、结构和核心词汇",
            "把新词和理解误区转化为复习任务",
        ],
        "workflow_phases": ["材料分级", "阅读目标", "快速浏览", "细读拆解", "理解检测", "复述输出", "词汇复习"],
        "assessment_dimensions": ["阅读速度", "主旨理解", "细节定位", "复述质量"],
        "review_item_types": ["reading_word", "sentence_pattern", "summary"],
        "sample_requests": ["给我一篇 B1 阅读材料并做理解训练。"],
        "output_labels": ["阅读材料", "理解任务", "长难句", "词汇回顾", "输出练习"],
    },
    "写作/改写": {
        "keywords": [
            "writing", "diary", "email", "proofreading", "rewrite",
            "resume-polish", "sentence-rewrite",
        ],
        "capabilities": [
            "分析写作目标、读者和语气",
            "提供结构、措辞、语法和逻辑层面的改进",
            "把高频错误和优秀表达沉淀为复习项",
        ],
        "workflow_phases": ["写作目标", "结构规划", "表达输入", "初稿生成", "逐项修改", "质量评分", "复写安排"],
        "assessment_dimensions": ["结构清晰度", "语法准确性", "词汇质量", "逻辑连贯"],
        "review_item_types": ["writing_error", "better_expression", "sentence_template"],
        "sample_requests": ["帮我润色一段关于远程工作的英文段落。"],
        "output_labels": ["写作目标", "结构建议", "修改建议", "优化版本", "复写任务"],
    },
    "考试备考": {
        "keywords": [
            "ielts", "toefl", "cet4", "college", "high-school", "postgraduate",
            "exam",
        ],
        "capabilities": [
            "对齐考试题型和评分标准",
            "生成专项训练、限时任务和评分反馈",
            "追踪薄弱题型并安排阶段复习",
        ],
        "workflow_phases": ["考试目标", "题型定位", "方法讲解", "限时练习", "评分反馈", "错因归类", "冲刺计划"],
        "assessment_dimensions": ["题型匹配", "完成度", "评分项表现", "时间控制"],
        "review_item_types": ["exam_error", "template", "topic_idea"],
        "sample_requests": ["给我一套雅思口语 Part 2 练习并评分。"],
        "output_labels": ["考试目标", "题目", "答题框架", "评分反馈", "下次重点"],
    },
    "商务/生活/文化": {
        "keywords": [
            "business", "study-abroad", "job-hunting", "cultural", "movie",
            "song", "news", "hot-topic", "growth-management", "parent-child",
        ],
        "capabilities": [
            "还原真实应用场景和语气边界",
            "给出地道表达、文化说明和任务演练",
            "记录可迁移表达并安排复用练习",
        ],
        "workflow_phases": ["场景确认", "语气选择", "表达输入", "示范对话", "文化提示", "迁移任务", "复用安排"],
        "assessment_dimensions": ["场景适配", "语气准确", "表达地道", "任务完成"],
        "review_item_types": ["scenario_expression", "culture_note", "dialogue_line"],
        "sample_requests": ["教我写一封商务会议跟进邮件。"],
        "output_labels": ["应用场景", "核心表达", "文化/语气", "实战任务", "复用计划"],
    },
}


CATEGORY_ORDER = [
    "考试备考",
    "听力",
    "写作/改写",
    "阅读",
    "词汇/语法",
    "发音/语音",
    "商务/生活/文化",
    "口语/对话",
]


@dataclass
class SkillSpec:
    skill_dir: Path
    name: str
    description: str
    body: str
    category: str
    output_labels: List[str]
    step_count: int
    profile: Dict[str, Any]


def parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    match = re.match(r"^---\n(.*?)\n---\n?", text, re.DOTALL)
    if not match:
        return {}, text

    metadata: Dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        metadata[key.strip()] = value
    return metadata, text[match.end():]


def infer_category(name: str, description: str = "") -> str:
    needle = f"{name} {description}".lower()
    for category in CATEGORY_ORDER:
        keywords = CATEGORY_LIBRARY[category]["keywords"]
        if any(keyword in needle for keyword in keywords):
            return category
    return "口语/对话"


def extract_output_labels(body: str) -> List[str]:
    labels: List[str] = []
    seen = set()
    for label in re.findall(r"【([^】]{1,30})】", body):
        clean = label.strip()
        if clean and clean not in seen:
            labels.append(clean)
            seen.add(clean)
    return labels[:10]


def count_steps(body: str) -> int:
    patterns = [
        r"(?:^|\n)\s*\d+[.、]\s+",
        r"第\s*[一二三四五六七八九十0-9]+\s*步",
    ]
    return sum(len(re.findall(pattern, body)) for pattern in patterns)


def default_profile(name: str, description: str, category: str) -> Dict[str, Any]:
    library = CATEGORY_LIBRARY[category]
    display = name.replace("-", " ").title()
    return {
        "schema_version": "1.0",
        "skill_name": name,
        "display_name": display,
        "category": category,
        "description": description,
        "capabilities": list(library["capabilities"]),
        "workflow_phases": list(library["workflow_phases"]),
        "assessment_dimensions": list(library["assessment_dimensions"]),
        "review_item_types": list(library["review_item_types"]),
        "sample_requests": list(library["sample_requests"]),
        "output_labels": list(library["output_labels"]),
    }


def load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def load_skill(skill_dir: Path) -> SkillSpec:
    skill_dir = skill_dir.resolve()
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(text)
    name = metadata.get("name") or skill_dir.name
    description = metadata.get("description", "")
    category = infer_category(name, description)
    profile_path = skill_dir / "references" / "skill_profile.json"
    profile = load_json(profile_path) or default_profile(name, description, category)
    profile.setdefault("skill_name", name)
    profile.setdefault("category", category)
    profile.setdefault("description", description)

    labels = extract_output_labels(body)
    if not labels:
        labels = list(CATEGORY_LIBRARY[category]["output_labels"])

    return SkillSpec(
        skill_dir=skill_dir,
        name=name,
        description=description,
        body=body,
        category=profile.get("category", category),
        output_labels=labels,
        step_count=count_steps(body),
        profile=profile,
    )


def _request_terms(request: str, spec: SkillSpec) -> List[str]:
    terms: List[str] = []

    phrase_patterns = [
        r"[\"“']([^\"”']{2,40})[\"”']",
        r"重点是([^，。,.!?；;]{2,30})",
        r"关于([^，。,.!?；;]{2,30})",
        r"练习一次([^，。,.!?；;]{2,30})",
        r"练习([^，。,.!?；;]{2,30})",
    ]
    for pattern in phrase_patterns:
        for item in re.findall(pattern, request):
            clean = item.strip(" 的。.,!?;:，。！？；：")
            if clean and clean not in terms:
                terms.append(clean)

    for item in re.findall(r"[A-Za-z][A-Za-z'-]{2,}", request):
        clean = item.strip(".,!?;:，。！？；：")
        if clean and clean.lower() not in {"please", "help", "english"} and clean not in terms:
            terms.append(clean)

    if len(terms) < 3:
        for item in spec.name.split("-"):
            if item and item not in terms:
                terms.append(item)
    if len(terms) < 3:
        for item in spec.profile.get("review_item_types", []):
            if item not in terms:
                terms.append(item)
    return terms[:5]


def build_session(
    skill_dir: Path,
    request: str = "",
    user_id: str = "local-user",
    level: str = "A2",
    minutes: int = 10,
    mode: str = "guided",
) -> Dict[str, Any]:
    spec = load_skill(skill_dir)
    request = request or spec.profile.get("sample_requests", ["开始一次学习任务。"])[0]
    phases = spec.profile.get("workflow_phases") or CATEGORY_LIBRARY[spec.category]["workflow_phases"]
    dimensions = spec.profile.get("assessment_dimensions") or CATEGORY_LIBRARY[spec.category]["assessment_dimensions"]
    terms = _request_terms(request, spec)

    plan = []
    for index, phase in enumerate(phases, 1):
        plan.append(
            {
                "step": index,
                "phase": phase,
                "agent_action": f"围绕用户请求“{request}”执行{phase}，难度对齐 {level}，控制在 {minutes} 分钟内。",
                "learner_output": "一句话回答、选择题、朗读/复述、短段输出或自评分。",
            }
        )

    review_types = spec.profile.get("review_item_types") or CATEGORY_LIBRARY[spec.category]["review_item_types"]
    review_items = []
    for index, term in enumerate(terms[:3]):
        review_items.append(
            {
                "item": term,
                "item_type": review_types[index % len(review_types)],
                "explanation": f"来自 {spec.name} 的本次学习重点，需要在后续任务中主动复用。",
                "difficulty": 2,
            }
        )

    return {
        "metadata": {
            "skill_name": spec.name,
            "category": spec.category,
            "description": spec.description,
            "generated_at": datetime.utcnow().isoformat(),
            "skill_dir": str(spec.skill_dir),
        },
        "learner": {
            "user_id": user_id,
            "level": level,
            "minutes": minutes,
            "mode": mode,
        },
        "request": request,
        "capabilities": spec.profile.get("capabilities", []),
        "session_plan": plan,
        "practice_pack": {
            "warmup": f"用一个低压力问题确认学习者对“{request}”的熟悉度。",
            "core_task": f"生成一个 {spec.category} 任务，要求学习者必须产出可评价的结果。",
            "feedback_rule": "先指出最影响理解/得分的 1-2 个问题，再给可立即复用的替代表达。",
            "transfer_task": "让学习者用相同技能迁移到自己的真实生活、考试或工作场景。",
        },
        "output_contract": {
            "required_labels": spec.output_labels[:6],
            "style": "中文解释 + 英文示例；任务指令短、可执行、可评分。",
        },
        "assessment": {
            "scale": "0-5",
            "dimensions": dimensions,
            "pass_rule": "总评达到 3 分以上进入下一难度，否则保留当前难度并缩短任务。",
        },
        "review": {
            "items": review_items,
            "schedule": ["今天", "1 天后", "3 天后", "7 天后"],
            "sm2_quality_hint": "0-2 表示遗忘或误用；3 表示勉强正确；4-5 表示能主动复用。",
        },
        "integration": {
            "log_event": "记录本次会话请求、任务输出和评分。",
            "add_review_item": "把错词、错句、表达模板或听力片段加入复习队列。",
            "sm2_update": "用户完成复习后根据表现更新间隔。",
        },
    }


def render_markdown(session: Dict[str, Any]) -> str:
    meta = session["metadata"]
    learner = session["learner"]
    lines = [
        f"# {meta['skill_name']} 增强学习会话",
        "",
        f"- 分类：{meta['category']}",
        f"- 学习者：{learner['user_id']} / {learner['level']} / {learner['minutes']} 分钟",
        f"- 请求：{session['request']}",
        "",
        "## 能力范围",
    ]
    for capability in session.get("capabilities", []):
        lines.append(f"- {capability}")

    lines.extend(["", "## 端到端流程"])
    for step in session["session_plan"]:
        lines.append(f"{step['step']}. {step['phase']}：{step['agent_action']}")

    lines.extend(["", "## 输出契约"])
    for label in session["output_contract"]["required_labels"]:
        lines.append(f"- 【{label}】")

    lines.extend(["", "## 评分维度"])
    for dimension in session["assessment"]["dimensions"]:
        lines.append(f"- {dimension}")

    lines.extend(["", "## 复习项"])
    for item in session["review"]["items"]:
        lines.append(f"- {item['item_type']}: {item['item']} - {item['explanation']}")

    return "\n".join(lines) + "\n"


def record_session(session: Dict[str, Any]) -> Dict[str, Any]:
    try:
        import english_agent_core as core
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"recorded": False, "error": f"Cannot import english_agent_core: {exc}"}

    user_id = session["learner"]["user_id"]
    skill_name = session["metadata"]["skill_name"]
    core.log_event(
        user_id=user_id,
        agent_name=skill_name,
        event_type="enhanced_session",
        content=json.dumps(
            {
                "request": session["request"],
                "level": session["learner"]["level"],
                "minutes": session["learner"]["minutes"],
            },
            ensure_ascii=False,
        ),
        result="session_plan_generated",
    )
    for item in session["review"]["items"]:
        core.add_review_item(
            user_id=user_id,
            agent_name=skill_name,
            item_type=item["item_type"],
            item=item["item"],
            explanation=item["explanation"],
            difficulty=item.get("difficulty", 2),
        )
    return {"recorded": True, "review_items": len(session["review"]["items"])}


def validate_skill(skill_dir: Path) -> Dict[str, Any]:
    skill_dir = skill_dir.resolve()
    skill_md = skill_dir / "SKILL.md"
    checks: Dict[str, bool] = {
        "skill_md_exists": skill_md.exists(),
        "run_script_exists": (skill_dir / "scripts" / "run_skill.py").exists(),
        "validate_script_exists": (skill_dir / "scripts" / "validate_skill.py").exists(),
        "profile_exists": (skill_dir / "references" / "skill_profile.json").exists(),
        "agent_metadata_exists": (skill_dir / "agents" / "openai.yaml").exists(),
    }
    details: Dict[str, Any] = {}
    if skill_md.exists():
        text = skill_md.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(text)
        checks.update(
            {
                "frontmatter_name": bool(metadata.get("name")),
                "frontmatter_description": bool(metadata.get("description")),
                "role_section": "角色定义" in body or "你是" in body,
                "core_flow": "核心流程" in body and count_steps(body) >= 5,
                "output_format": "输出格式" in body,
                "integration_hooks": all(
                    hook in body for hook in ["log_event", "add_review_item", "sm2_update"]
                ),
                "enhancement_section": ENHANCEMENT_START in body and ENHANCEMENT_END in body,
            }
        )
        details["name"] = metadata.get("name", skill_dir.name)
        details["category"] = infer_category(metadata.get("name", skill_dir.name), metadata.get("description", ""))
        details["step_count"] = count_steps(body)
        details["output_labels"] = extract_output_labels(body)

    profile_path = skill_dir / "references" / "skill_profile.json"
    if profile_path.exists():
        try:
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            checks["profile_json_valid"] = True
            checks["profile_has_capabilities"] = bool(profile.get("capabilities"))
            checks["profile_has_workflow"] = bool(profile.get("workflow_phases"))
        except json.JSONDecodeError as exc:
            checks["profile_json_valid"] = False
            details["profile_error"] = str(exc)

    missing = [name for name, ok in checks.items() if not ok]
    return {
        "skill_dir": str(skill_dir),
        "passed": not missing,
        "checks": checks,
        "missing_or_failed": missing,
        "details": details,
    }


def _write_output(text: str, output: Optional[str]) -> None:
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def main(default_skill_dir: Optional[Path] = None, argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run an enhanced English skill session.")
    parser.add_argument("--skill", default=str(default_skill_dir or Path.cwd()))
    parser.add_argument("--request", default="")
    parser.add_argument("--user-id", default="local-user")
    parser.add_argument("--level", default="A2")
    parser.add_argument("--minutes", type=int, default=10)
    parser.add_argument("--mode", default="guided")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--record", action="store_true", help="Persist event and review items with english_agent_core.")
    parser.add_argument("--doctor", action="store_true", help="Validate the skill resource package.")
    parser.add_argument("--output")
    args = parser.parse_args(list(argv) if argv is not None else None)

    skill_dir = Path(args.skill)
    if args.doctor:
        result = validate_skill(skill_dir)
        payload = json.dumps(result, ensure_ascii=False, indent=2)
        _write_output(payload + "\n", args.output)
        return 0 if result["passed"] else 1

    session = build_session(
        skill_dir=skill_dir,
        request=args.request,
        user_id=args.user_id,
        level=args.level,
        minutes=args.minutes,
        mode=args.mode,
    )
    if args.record:
        session["record_result"] = record_session(session)

    if args.format == "json":
        _write_output(json.dumps(session, ensure_ascii=False, indent=2) + "\n", args.output)
    else:
        _write_output(render_markdown(session), args.output)
    return 0


def validate_main(default_skill_dir: Optional[Path] = None, argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an enhanced English skill package.")
    parser.add_argument("--skill", default=str(default_skill_dir or Path.cwd()))
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(list(argv) if argv is not None else None)

    result = validate_skill(Path(args.skill))
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = "PASS" if result["passed"] else "FAIL"
        print(f"{status} {Path(args.skill).resolve()}")
        if result["missing_or_failed"]:
            print("Missing/failed: " + ", ".join(result["missing_or_failed"]))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
