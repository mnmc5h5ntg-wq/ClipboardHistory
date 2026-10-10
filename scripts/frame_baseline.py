#!/usr/bin/env python3
"""帧基线对比（第三轮审计 §3 C-2）。

CI 已经会把 78 张离屏帧拍出来（D-7 那一轮补的），但它只回答"今天拍得出来吗"，
不回答"和上一版比，哪几帧变了"。视觉回归最难复查的正是后者：
改动者看不见基线， reviewer 只能凭印象比。

这里存的**不是图片**，而是每张帧的 sha256 —— 一份 JSON，随仓库走。

    比对：  python3 scripts/frame_baseline.py compare <frames目录>
    更新：  python3 scripts/frame_baseline.py update  <frames目录>

两条规矩是这套办法有意义的前提：

1. **改了界面就在同一个 commit 里 update 基线**。否则基线永远过期，
   比对结果永远一片红，很快就没人看（这是 D-7 关于"红色要看不得"的同一条教训）。
2. **"消失的一帧"和"多出来的一帧"都算回归**。帧数掉了意味着某个夹具不再被执行 ——
   那正是执行数守卫防的那类事，只是换到了视觉这一侧。

退出码：0 = 完全一致；1 = 有差异（列出帧名）；2 = 用法/环境错误（基线文件不存在等）。
"""
import argparse
import hashlib
import json
import os
import sys
from typing import Dict, List, Tuple

BASELINE_RELATIVE = os.path.join("docs", "frame_baseline.json")
SCHEMA_VERSION = 1


def manifest_path(repo_root: str) -> str:
    return os.path.join(repo_root, BASELINE_RELATIVE)


def sha256_of(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect(frames_dir: str) -> Dict[str, str]:
    """目录里每张 PNG 的 sha256，键是文件名。"""
    result = {}  # type: Dict[str, str]
    for name in sorted(os.listdir(frames_dir)):
        if not name.endswith(".png"):
            continue
        full = os.path.join(frames_dir, name)
        if os.path.isfile(full):
            result[name] = sha256_of(full)
    return result


def compare(baseline: Dict[str, str], current: Dict[str, str]) -> Tuple[List[str], List[str], List[str]]:
    """(变了, 少了, 多了)。分开报是因为三者的处置完全不同：
    变了要人看图，少了要查为什么夹具不跑了，多了要确认是新功能还是重名。"""
    changed = [name for name in sorted(baseline) if name in current and baseline[name] != current[name]]
    missing = [name for name in sorted(baseline) if name not in current]
    added = [name for name in sorted(current) if name not in baseline]
    return changed, missing, added


def load_baseline(path: str) -> Dict[str, str]:
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    frames = document.get("frames")
    if not isinstance(frames, dict):
        raise ValueError("基线文件里没有 frames 字典：%s" % path)
    return {str(k): str(v) for k, v in frames.items()}


def write_baseline(path: str, frames: Dict[str, str]) -> None:
    document = {
        "schema": SCHEMA_VERSION,
        "count": len(frames),
        "note": "离屏帧的 sha256 基线。改了界面就在同一个 commit 里跑 update；"
                "CI 的 compare 步骤靠它回答“上一版比这一版哪些帧变了”。",
        "frames": frames,
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="离屏帧基线的比对与更新")
    parser.add_argument("action", choices=["compare", "update", "check"])
    parser.add_argument("frames_dir")
    parser.add_argument("--allow-missing", action="append", default=[],
                        help="允许缺席的帧名（可重复）。无头 runner 上有几帧注定拍不出来 —— "
                             "「捕获失效闸门」拒绝把 95% 空白的帧当证据写盘，那是诚实的行为。"
                             "把它们列在这里，剩下的缺席才是真回归。")
    parser.add_argument("--repo-root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    args = parser.parse_args(argv)

    path = manifest_path(args.repo_root)
    if not os.path.isdir(args.frames_dir):
        print("FRAME_BASELINE_ERROR=frames 目录不存在：%s" % args.frames_dir)
        return 2

    if args.action == "update":
        frames = collect(args.frames_dir)
        write_baseline(path, frames)
        print("FRAME_BASELINE_UPDATED=%d" % len(frames))
        return 0

    if not os.path.exists(path):
        print("FRAME_BASELINE_ERROR=基线不存在：%s（先跑 update）" % path)
        return 2

    try:
        baseline = load_baseline(path)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print("FRAME_BASELINE_ERROR=基线读不出来：%s" % error)
        return 2

    current = collect(args.frames_dir)
    changed, missing, added = compare(baseline, current)
    # 先扣掉许可名单，再谈"少帧"：否则这条硬门只是把 runner 的物理限制每天复述一遍。
    allowed = [name for name in missing if name in set(args.allow_missing)]
    missing = [name for name in missing if name not in set(args.allow_missing)]
    print("FRAME_BASELINE_COMPARED=%d" % len(current))
    if allowed:
        print("FRAME_BASELINE_ALLOW_MISSING=%d  %s" % (len(allowed), ", ".join(allowed)))
    print("FRAME_BASELINE_CHANGED=%d" % len(changed))
    print("FRAME_BASELINE_MISSING=%d" % len(missing))
    print("FRAME_BASELINE_ADDED=%d" % len(added))
    for name in changed:
        print("  changed  %s" % name)
    for name in missing:
        print("  missing  %s  <- 夹具不再产出这一帧，必须查" % name)
    for name in added:
        print("  added    %s" % name)
    if args.action == "check":
        # check = 只要求"一帧不许少"（多帧与变帧交给人判断，因为新功能本来就会加帧）。
        return 1 if missing else 0
    return 1 if (changed or missing or added) else 0


if __name__ == "__main__":
    sys.exit(main())
