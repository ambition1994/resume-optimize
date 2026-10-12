#!/usr/bin/env python3
"""维护任务目录的 manifest.json，并同步 tmp/index.md 中该任务所在行。

用法：
  update-manifest.py init <任务目录> --jd-dir <截图目录> --resume <简历> [--facts <事实库>] [--template <tex>]
  update-manifest.py update <任务目录> [--stage <阶段>] [--set 键路径=值]... [--append 键路径=值]...
                            [--note 文本]... [--issue 文本]...
  update-manifest.py show <任务目录>

键路径用点分隔，例如 target.company、artifacts.jd_text。值为 null 时写入空值。
--append 追加到列表字段（例如 artifacts.resume_match、proposals.accepted、facts_added）。
index.md 位于任务目录的上级目录（项目根目录 tmp/）。
"""
import argparse
import datetime
import json
import os
import sys
from zoneinfo import ZoneInfo

STAGES = [
    "created", "jd_analyzed", "jd_confirmed", "proposal_ready",
    "proposal_confirmed", "built", "completed", "failed", "cancelled",
]
INDEX_HEADER = "| 创建时间 | 公司 | 岗位 | 阶段 | 任务目录 |\n|---|---|---|---|---|\n"


def now():
    return datetime.datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%d_%H_%M_%S")


def new_manifest(task_dir, args):
    ts = now()
    return {
        "task_dir": task_dir,
        "created_at": ts,
        "updated_at": ts,
        "stage": "created",
        "inputs": {
            "jd_dir": args.jd_dir,
            "resume": args.resume,
            "facts": args.facts,
            "template": args.template,
        },
        "target": {"company": None, "position": None},
        "artifacts": {
            "jd_text": None,
            "jd_analysis": None,
            "resume_extracted": None,
            "resume_original": [],
            "resume_match": [],
            "optimization_proposals": [],
            "resume_optimized_md": [],
            "resume_optimized_tex": [],
            "resume_optimized_pdf": [],
            "build_report": [],
            "diff": [],
        },
        "proposals": {"accepted": [], "rejected": []},
        "facts_added": [],
        "open_issues": [],
        "notes": [],
    }


def parse_assignment(text):
    if "=" not in text:
        sys.exit(f"参数格式应为 键路径=值：{text}")
    key, value = text.split("=", 1)
    return key.split("."), None if value == "null" else value


def walk(manifest, path):
    node = manifest
    for part in path[:-1]:
        if not isinstance(node.get(part), dict):
            sys.exit(f"键路径不存在：{'.'.join(path)}")
        node = node[part]
    last = path[-1]
    if last not in node:
        sys.exit(f"键路径不存在：{'.'.join(path)}")
    return node, last


def sync_index(manifest):
    index = os.path.join(os.path.dirname(manifest["task_dir"]), "index.md")
    row = "| {} | {} | {} | {} | {} |".format(
        manifest["created_at"],
        manifest["target"]["company"] or "",
        manifest["target"]["position"] or "",
        manifest["stage"],
        manifest["task_dir"],
    )
    lines = []
    if os.path.exists(index):
        with open(index, encoding="utf-8") as f:
            lines = f.read().splitlines()
    if not lines:
        lines = INDEX_HEADER.rstrip("\n").splitlines()
    suffix = f"| {manifest['task_dir']} |"
    for i, line in enumerate(lines):
        if line.rstrip().endswith(suffix):
            lines[i] = row
            break
    else:
        lines.append(row)
    with open(index, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return index


def fill_missing(manifest, template):
    """按当前结构补全旧版 manifest 缺少的字段；旧版中为 null 的列表字段改为空列表。"""
    for key, default in template.items():
        if key not in manifest:
            manifest[key] = default
        elif isinstance(default, dict) and isinstance(manifest[key], dict):
            fill_missing(manifest[key], default)
        elif isinstance(default, list) and manifest[key] is None:
            manifest[key] = []


def load(path):
    with open(path, encoding="utf-8") as f:
        manifest = json.load(f)
    blank = argparse.Namespace(jd_dir=None, resume=None, facts=None, template=None)
    fill_missing(manifest, new_manifest(manifest.get("task_dir"), blank))
    return manifest


def save(path, manifest):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("task_dir")
    p_init.add_argument("--jd-dir", required=True)
    p_init.add_argument("--resume", required=True)
    p_init.add_argument("--facts")
    p_init.add_argument("--template")

    p_update = sub.add_parser("update")
    p_update.add_argument("task_dir")
    p_update.add_argument("--stage", choices=STAGES)
    p_update.add_argument("--set", action="append", default=[])
    p_update.add_argument("--append", action="append", default=[])
    p_update.add_argument("--note", action="append", default=[])
    p_update.add_argument("--issue", action="append", default=[])

    p_show = sub.add_parser("show")
    p_show.add_argument("task_dir")

    args = parser.parse_args()
    task_dir = os.path.realpath(args.task_dir)
    path = os.path.join(task_dir, "manifest.json")

    if args.cmd == "init":
        if os.path.exists(path):
            sys.exit(f"manifest.json 已存在，拒绝覆盖：{path}")
        manifest = new_manifest(task_dir, args)
    else:
        if not os.path.exists(path):
            sys.exit(f"manifest.json 不存在：{path}")
        manifest = load(path)
        if args.cmd == "show":
            print(json.dumps(manifest, ensure_ascii=False, indent=2))
            return 0
        for item in args.set:
            keys, value = parse_assignment(item)
            node, last = walk(manifest, keys)
            if isinstance(node[last], list):
                sys.exit(f"{item.split('=')[0]} 是列表字段，请使用 --append")
            node[last] = value
        for item in args.append:
            keys, value = parse_assignment(item)
            node, last = walk(manifest, keys)
            if not isinstance(node[last], list):
                sys.exit(f"{item.split('=')[0]} 不是列表字段，请使用 --set")
            if value not in node[last]:
                node[last].append(value)
        manifest["notes"].extend(args.note)
        manifest["open_issues"].extend(args.issue)
        if args.stage:
            manifest["stage"] = args.stage
        manifest["updated_at"] = now()

    save(path, manifest)
    index = sync_index(manifest)
    print(f"manifest={path}\nstage={manifest['stage']}\nindex={index}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
