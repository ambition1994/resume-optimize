#!/bin/bash
# 用确定性工具提取简历文本，作为 LLM 转录的校验基线。
# 用法：extract-resume-text.sh <简历路径> <输出 .txt 路径>
set -euo pipefail

if [ "$#" -ne 2 ]; then
  printf '%s\n' '用法：extract-resume-text.sh <简历路径> <输出 .txt 路径>' >&2
  exit 2
fi

src="$1"
out="$2"

if [ ! -r "$src" ]; then
  printf '无法读取简历：%s\n' "$src" >&2
  exit 1
fi
if [ -e "$out" ]; then
  printf '输出文件已存在，拒绝覆盖：%s\n' "$out" >&2
  exit 1
fi

ext="$(printf '%s' "${src##*.}" | tr '[:upper:]' '[:lower:]')"
case "$ext" in
  pdf)
    if ! command -v pdftotext >/dev/null 2>&1; then
      printf '%s\n' '未找到 pdftotext，请先安装 poppler（brew install poppler）。' >&2
      exit 1
    fi
    pdftotext -layout -enc UTF-8 "$src" "$out"
    ;;
  md|txt)
    cp "$src" "$out"
    ;;
  *)
    printf '不支持的简历格式：.%s（仅支持 PDF、Markdown、TXT）\n' "$ext" >&2
    exit 1
    ;;
esac

# 有效字符过少通常意味着扫描件或图片型 PDF，无法作为基线
chars="$(tr -d '[:space:]' < "$out" | wc -m | tr -d ' ')"
if [ "$chars" -lt 50 ]; then
  printf '提取到的有效字符仅 %s 个，可能是扫描件，无法作为确定性基线：%s\n' "$chars" "$out" >&2
  exit 3
fi

printf '%s\n' "$out"
