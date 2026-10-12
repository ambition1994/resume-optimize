#!/bin/bash
set -euo pipefail

project_root="$(cd "$(dirname "$0")/.." && pwd -P)"

if [ "$(uname -s)" != "Darwin" ]; then
  printf '%s\n' '文件夹选择框仅支持 macOS。' >&2
  exit 1
fi

osascript - "$project_root" <<'APPLESCRIPT'
on run arguments
    set projectRoot to item 1 of arguments
    try
        set selectedFolder to choose folder with prompt "请选择存放 JD 截图的文件夹" default location (POSIX file projectRoot)
        return POSIX path of selectedFolder
    on error errorMessage number errorNumber
        if errorNumber is -128 then
            error "已取消选择 JD 截图文件夹。" number -128
        end if
        error errorMessage number errorNumber
    end try
end run
APPLESCRIPT
