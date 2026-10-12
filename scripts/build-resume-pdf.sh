#!/bin/bash
# 在任务目录内编译 LaTeX 简历，不改动 src/ 下的模板仓库。
# 用法：build-resume-pdf.sh <tex 文件> <模板目录>
# 编译产物写入 tex 所在目录的 build/ 子目录；成功时输出 PDF 路径与页数。
set -euo pipefail

if [ "$#" -ne 2 ]; then
  printf '%s\n' '用法：build-resume-pdf.sh <tex 文件> <模板目录>' >&2
  exit 2
fi

tex="$(cd "$(dirname "$1")" && pwd -P)/$(basename "$1")"
template_dir="$(cd "$2" && pwd -P)"

if [ ! -r "$tex" ]; then
  printf '无法读取 tex 文件：%s\n' "$tex" >&2
  exit 1
fi
case "$(dirname "$tex")" in
  "$template_dir"|"$template_dir"/*)
    printf '%s\n' 'tex 文件不能位于模板目录内，请先复制到任务目录。' >&2
    exit 1
    ;;
esac
for cmd in latexmk xelatex pdfinfo; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    printf '未找到 %s，请确认已安装 TeX Live 与 poppler。\n' "$cmd" >&2
    exit 1
  fi
done

out_dir="$(dirname "$tex")/build"
log="$out_dir/latexmk.out"
mkdir -p "$out_dir"

# 只加入模板顶层目录：.cls 和头像图片在顶层；模板自带的 fontawesome5/ 子目录与系统字体不兼容，
# 递归搜索会覆盖 TeX Live 的 fontawesome5 宏包而导致找不到字体。
if ! (cd "$(dirname "$tex")" && TEXINPUTS="$template_dir:" latexmk -xelatex \
    -interaction=nonstopmode -halt-on-error -outdir="$out_dir" "$tex") >"$log" 2>&1; then
  printf '编译失败，日志：%s\n' "$log" >&2
  grep -h -A4 '^!' "$out_dir"/*.log 2>/dev/null | head -20 >&2 || true
  exit 1
fi

pdf="$out_dir/$(basename "${tex%.tex}").pdf"
pages="$(pdfinfo "$pdf" | awk '/^Pages:/ {print $2}')"
printf 'pdf=%s\npages=%s\n' "$pdf" "$pages"
