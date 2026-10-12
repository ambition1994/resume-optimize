#!/usr/bin/env python3
"""对比确定性提取文本与 LLM 转录的 resume_original_*.md，找出漏转与疑似新增内容。

用法：python check-transcription.py <提取文本.txt> <resume_original.md>

比对前做归一化：NFKC 统一全半角后，只保留汉字、ASCII 字母数字和 + % . 等少量符号，
因此空白、换行、Markdown 标记和图标字体乱码不会影响结果。
提取文本中每列开头单独成词的单个字符（如图标字体提取出的 a、×、Ɵ）视为图标，不参与比对。
resume_original 的 YAML frontmatter 与 HTML 注释（页码标记等）视为元数据，不参与比对。

退出码：0 一致；1 发现差异；2 用法或读取错误。
"""
import re
import sys
import unicodedata

KEEP = re.compile(r"[\u4e00-\u9fffA-Za-z0-9+%.]")
MIN_LEN = 2


def normalize(text):
    text = unicodedata.normalize("NFKC", text)
    return "".join(KEEP.findall(text)).lower()


# 图标字体常被提取成列首的单个字符加空格，例如“a github.com/...”
ICON = re.compile(r"^[^\s\u4e00-\u9fff]\s+")


def strip_icons(line):
    """去掉 -layout 输出中每列开头的图标字符。"""
    return "  ".join(ICON.sub("", chunk) for chunk in re.split(r"\s{2,}", line.strip()))


def strip_metadata(md):
    md = re.sub(r"\A---\n.*?\n---\n", "", md, flags=re.S)
    return re.sub(r"<!--.*?-->", "", md, flags=re.S)


def check(extracted, original):
    # 图标去除可能误删正文中以单个符号开头的续行（如“+ Kubernetes”），
    # 因此原始文本与去除图标后的文本任一能匹配即视为一致。
    raw_lines = extracted.splitlines()
    clean_lines = [strip_icons(line) for line in raw_lines]
    ext_alls = (normalize(extracted), normalize("\n".join(clean_lines)))
    orig_all = normalize(original)

    def in_orig(text):
        return normalize(text) in orig_all

    missing, reordered = [], []
    for raw, clean in zip(raw_lines, clean_lines):
        if len(normalize(clean)) < MIN_LEN or in_orig(raw) or in_orig(clean):
            continue
        # -layout 输出用多个空格分隔列，逐列检查以区分“漏转”与“仅顺序不同”
        chunks = [c for c in re.split(r"\s{2,}", clean) if len(normalize(c)) >= MIN_LEN]
        if chunks and all(in_orig(c) for c in chunks):
            reordered.append(clean)
        else:
            missing.append(raw.strip())

    added = [
        line.strip()
        for line in original.splitlines()
        if len(normalize(line)) >= MIN_LEN and all(normalize(line) not in e for e in ext_alls)
    ]
    return missing, reordered, added


def main():
    if len(sys.argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        with open(sys.argv[1], encoding="utf-8") as f:
            extracted = f.read()
        with open(sys.argv[2], encoding="utf-8") as f:
            original = strip_metadata(f.read())
    except OSError as e:
        print(f"读取失败：{e}", file=sys.stderr)
        return 2

    missing, reordered, added = check(extracted, original)
    sections = [
        ("提取文本中存在、转录中缺失（疑似漏转或改字）", missing),
        ("转录中存在、提取文本中没有（疑似新增或改字）", added),
        ("各列内容都在，但同一行的顺序不同（通常可忽略）", reordered),
    ]
    for title, items in sections:
        print(f"## {title}：{len(items)} 处")
        for item in items:
            print(f"- {item}")
        print()

    if missing or added:
        print("结论：存在差异，需要逐条核对后再继续。")
        return 1
    print("结论：转录与提取文本一致。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
