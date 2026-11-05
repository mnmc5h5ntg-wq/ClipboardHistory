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
import io
import json
import os
import platform
import re as _re
import struct
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

# 档位词表只有一份真值（R587 / 靶 B）：倍率解析里的 `(?:light|dark)` 由它现推，
# 这样加一档/改名时这一侧不会**静默**退化成「帧名里推不出倍率」（那条出口不红）。
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)
from tier_vocabulary import TIERS, tier_suffix_pattern  # noqa: E402

BASELINE_RELATIVE = os.path.join("docs", "frame_baseline.json")
# 发布时冻结的**逐版本**基线放这里（§3 C-2 要的是"和上一版比"，
# 只有一份可随时 update 的工作基线的话，"上一版"其实是"上一次有人记得 update 的时候"）。
RELEASE_DIR_RELATIVE = os.path.join("docs", "frame_baselines")
# R584：基线是**某一台机器的产物**，不是无主的地面真值 —— runner 自己印的 `倍率=1.0x`
# 与本机的 1440×1040（名义 720×520 的 2 倍）两个通道对拍后量到的事实是：拿本机烤的那份
# 工作基线去比 runner 的帧，`changed` = **356/356**，每一帧都不同。那一格红得没法逐张处置，
# 所以逐机器基线放这个目录：哪台机器有自己那份，哪台的变帧才归它判。
MACHINE_BASELINE_DIR_RELATIVE = os.path.join("docs", "frame_baselines", "by_machine")
SCHEMA_VERSION = 1

_VERSION_IN_NAME = _re.compile(r"v(\d+)\.(\d+)(?:\.(\d+))?")
_MACHINE_UNSAFE = _re.compile(r"[^0-9A-Za-z]+")


def version_key(name: str):
    """`v1.4.10` 必须排在 `v1.4.9` 之后 —— 按字符串排会得到相反的答案，
    而这条错误会让"上一版"选错对象，整条 diff 的语义就没了。"""
    match = _VERSION_IN_NAME.search(name)
    if not match:
        return (0, 0, 0, name)
    parts = [int(x) if x else 0 for x in match.groups()]
    return (parts[0], parts[1], parts[2], name)


def manifest_path(repo_root: str) -> str:
    return os.path.join(repo_root, BASELINE_RELATIVE)


def machine_key(env: Optional[Dict[str, str]] = None) -> str:
    """这台机器的键 —— 照 `motion_floor_gate.machine_key()` 那套既有约定，不另发明第四种。

    三份 python 侧实现（这一份、`motion_floor_gate`、`test_surface_left_axes`）由
    `scripts/tests/test_frame_baseline.py` 的同一张真值表钉住"取值必须相同"；
    Swift 侧那份只差大小写（BACKLOG **657**），所以**本文件的键只与本文件写的登记行 join**，
    不与 Swift 那份互认。
    """
    source = dict(os.environ) if env is None else env
    explicit = source.get("MOTION_FLOOR_MACHINE_KEY")
    if explicit:
        return explicit
    if source.get("GITHUB_ACTIONS", "").lower() in ("1", "true"):
        return "github-runner"
    return "local:" + platform.node()


def sanitize_machine(key: str) -> str:
    """键要进文件名，非字母数字换成 `_`，但**大小写一个字都不抹**。

    这条不是洁癖：657 量到的正是 `MacBook-Air.local` 与 `macbook-air.local` 只差大小写。
    在这里 `lower()` 一次，那两台（其实是一台，也可能真是两台）就合成同一个文件 —— 门会拿
    其中一份基线去判另一份的像素。所以只有"不同键 ⇒ 不同文件名"是安全的。
    """
    return _MACHINE_UNSAFE.sub("_", key).strip("_")


def machine_baseline_dir(repo_root: str) -> str:
    return os.path.join(repo_root, MACHINE_BASELINE_DIR_RELATIVE)


def machine_baseline_path(repo_root: str, key: str) -> str:
    return os.path.join(machine_baseline_dir(repo_root), "%s.json" % sanitize_machine(key))


# R583 / BACKLOG 655：`check` 以前**只判 missing**，于是 `changed>0` 与 `added>0` 两态谁都不判 ——
# 那 8 张变帧不是被豁免，而是没人看。豁免名单是账，"没人判"不是。
# 现在三态都可数：变帧/新帧必须逐条登记在名册里（帧名 + 理由 + 归哪张单），否则门红。
DRIFT_REGISTRY_RELATIVE = os.path.join("docs", "frame_drift_registry.json")
DRIFT_KINDS = ("changed", "added")


def drift_registry_path(repo_root: str) -> str:
    return os.path.join(repo_root, DRIFT_REGISTRY_RELATIVE)


def load_drift_registry(path: str) -> List[Dict[str, str]]:
    """读登记名册。形状坏了要抛出去，不许在调用方手里变成"0 条 ⇒ 全绿"（R99 那一族）。"""
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    rows = document.get("rows")
    if not isinstance(rows, list):
        raise ValueError("登记名册里没有 rows 列表：%s" % path)
    out = []  # type: List[Dict[str, str]]
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("登记名册里有一行不是对象：%r" % (row,))
        kind = str(row.get("kind", ""))
        if kind not in DRIFT_KINDS:
            raise ValueError("登记名册里有一行的 kind 不认识（只允许 %s）：%r" % ("/".join(DRIFT_KINDS), kind))
        out.append({"frame": str(row.get("frame", "")), "kind": kind,
                    "machine": str(row.get("machine", "")),
                    "reason": str(row.get("reason", "")), "ticket": str(row.get("ticket", "")),
                    "observed": row.get("observed") if isinstance(row.get("observed"), dict) else None,
                    "registered_by_round": str(row.get("registered_by_round", ""))})
    return out


def baseline_digest(frames: Dict[str, str]) -> str:
    """把一份基线的**内容**压成一个串 —— 出处的对照物。

    为什么不用文件本身的 sha256：`update` 每次都会重写文件（`count`/`note` 顺序无关，但键序会变），
    而出处要认的是"这一行当时是对着哪一份**帧集**登记的"。
    """
    blob = json.dumps(frames, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def verify_provenance(rows: List[Dict[str, object]], machine: str,
                      current: Dict[str, str], digest: str,
                      drifting: Optional[List[str]] = None) -> Dict[str, List[str]]:
    """纯函数：本机名册行必须带**它自己观测到的那对哈希**。

    没有这一层，任何一轮手抄一行 `machine=github-runner` 就能把 runner 的 `未登记=348` 洗成 0，
    而**一朵红都不会有** —— 那正是 R583 那个洞换了个方向（登记从"没人判"变成"谁都能替别人登记"）。

    只问**此刻正在豁免漂移的那几行**：一行陈旧行（这台机器今天不漂）没在替任何人放行，
    拿"没出处"去红它就是把判定从"这条豁免可不可信"扩成"每一行都得重写过"（那是逼人删账）。
    他机行不由本机证伪（本机没有那一台的帧，硬判就是拿自己的观测替别人下结论）；
    那一台的基线进了仓库之后才谈得上跨机证伪 ⇒ 658。
    """
    no_proof, mismatch = [], []
    pool = None if drifting is None else set(drifting)
    for row in rows:
        if row.get("machine", "") != machine:
            continue
        name = str(row.get("frame", ""))
        if pool is not None and name not in pool:
            continue
        proof = row.get("observed")
        if not isinstance(proof, dict) or not str(proof.get("frame_sha") or "") \
                or not str(proof.get("baseline_sha") or ""):
            no_proof.append(name)
            continue
        if str(proof.get("baseline_sha")) != digest or \
           str(proof.get("frame_sha")) != str(current.get(name, "")):
            mismatch.append(name)
    return {"no_proof": no_proof, "mismatch": mismatch}


def register_drift(args) -> int:
    """`register-drift`：给当前**这台机器**观测到的漂移补登记行。

    三条硬规矩：① `machine` 一律取运行时 `machine_key()`，命令行里没有 `--machine` 这种口子；
    ② 理由与单号缺一就不写（退 2）—— 登记是账，不是措辞；
    ③ 每一行带 `observed`（这一张帧当时的 sha256 + 当时那份基线的 digest）⇒ `check` 之后能证伪手抄行。
    """
    machine = machine_key()
    if not args.restamp and not ((args.reason or "").strip() and (args.ticket or "").strip()):
        print(u"FRAME_BASELINE_ERROR=register-drift 必须同时给 --reason 与 --ticket（空理由/空单号不算登记）")
        return 2
    path, _label = resolve_baseline_path(args.repo_root, "working")
    if not os.path.exists(path):
        print("FRAME_BASELINE_ERROR=基线不存在：%s（先跑 update）" % path)
        return 2
    try:
        document = load_baseline_document(path)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print("FRAME_BASELINE_ERROR=基线读不出来：%s" % error)
        return 2
    baseline = {str(k): str(v) for k, v in document["frames"].items()}
    digest = baseline_digest(baseline)
    current = collect(args.frames_dir)
    changed, _missing, added = compare(baseline, current)
    registry = args.drift_registry or drift_registry_path(args.repo_root)
    rows = load_drift_registry(registry) if os.path.exists(registry) else []
    mine = [r for r in rows if r.get("machine", "") == machine]
    done = set(str(r["frame"]) for r in mine if r["kind"] == "changed") | \
           set(str(r["frame"]) for r in mine if r["kind"] == "added")
    if args.restamp:
        # 只补出处，不新增行；也只碰本机的行。理由/单号必须已经在账上（空着就不许盖戳）。
        stamped, refused = [], []
        for row in rows:
            if row.get("machine", "") != machine:
                continue
            name = str(row.get("frame", ""))
            drifting = name in changed or name in added
            if not (str(row.get("reason", "")).strip() and str(row.get("ticket", "")).strip()):
                refused.append(name)
                continue
            if not drifting:
                refused.append(name)
                continue
            row["observed"] = {"frame_sha": current.get(name, ""), "baseline_sha": digest}
            stamped.append(name)
        if not stamped:
            print(u"FRAME_BASELINE_RESTAMP=0 本机没有「正在漂且理由/单号齐全」的行可盖出处（拒绝 %d 行）"
                  % len(refused))
            return 0 if not refused else 1
        write_drift_registry(registry, rows, machine)
        print("FRAME_BASELINE_RESTAMP=%d 机器=%s 基线出处=%s 拒绝=%d"
              % (len(stamped), machine, digest[:12], len(refused)))
        for name in refused:
            print(u"  拒绝盖戳  %s  <- 这一行此刻不在漂移里，或理由/单号是空的 ⇒ 出处只能盖本机真的看见的东西" % name)
        return 0
    wanted = [str(f) for f in args.frame] if args.frame else \
             [n for n in changed + added if n not in done]
    if not wanted:
        print(u"FRAME_BASELINE_REGISTER=没东西要登记（本机名下这些漂移都已登记，或点名的帧不在漂移里）")
        return 0
    added_rows, skipped = [], []
    for name in wanted:
        kind = "changed" if name in changed else ("added" if name in added else "")
        if not kind:
            skipped.append(name)
            continue
        added_rows.append({"frame": name, "kind": kind, "machine": machine,
                           "reason": args.reason.strip(), "ticket": args.ticket.strip(),
                           "registered_by_round": (args.round or "").strip(),
                           "observed": {"frame_sha": current.get(name, ""), "baseline_sha": digest}})
    if not added_rows:
        print(u"FRAME_BASELINE_REGISTER=点名的帧都不在当前漂移里（%s）⇒ 不写" % u",".join(skipped))
        return 2
    merged = rows + added_rows
    write_drift_registry(registry, merged, machine)
    print("FRAME_BASELINE_REGISTER=%d 机器=%s 基线出处=%s" % (len(added_rows), machine, digest[:12]))
    for row in added_rows:
        print("  登记  %s kind=%s 单号=%s" % (row["frame"], row["kind"], row["ticket"]))
    if skipped:
        print("  跳过（不在漂移里）  %s" % u",".join(skipped))
    return 0


def write_drift_registry(path: str, rows: List[Dict[str, object]], machine: str) -> None:
    """名册的**写路径**（上一版只有读路径 ⇒ 那 8 行的 `machine` 值是被抄进去的字面）。

    只允许写运行时的本机键；已有行的内容一字不动（登记是账，重排/改写要人来做，且必须走同一条命令）。
    ⚠ note 是**人写的句子**，不许被生成器覆盖：本轮第一次跑 `--restamp` 就把 R583 那句
    "本名册不是重烤基线的替代品" 冲掉了 ⇒ 改成"原文在就留着，只在末尾补一次新句"（改账不删原文）。
    """
    extra = (u"R585 起每行带 `observed`（这一行当轮观测到的帧 sha256 + 基线 digest）⇒ 手抄一行 "
             u"`machine=github-runner:*` 洗不掉那一台的未登记；补登记请走 "
             u"`python3 scripts/frame_baseline.py register-drift <帧目录> --reason … --ticket …`。")
    note = (u"帧基线里「变帧 / 新帧」的逐张登记名册（R583 / BACKLOG 655）。"
            u"登记的键是 (机器, 帧)：本机的行只豁免本机的漂移。")
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as handle:
                existing = json.load(handle)
            kept = str(existing.get("note") or "").strip()
            if kept:
                note = kept
        except (ValueError, OSError, json.JSONDecodeError):
            pass          # 读不出原文就不猜；下面的写会把坏形状照原样交给 load_drift_registry 去红
    if extra not in note:
        note = note + extra
    document = {"schema": 1,
                "note": note,
                "written_by_machine": machine,
                "rows": sorted(rows, key=lambda r: (str(r.get("machine", "")), str(r.get("frame", ""))))}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def judge_drift(changed: List[str], added: List[str], baseline: Dict[str, str],
                current: Dict[str, str],
                rows: Optional[List[Dict[str, str]]],
                machine: str = "",
                provenance: Optional[Dict[str, List[str]]] = None) -> Dict[str, object]:
    """纯函数：三态 + 名册（按 (机器, 帧) 取键）⇒ 该红的与只报数的。

    ⚠ **陈旧行与「他机行」都只报数、不判**，这不是漏：漂移是**按机器**的（本机那 8 张在 runner
       上一张都不漂，而 runner 相对本机基线是 356/356 全漂），另一台此刻不漂不代表这条登记写错了 ——
       把它判红等于逼人在两台机器之间来回删名册。
       真正该红的两件事与机器无关：**对不上任何帧名的行**（拼错的、改名后留下的），
       以及**这台机器自己漂了却没登记**。
    ⚠ **本机的行只豁免本机的漂移**（R584：上一版没有 `machine` 字段，于是本机那 8 行
       事实上在给任何机器的漂移背书放行）。
    """
    rows = rows or []
    mine = [r for r in rows if r.get("machine", "") == machine]
    foreign = [r for r in rows if r.get("machine", "") != machine]
    rows_without_machine = [r["frame"] for r in rows if not r.get("machine", "").strip()]
    registered_changed = set(r["frame"] for r in mine if r["kind"] == "changed")
    registered_added = set(r["frame"] for r in mine if r["kind"] == "added")
    unregistered = [n for n in changed if n not in registered_changed] + \
                   [n for n in added if n not in registered_added]
    unknown = [r["frame"] for r in rows
               if (r["kind"] == "changed" and r["frame"] not in baseline)
               or (r["kind"] == "added" and r["frame"] not in current)]
    bad_fields = [r["frame"] for r in rows if not r["reason"].strip() or not r["ticket"].strip()]
    stale = [r["frame"] for r in mine
             if r["kind"] == "changed" and r["frame"] in baseline and r["frame"] not in changed]
    return {
        "machine": machine, "changed": len(changed), "added": len(added),
        "registered": len([n for n in changed if n in registered_changed])
                      + len([n for n in added if n in registered_added]),
        "unregistered": unregistered,
        "rows": len(rows), "unknown": unknown, "bad_fields": bad_fields, "stale": stale,
        "mine": len(mine), "foreign": len(foreign), "rows_without_machine": rows_without_machine,
        "no_proof": list((provenance or {}).get("no_proof") or []),
        "mismatch": list((provenance or {}).get("mismatch") or []),
    }


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


def load_baseline_document(path: str) -> Dict[str, object]:
    """整份文档（`load_baseline` 只给 frames 字典，会把署名丢掉）。"""
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    if not isinstance(document.get("frames"), dict):
        raise ValueError("基线文件里没有 frames 字典：%s" % path)
    return document


def baseline_owner(document: Dict[str, object]) -> str:
    """这份基线是**哪台机器的产物**；没署名就返回空串 —— 空串不等于"哪台都算"。"""
    return str(document.get("machine") or "").strip()


def git_head_commit(repo_root: str) -> str:
    """此刻这一棵树是哪一笔。取不到就返回空串 —— 空串意思是**不知道**，不是"哪笔都算"。

    为什么由工具自己取而不给命令行口子：出处一旦被手填，它就退化成另一句措辞（R585 那条
    「登记是账，不是措辞」的同一族）。所以这里没有 `--baked-by`／`--commit`：参数是**观测**，不是**声明**。
    """
    try:
        proc = subprocess.Popen(["git", "-C", repo_root, "rev-parse", "HEAD"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, _err = proc.communicate(timeout=20)
        if proc.returncode != 0:
            return ""
        return out.decode("utf-8", "replace").strip()
    except (OSError, ValueError):
        return ""


def ledger_round(repo_root: str) -> str:
    """这一份基线是**哪一轮**烤的：读台账自己的轮次标题，不读环境变量、不接受手填。

    口径是「最新已落地那一节的 R 号 + 1」= 正在烤它的那一轮（仓库里 `Rnnn = 第 nnn-1 轮` 那条映射
    由 `commit_round_identity.py` 钉着，这里只复用它已经写在标题里的那个数，不再新造一套）。
    两个来源各算各的，谁先有数用谁；都没有 ⇒ 空串 = **不知道**，不许猜一个。
    """
    for name in ("AGENT_STATE.md", "AGENT_UI_AUDIT.md"):
        path = os.path.join(repo_root, name)
        if not os.path.exists(path):
            continue
        text = io.open(path, encoding="utf-8", errors="replace").read()
        nums = [int(x) for x in _re.findall(r"(?m)^## R(\d+)", text)]
        if nums:
            return "R%d" % (max(nums) + 1)
        rounds = [int(x) for x in _re.findall(r"(?m)^## 第 (\d+) 轮", text)]
        if rounds:
            return "R%d" % (max(rounds) + 2)
    return ""


def png_size(path: str) -> Tuple[int, int]:
    """PNG 的像素尺寸，只读 IHDR 那 8 个字节。

    为什么不用 PIL：这一支门在 CI 里跑在 Pillow 那一步之前也算（R218 之后步骤顺序动过两次），
    而"这份基线是按什么倍率烤的"不能因为某个解释器缺库就答不出来。
    """
    try:
        with open(path, "rb") as handle:
            head = handle.read(24)
        if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n":
            return (0, 0)
        width, height = struct.unpack(">II", head[16:24])
        return (int(width), int(height))
    except (OSError, struct.error):
        return (0, 0)


def capture_scale(frames_dir: str) -> Dict[str, object]:
    """这批帧的捕获倍率 —— 报成**分布**，不报成单一读数（R587 / 靶 A）。

    帧名里写的是逻辑点尺寸（`…-720x520-dark.png`），PNG 头里是像素尺寸 ⇒ 倍率 = 像素宽 ÷ 逻辑宽。
    上一版这里 `max(set(ratios), key=ratios.count)` 没有任何并列检测，于是：
      · 355 张 2x + 1 张 1x 这种**混批**照样印 `2.00x`，读者看不出这批是混的；
      · 两档各半时印的是 `set` 遍历顺序决定的那一个 —— 那是抛硬币，不是读数。
    所以现在交出去的是 `(倍率或空串, 分布, 不一致帧数, 原因)`：并列 ⇒ 倍率一律当**不知道**（空串），
    原因里点名 `tie`，由调用方走**已有的那一条** `SCALE_NOT_RUN` 出口（不新造第二个不判出口）。
    `bad`（x 与 y 推不出同一倍率的帧）以前算完就被 `_bad` 丢掉 ⇒ 现在照报，进文档也进行。
    """
    ratios = []
    bad = 0
    unreadable = 0
    sizeless = 0
    try:
        names = sorted(os.listdir(frames_dir))
    except OSError:
        return {"scale": "", "frames": 0, "bad": 0, "sizeless": 0, "dist": [], "reason": "no-dir"}
    for name in names:
        if not name.endswith(".png"):
            continue
        m = _re.search(r"-(\d+)x(\d+)-(?:%s)\.png$" % "|".join(TIERS), name)
        if not m:
            # 帧名里没有逻辑尺寸段 ⇒ 这一张**进不了倍率**，但不能当它不存在：计数照报，
            # 否则"分布只覆盖了一半这批"没人知道。现读语料（本机这一批 + 三份基线名单）里这一支是 **0**
            # ⇒ 它是**分母完整性**的证人，不是今天的读数（证人用合成帧名，见 ScaleDistributionTests）。
            sizeless += 1
            continue
        px, py = png_size(os.path.join(frames_dir, name))
        lx, ly = int(m.group(1)), int(m.group(2))
        if px <= 0 or lx <= 0 or ly <= 0:
            unreadable += 1
            bad += 1
            continue
        if px % lx != 0 or py != ly * (px // lx):
            bad += 1          # 两轴推不出同一个倍率：这一张既进分布也进 bad，两边都要看得见
        ratios.append(float(px) / float(lx))
    if not ratios:
        return {"scale": "", "frames": 0, "bad": bad, "sizeless": sizeless, "dist": [],
                "reason": "unreadable" if unreadable else "no-frames"}
    counts = {}
    for r in ratios:
        counts["%0.2fx" % r] = counts.get("%0.2fx" % r, 0) + 1
    dist = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    top = dist[0][1]
    tied = [name for name, cnt in dist if cnt == top]
    if len(tied) > 1:
        return {"scale": "", "frames": len(ratios), "bad": bad, "sizeless": sizeless,
                "dist": dist, "reason": "tie"}
    return {"scale": dist[0][0], "frames": len(ratios), "bad": bad, "sizeless": sizeless,
            "dist": dist, "reason": "ok"}


def scale_dist_text(info: Dict[str, object]) -> str:
    """分布的逐字形状 `2.00x:355,1.00x:1`（值槽里不许有裸 ASCII 空格 —— R565 那条）。"""
    dist = list((info or {}).get("dist") or [])
    return u",".join(u"%s:%d" % (name, cnt) for name, cnt in dist) or u"（无）"


def bake_provenance(repo_root: Optional[str], frames_dir: Optional[str],
                    inherit: Optional[Dict[str, object]] = None) -> Dict[str, str]:
    """这份基线是**谁在哪一笔、按什么倍率**烤的。全部运行时观测，没有手填口子。"""
    if inherit is not None:
        commit = str(inherit.get("baked_from_commit") or "").strip()
        if commit:
            return {"commit": commit,
                    "round": str(inherit.get("baked_by_round") or "").strip(),
                    "scale": str(inherit.get("capture_scale") or "").strip(),
                    "scale_frames": str(inherit.get("capture_scale_frames") or "").strip(),
                    "dist": str(inherit.get("capture_scale_dist") or "").strip(),
                    "bad": str(inherit.get("capture_scale_bad_frames") or "").strip(),
                    "sizeless": str(inherit.get("capture_scale_sizeless") or "").strip(),
                    "reason": str(inherit.get("capture_scale_reason") or "").strip()}
    commit = git_head_commit(repo_root) if repo_root else ""
    rnd = ledger_round(repo_root) if repo_root else ""
    info = capture_scale(frames_dir) if frames_dir else {
        "scale": "", "frames": 0, "bad": 0, "sizeless": 0, "dist": [], "reason": "no-dir"}
    return {"commit": commit, "round": rnd,
            "scale": str(info["scale"]),
            "scale_frames": str(info["frames"]) if info["frames"] else "",
            "dist": scale_dist_text(info), "bad": str(info["bad"]),
            "sizeless": str(info.get("sizeless") or ""),
            "reason": str(info["reason"])}


def baseline_bake(document: Dict[str, object]) -> Dict[str, str]:
    """读回一份基线文档的出处；缺字段一律读成空串 = **不知道**，不默认成"新"或"这一笔"。"""
    return {
        "commit": str(document.get("baked_from_commit") or "").strip(),
        "round": str(document.get("baked_by_round") or "").strip(),
        "scale": str(document.get("capture_scale") or "").strip(),
        "scale_frames": str(document.get("capture_scale_frames") or "").strip(),
        "dist": str(document.get("capture_scale_dist") or "").strip(),
        "bad": str(document.get("capture_scale_bad_frames") or "").strip(),
        "sizeless": str(document.get("capture_scale_sizeless") or "").strip(),
        "reason": str(document.get("capture_scale_reason") or "").strip(),
    }


def bake_line(document: Dict[str, object]) -> str:
    bake = baseline_bake(document)
    return (u"出处=%s commit=%s 轮=%s 倍率=%s 口径帧数=%s 倍率分布=%s 不一致帧数=%s 无尺寸段=%s 原因=%s"
            % (u"有" if bake["commit"] else u"无",
               bake["commit"] or u"（无）",
               bake["round"] or u"（无）",
               bake["scale"] or u"（不知道）",
               bake["scale_frames"] or u"（无）",
               bake["dist"] or u"（无）",
               bake["bad"] or u"0",
               bake["sizeless"] or u"0",
               bake["reason"] or u"（无）"))


def write_baseline(path: str, frames: Dict[str, str], machine: Optional[str] = None,
                   repo_root: Optional[str] = None, frames_dir: Optional[str] = None,
                   inherit: Optional[Dict[str, object]] = None) -> None:
    bake = bake_provenance(repo_root, frames_dir, inherit)
    document = {
        "schema": SCHEMA_VERSION,
        "count": len(frames),
        # 署名是判定的一部分：像素是不是"同一台机器上的同一件事"，只有产出它的那台机器知道。
        "machine": machine_key() if machine is None else machine,
        # R586 / 靶 A：出处也是判定的一部分。只有 machine 那一格答不了"这份基线是不是拿被判的那批帧
        # 自己烤的"—— 那种时候 `变帧=0` 与"没人改过界面"逐字相同，门却会给它签绿。
        "baked_from_commit": bake["commit"],
        "baked_by_round": bake["round"],
        "capture_scale": bake["scale"],
        "capture_scale_frames": bake["scale_frames"],
        # R587 / 靶 A：单一读数会藏住混批与并列 ⇒ 分布、bad、原因一起落盘，
        # 让"这份基线是按什么倍率烤的"这句话在文档里就是完整的。
        "capture_scale_dist": bake["dist"],
        "capture_scale_bad_frames": bake["bad"],
        "capture_scale_sizeless": bake["sizeless"],
        "capture_scale_reason": bake["reason"],
        "note": "离屏帧的 sha256 基线。改了界面就在同一个 commit 里跑 update；"
                "CI 的 compare 步骤靠它回答“上一版比这一版哪些帧变了”。",
        "frames": frames,
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def release_dir(repo_root: str) -> str:
    return os.path.join(repo_root, RELEASE_DIR_RELATIVE)


def released_baselines(repo_root: str) -> List[str]:
    """按版本号排序的逐版本基线文件名（旧 → 新）。"""
    directory = release_dir(repo_root)
    if not os.path.isdir(directory):
        return []
    return sorted((n for n in os.listdir(directory) if n.endswith(".json")), key=version_key)


def latest_released_baseline(repo_root: str) -> Optional[str]:
    names = released_baselines(repo_root)
    return os.path.join(repo_root, RELEASE_DIR_RELATIVE, names[-1]) if names else None


def snapshot(repo_root: str, version: str) -> Optional[str]:
    """把当前工作基线冻结成 `docs/frame_baselines/vX.Y.Z.json`。

    发布脚本调它（不重拍帧）：冻结的是"这次发出去的包对应的界面"，
    而那份帧在发布前就该由 `update` 确认过是最新的。
    """
    source = manifest_path(repo_root)
    if not os.path.exists(source):
        return None
    document = load_baseline_document(source)
    frames = {str(k): str(v) for k, v in document["frames"].items()}
    target = os.path.join(release_dir(repo_root), "%s.json" % ("v%s" % version.lstrip("v")))
    # 继承署名，不重新签：快照冻的是"那份基线对应的界面"，不是"此刻跑 snapshot 的这台机器"。
    # 出处照继承，不重烤：快照冻的是"那份基线对应的那一笔"，不是"此刻跑 snapshot 的这一笔"。
    write_baseline(target, frames, machine=baseline_owner(document), inherit=document)
    return target


def resolve_baseline_path(repo_root: str, against: str = "auto") -> Tuple[str, str]:
    """返回 (路径, 说明)。`auto` = 有逐版本基线就用最新的那一版，否则退回工作基线。"""
    if against == "working":
        return manifest_path(repo_root), "working"
    latest = latest_released_baseline(repo_root)
    if against == "latest-release":
        if not latest:
            raise ValueError("还没有任何逐版本基线（跑一次 snapshot 才有）")
        return latest, os.path.basename(latest)[:-5]
    if latest:
        return latest, os.path.basename(latest)[:-5]
    return manifest_path(repo_root), "working"


def build_parser() -> argparse.ArgumentParser:
    """把参数表单独暴露出来（R587 / 顺账）：

    为什么 —— 上一轮印给读者的出路里那个旗标值写错了（少了 `latest-` 前缀），
    靠一把刀钉住。这一轮要的是**仪器守卫**：印出去的每条命令串能不能被这份 parser 自己吃下，
    由 `scripts/tests/test_printed_commands.py` 现读源码里的 print 串、真解析一遍，
    而不是每犯一次记一笔。措辞里多一个字母就是空头支票（R585/R586 同族，已复发一次）。
    """
    parser = argparse.ArgumentParser(description="离屏帧基线的比对与更新")
    parser.add_argument("action", choices=["compare", "update", "check", "snapshot", "register-drift"])
    parser.add_argument("frames_dir", nargs="?", default=None,
                        help="compare / check / update / register-drift 必需；"
                             "snapshot 只冻结已有的工作基线")
    parser.add_argument("--version", default=None, help="snapshot 用：要冻结成哪个版本（如 1.4.8）")
    parser.add_argument("--for-machine", action="store_true",
                        help="update 用：把这份帧写成**这台机器自己的**基线 "
                             "（docs/frame_baselines/by_machine/<键>.json，键一律运行时取，"
                             "没有 --machine 这种口子）；不加这一句就照旧只写工作基线。")
    parser.add_argument("--reason", default=None,
                        help="register-drift 必需：这一张为什么漂（登记是账，空着就不算登记）")
    parser.add_argument("--ticket", default=None, help="register-drift 必需：归哪张单")
    parser.add_argument("--round", default=None, help="register-drift 可选：哪一轮登记的")
    parser.add_argument("--restamp", action="store_true",
                        help="register-drift 用：不新增行，只给**本机已有**的登记行补上 `observed` 那对哈希"
                             "（R585 之前那 8 行的 machine 值是手抄的字面 ⇒ 没有出处；"
                             "只准盖本机当轮真的观测到的东西，别机器行一律不碰）")
    parser.add_argument("--frame", action="append", default=[],
                        help="register-drift：只登记点名的那几张（可重复）；不给就登记当前所有未登记的漂移")
    parser.add_argument("--allow-missing", action="append", default=[],
                        help="允许缺席的帧名（可重复）。无头 runner 上有几帧注定拍不出来 —— "
                             "「捕获失效闸门」拒绝把 95%% 空白的帧当证据写盘，那是诚实的行为。"
                             "把它们列在这里，剩下的缺席才是真回归。")
    parser.add_argument("--repo-root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parser.add_argument("--against", default="auto", choices=["auto", "working", "latest-release"],
                        help="比对对象：默认 auto，即有逐版本基线就和最新一版比，否则和工作基线比")
    parser.add_argument("--drift-registry", default=None,
                        help="变帧/新帧的逐张登记名册（默认 docs/frame_drift_registry.json）。"
                             "check 用它把 changed 与 added 两态也变成会红的判据 —— 登记是账，不是措辞。")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.action != "snapshot":
        if not args.frames_dir:
            print("FRAME_BASELINE_ERROR=%s 需要 frames 目录参数" % args.action)
            return 2
    if args.frames_dir is not None and not os.path.isdir(args.frames_dir):
        print("FRAME_BASELINE_ERROR=frames 目录不存在：%s" % args.frames_dir)
        return 2

    if args.action == "snapshot":
        if not args.version:
            print("FRAME_BASELINE_ERROR=snapshot 需要版本号")
            return 2
        target = snapshot(args.repo_root, args.version)
        if not target:
            print("FRAME_BASELINE_ERROR=还没有工作基线可冻结（先跑 update）")
            return 2
        print("FRAME_BASELINE_SNAPSHOT=%s" % target)
        return 0

    if args.action == "update":
        frames = collect(args.frames_dir)
        if args.for_machine:
            # R585 / 658 的前置：上一版这里**永远**写工作基线，而它印给读者的出路写着
            # "update 会署名并写 by_machine/<键>.json" —— 那句是假的，任何机器照它跑都停在 `判=不判`。
            # 键一律由运行时取（`machine_key()`），没有 `--machine` 这种"我自己说是哪台"的口子。
            key = machine_key()
            target = machine_baseline_path(args.repo_root, key)
            write_baseline(target, frames, machine=key,
                           repo_root=args.repo_root, frames_dir=args.frames_dir)
            print("FRAME_BASELINE_UPDATED=%d" % len(frames))
            print("FRAME_BASELINE_MACHINE_BASELINE=%s 署名=%s" % (target, key))
            # 印的是**回读**出来的那份文档，不是我以为写进去的那些字段（R580 那一族：
            # "我签的字"要由盘上那份文件说，不能由写手的变量说）。
            print("FRAME_BASELINE_BAKE %s" % bake_line(load_baseline_document(target)))
            return 0
        # 工作基线永远写在 docs/frame_baseline.json：逐版本的那份是它的快照，不是替代品。
        write_baseline(manifest_path(args.repo_root), frames)
        print("FRAME_BASELINE_UPDATED=%d" % len(frames))
        return 0

    if args.action == "register-drift":
        return register_drift(args)

    machine = machine_key()
    path = None       # type: Optional[str]
    against_label = ""
    # check 时先看这台机器自己那份：`by_machine/<键>.json` 在就用它，变帧那一维就归这台机器判。
    # 没有就走工作基线，而工作基线**认不认这台机器**由它的署名说（见下面的 owner/judged）。
    if args.action == "check" and args.against in ("working", "auto"):
        candidate = machine_baseline_path(args.repo_root, machine)
        if os.path.exists(candidate):
            path, against_label = candidate, "by_machine:%s" % machine
    if path is None:
        try:
            path, against_label = resolve_baseline_path(args.repo_root, args.against)
        except ValueError as error:
            print("FRAME_BASELINE_ERROR=%s" % error)
            return 2
    if not os.path.exists(path):
        print("FRAME_BASELINE_ERROR=基线不存在：%s（先跑 update）" % path)
        return 2

    try:
        baseline_document = load_baseline_document(path)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print("FRAME_BASELINE_ERROR=基线读不出来：%s" % error)
        return 2
    baseline = {str(k): str(v) for k, v in baseline_document["frames"].items()}
    owner = baseline_owner(baseline_document)
    if against_label.startswith("by_machine:") and owner != machine:
        # 文件名说的是一台、里面署名是另一台 ⇒ 这份东西不可信，不许拿它判任何人。
        print("FRAME_BASELINE_ERROR=逐机器基线自相矛盾：文件名=%s 署名=%s" % (machine, owner or "（未署名）"))
        return 2
    judged = (owner != "" and owner == machine)
    bake = baseline_bake(baseline_document)
    # 「同批自烤」= 基线文档说它是在**此刻这一笔**上烤的。那种时候 `变帧=0` 不含任何信息：
    # 它既可以是"没人改过界面"，也可以是"刚拿被判的那批帧自己烤了一遍"，两条在输出里逐字相同。
    # 上一轮给名册补了 `observed`（手抄行从此可证伪），基线这一侧是同一个洞却没有同一个药 ⇒ 这一格补上。
    head = git_head_commit(args.repo_root)
    same_bake = bool(bake["commit"]) and bake["commit"] == head
    cur_info = capture_scale(args.frames_dir)
    current_scale = str(cur_info["scale"])
    current_scale_frames = int(cur_info["frames"])

    current = collect(args.frames_dir)
    changed, missing, added = compare(baseline, current)
    # 先扣掉许可名单，再谈"少帧"：否则这条硬门只是把 runner 的物理限制每天复述一遍。
    allowed = [name for name in missing if name in set(args.allow_missing)]
    missing = [name for name in missing if name not in set(args.allow_missing)]
    print("FRAME_BASELINE_AGAINST=%s" % against_label)
    print("FRAME_BASELINE_MACHINE=%s" % machine)
    print("FRAME_BASELINE_OWNER=%s" % (owner or "（未署名）"))
    print("FRAME_BASELINE_COMPARED=%d" % len(current))
    if allowed:
        print("FRAME_BASELINE_ALLOW_MISSING=%d  %s" % (len(allowed), ", ".join(allowed)))
    print("FRAME_BASELINE_CHANGED=%d" % len(changed))
    print("FRAME_BASELINE_MISSING=%d" % len(missing))
    print("FRAME_BASELINE_ADDED=%d" % len(added))
    print(u"FRAME_BASELINE_BAKE %s" % bake_line(baseline_document))
    if not bake["commit"]:
        # 旧文档读得动，判定也照旧 —— 但它说不出自己是哪一笔烤的，所以"变帧=0"在这份文件上
        # 从来没有证人。这一支**具名不拦路**（它不是新造成的红），也不许被读成"这份基线没问题"。
        print(u"FRAME_BASELINE_BAKE_PROVENANCE=absent "
              u"⇒ 这份基线没有 baked_from_commit（R586 之前烤的旧文档，形状照读、判定照旧）；"
              u"它答不了「判的就是烤它的那批帧吗」⇒ 不许把 变帧=0 读成「没人改过界面」（BACKLOG 660）")
    if same_bake:
        print(u"FRAME_BASELINE_SAME_BAKE=%s" % bake["commit"][:7])
        print(u"  同批  基线的 baked_from_commit 与此刻 HEAD 同一笔（%s）⇒ 这一趟的 变帧=%d 不给「没变」签字："
              u"它同样兼容「刚拿被判的这批帧自己烤了一遍」。%s"
              % (bake["commit"][:7], len(changed),
                 u"出路 让基线与被判的帧出自不同一笔（例如发布那一笔烤、下一笔判），"
                 u"或改判逐版本基线 `--against latest-release`；不许为了让这一支绿就把出处字段删掉，也不许调宽任何阈值"))
    # ── 倍率这一维（R587 / 靶 A）：报的是**分布**，不是一个看起来确定的读数。
    #   并列（两档各半）与"帧名/头读不出"都归**同一条**不判出口 `SCALE_NOT_RUN`，原因写在值里；
    #   这样"加一档就静默退化"那一族没有第二条门路可走，也不新造第二个不判出口。
    if cur_info["reason"] == "tie":
        print(u"FRAME_BASELINE_SCALE_TIE 当轮=%s（%d 张里众数并列）⇒ 倍率按「不知道」处理，"
              u"下面那条 SCALE_NOT_RUN 是这一支唯一的出口"
              % (scale_dist_text(cur_info), current_scale_frames))
    if cur_info.get("sizeless"):
        print(u"FRAME_BASELINE_SCALE_SIZELESS 当轮=%d 张帧名里没有 `-宽x高-档` 那一段"
              u"⇒ 它们进不了倍率分布，只报数不拦路（这一支是分布的**分母完整性**证人）" % cur_info["sizeless"])
    if cur_info["bad"]:
        # `bad` 以前算完就被 `_bad` 丢掉 ⇒ 现在照报：混批与"两轴推不出同一倍率"都要看得见。
        print(u"FRAME_BASELINE_SCALE_BAD 当轮=%d/%d 张的两轴推不出同一倍率（只报数不拦路）"
              % (cur_info["bad"], current_scale_frames))
    if bake["reason"] == "tie":
        print(u"FRAME_BASELINE_SCALE_TIE 基线=%s ⇒ 那份基线自己就是说不出倍率的（混批或并列烤的）"
              % (bake["dist"] or u"（无）"))
    if bake["scale"] and current_scale and bake["scale"] != current_scale:
        # 只报数不拦路：R584 已经量到 runner 自印 1.00x 而工作基线是本机 2x 烤的那件事，
        # 这一格把它从"推理"变成基线文档自己说得出来的读数。放宽/收紧都不发生。
        print(u"FRAME_BASELINE_SCALE_MISMATCH 基线=%s 当轮=%s（当轮量到 %d 张 分布=%s）⇒ 只报数不拦路，"
              u"它是「变帧那一维是不是同一件事」的现场证人"
              % (bake["scale"], current_scale, current_scale_frames, scale_dist_text(cur_info)))
    if not current_scale:
        # 这一支是"当轮倍率说不出"的**唯一**出口（R587 / 靶 A ①：并列不许另开第二条不判门路）。
        # 上一版它挂在 `elif bake["scale"] and …` 下面 ⇒ 基线自己也说不出倍率时（混批/并列烤的）
        # 两个 unknown 撞在一起，反而一行读数都不印 —— 那是"谁都不知道"被读成"没什么要报的"。
        print(u"FRAME_BASELINE_SCALE_NOT_RUN=%s（当轮分布=%s 基线倍率=%s）⇒ 这一维今天没读数，"
              u"不许读成倍率相符，也不许读成倍率不合"
              % (cur_info["reason"], scale_dist_text(cur_info) or u"（无）",
                 bake["scale"] or u"（不知道）"))
    for name in changed:
        print("  changed  %s" % name)
    for name in missing:
        print("  missing  %s  <- 夹具不再产出这一帧，必须查" % name)
    for name in added:
        print("  added    %s" % name)
    if args.action != "check":
        return 1 if (changed or missing or added) else 0

    # —— check：三态都要有人判。以前这里只写 `return 1 if missing else 0`，
    #    于是 changed/added 两态"命令成功、输出看着齐、其实谁都没判"（R583 / 655 那个洞）。
    registry = args.drift_registry or drift_registry_path(args.repo_root)
    rows = None      # type: Optional[List[Dict[str, str]]]
    registry_state = "absent"
    if os.path.exists(registry):
        try:
            rows = load_drift_registry(registry)
            registry_state = "loaded"
        except (ValueError, OSError, json.JSONDecodeError) as error:
            print(u'FRAME_BASELINE_DRIFT_REGISTRY=broken %s ⇒ 名册读不出来时不许当成「没有登记」' % error)
            return 2
    digest = baseline_digest(baseline)
    # 出处只在"这一维归本机判"时才可证伪：不判那一支手里那份基线不是本机的观测，
    # 拿它去证伪本机的登记行就是反过来犯错（R584 ⑵ 那一族的镜像）。数目照报。
    provenance = verify_provenance(rows or [], machine, current, digest,
                                   drifting=list(changed) + list(added))
    verdict = judge_drift(changed, added, baseline, current, rows, machine,
                          provenance if judged else {"no_proof": [], "mismatch": []})
    verdict["no_proof_all"] = provenance["no_proof"]
    verdict["mismatch_all"] = provenance["mismatch"]
    print("FRAME_BASELINE_DRIFT_REGISTRY=%s %s 行=%s" % (registry_state, registry, verdict["rows"]))
    print("FRAME_BASELINE_REGISTRY_DIGEST=%s" % digest[:12])
    common = (u"本机=%s 基线署名=%s 判=%s 变帧=%d 新帧=%d 本机行=%d 他机行=%d "
              u"名册对不上帧名=%d 名册空理由或空单号=%d 名册缺机器=%d "
              u"名册无出处=%d 出处对不上=%d"
              % (machine, owner or "（未署名）", "判" if judged else "不判",
                 verdict["changed"], verdict["added"], verdict["mine"], verdict["foreign"],
                 len(verdict["unknown"]), len(verdict["bad_fields"]),
                 len(verdict["rows_without_machine"]),
                 len(verdict["no_proof_all"]) if not judged else len(verdict["no_proof"]),
                 len(verdict["mismatch_all"]) if not judged else len(verdict["mismatch"])))
    for name in verdict["rows_without_machine"]:
        print(u"  名册缺机器  %s  <- 登记行必须写明它豁免**哪台**机器的漂移；"
              u"没有机器字段就等于本机在给所有机器的漂移背书放行" % name)
    for name in (verdict["no_proof"] if judged else provenance["no_proof"]):
        print(u"  名册无出处  %s  <- 这一行没带它当轮观测到的那对哈希 ⇒ 分不清是命令写的还是手抄的；"
              u"补登记请走 register-drift" % name)
    for name in (verdict["mismatch"] if judged else provenance["mismatch"]):
        print(u"  出处对不上  %s  <- 这一行记的帧哈希/基线 digest 与本机当轮观测不同字 ⇒ "
              u"它不是这台机器这一轮看到的，不许拿它豁免本轮的漂移" % name)
    for name in verdict["bad_fields"]:
        print(u"  名册缺字段  %s  <- 登记必须有理由与单号，否则它只是措辞" % name)
    for name in verdict["unknown"]:
        print(u"  名册对不上  %s  <- 名册里这一行既不对应当前基线的变帧、也不对应当前产出的新帧（拼错或夹具改名后留下的）" % name)
    # 两条支路的**字段集不同**，这不是省事：`已登记/未登记/陈旧行` 只有在"这一维归这台机器判"时才是读数，
    # 把它们印成数字再报 `拦路=0` 会让读数自相矛盾（R565：含裸空格的值打死尺；这里是含假数的值打死尺）。
    unreg_word = u"不判"
    if not judged:
        # 基线不是这台机器的产物 ⇒ 变帧这一维**判决对象不存在**，不判；但缺席照判，且数目照报。
        # 这不是"就近具名 skip"：它带数（下面那行把 356 张这类数全印出来）也带出路（再下面那行）。
        # 通道值里不许有裸 ASCII 空格（R565 那条：含空格的值会打死解析它的尺）。这里走
        # `sanitize_machine()` 而不是 `replace(" ", "_")`：后者那个空格字面量本身就会被
        # `ci_channel_hygiene.py` 的"值槽喂了一个含空格的串"那条判据抓成红（本轮实测），
        # 而前者是同一个函数、同一份语义（只抹标点、大小写照留）。逐字键在表头那一行照印。
        reason = ("baseline-unsigned" if not owner
                  else "baseline-owned-by:" + sanitize_machine(owner))
        print(u"FRAME_BASELINE_DRIFT %s 未登记（不判）=%d"
              % (common, len(verdict["unregistered"])))
        print(u"FRAME_BASELINE_DRIFT_NOT_JUDGED=%s" % reason)
        print(u"  出路  让这台机器有自己的基线（变帧维度就归它判）：在 %s 上跑 "
              u"`python3 scripts/frame_baseline.py update <那一台的帧目录> --for-machine`，"
              u"它会署名并写 docs/frame_baselines/by_machine/%s.json，随仓库提交即可。"
              u"（BACKLOG 658；R585 起这条命令真的会落那个文件 —— 上一版这里少写 `--for-machine`，"
              u"照旧命令跑完永远停在 `判=不判`；不许改期望、不许调宽阈值、不许把这一格读成「这台机器绿了」）"
              % (machine, sanitize_machine(machine)))
        blockers = len(missing) + len(verdict["unknown"]) + len(verdict["bad_fields"]) \
                 + len(verdict["rows_without_machine"]) + (1 if same_bake else 0)
    else:
        print(u"FRAME_BASELINE_DRIFT %s 已登记=%d 未登记=%d 陈旧行=%d"
              % (common, verdict["registered"], len(verdict["unregistered"]), len(verdict["stale"])))
        unreg_word = u"%d" % len(verdict["unregistered"])
        for name in verdict["unregistered"]:
            print(u"  未登记  %s  <- 既没在这台机器的名册里登记，也没人判它 ⇒ 门红（补登记走 register-drift，或查为什么变了；不许调宽阈值）" % name)
        for name in verdict["stale"]:
            print(u"  陈旧行（只报数）  %s  <- 这台机器此刻不漂；漂移按机器，删行会逼两台来回改" % name)
        blockers = len(missing) + len(verdict["unregistered"]) + len(verdict["unknown"]) \
                 + len(verdict["bad_fields"]) + len(verdict["rows_without_machine"]) \
                 + len(verdict["no_proof"]) + len(verdict["mismatch"]) + (1 if same_bake else 0)
    print(u"FRAME_BASELINE_RESULT=%s 拦路=%d（缺席%d 未登记%s 对不上%d 缺字段%d 缺机器%d 无出处%d 出处不符%d 同批%d）"
          % (u"ok" if blockers == 0 else u"red", blockers, len(missing), unreg_word,
             len(verdict["unknown"]), len(verdict["bad_fields"]),
             len(verdict["rows_without_machine"]), len(verdict["no_proof"]),
             len(verdict["mismatch"]), (1 if same_bake else 0)))
    return 0 if blockers == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
