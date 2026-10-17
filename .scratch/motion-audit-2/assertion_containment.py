#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""断言/读数**集合包含**对账：把"改完之后某一句悄悄没了"变成一条能跑的、有出处的检查。

为什么要它（R101 / U-289 的实底）：我编辑 `UICaptureHarness.swift` 时，
`XCTAssertEqual(control.count, 2, "系统参照必须亮暗两档各一条…")` 这一整条**被替换掉了**，
而 `swift test` 全绿 —— 因为少一条断言不会让任何东西红。
第一次发现它靠的是一次性的 `python3 - <<PY`（把改前/改后的断言消息当多重集比），
**那把尺没落盘**，于是"我确实丢了那一条"这件事本身也无从复查（与 U-287 同形：
一次性脚本 + 被删的产物 = 台账里留着一句无法复查的话）。这一版把尺钉在仓库里。

口径（每条key怎么来的，写清楚免得日后误读）：
- **断言**：`XCTAssert*(` 后面第一个字符串字面量的**规范化前 60 字符**。
  规范化 = 折叠空白 + **把每一处插值 `\\(任意表达式)` 折成一个 `\\(…)`** + 去掉 `\\"` 的痕迹。
  折插值是为了：消息里 `\\(count)` 改成 `\\(counts.count)` 属于**同一句话换了个变量**，
  不算丢失（不折的话第一版自检就误报了这一格 —— 见 `selftest()` 的第二个构造用例）。
  代价写在这里：两条只有插值不同的断言会并成同一个 key，
  所以本工具判的是**每个 key 的出现次数**，数量差（2→1）仍然是丢失，照样报。
- **读数通道**：`emit("TAG …` 里的那个**大写成 TAG**（≥4 个字符，允许 `_`、数字）。
  TAG 是判据的对外契约（CI 只读得到这些行），所以 TAG 消失与断言消失同级。

它**不能**做的事，也写在这里免得被当成全能守卫：
- 不看语义：同一条断言换了字面前缀会被记成"一丢一得"，需要人读那两条是不是同一件事；
- 不看结构：把断言从一个函数搬到另一个函数，它只说"这一份里有"；
- 只比**同一支文件**的两个版本，跨文件的搬动它判不了。

用法：
  python3 .scratch/motion-audit-2/assertion_containment.py <文件> [--ref HEAD]
  python3 .scratch/motion-audit-2/assertion_containment.py --selftest
退出码：0=没有"丢失"，1=有丢失，2=用法/读取错误。
"""
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ASSERT_HEAD = re.compile(r"\b(XCTAssert\w*)\s*\(")
# 字符串字面量：先吃掉 Swift 的 `+` 拼接里每一段，只取第一段做 key（见文档串"口径"）。
FIRST_STRING = re.compile(r'"((?:[^"\\]|\\.)*)"')
EMIT_TAG = re.compile(r'\bemit\(\s*"([A-Z][A-Z0-9_]{3,})')
INTERP = re.compile(r"\\\(.*?\)")

KEY_LEN = 60


def keyname(k):
    """断言的 key 是 `(XCTAssert…, 消息)` 二元组，读数 TAG 的 key 是**裸字符串**。

    第一版这里写 `k[0]` / `k[1]` ⇒ 对 TAG 那种字符串键取到的是**第一个字符与第二个字符**，
    于是四行 `GAINED C … A` 这种"格式像结论、内容是字母"的东西被打印出来（R102 / U-302 同族）。
    """
    return k[0] if isinstance(k, tuple) else k


def keybody(k):
    return k[1] if isinstance(k, tuple) else ""


def normalize(s):
    s = re.sub(r"\s+", " ", s.replace('\\"', '"')).strip()
    return INTERP.sub(r"\\(…)", s)


def first_string_in_call(text, start):
    """从 `XCTAssert…(` 之后扫**这一次调用自己的括号范围**，取第一个字符串字面量。

    为什么要有它（R106 / U-333）：上一版是 `text[m.end():m.end()+4000]` 里找第一个引号 ——
    那会**越过调用的右括号**读到后面别的语句的消息里。后果不是漏判而是**假丢失**：
    本轮在文件中间插入一个新判据之后，两条本来就没有消息的 `XCTAssertEqual`
    的 key 从"找不到那张产品表格"变成了别的字符串，闸门报 `CONTAINMENT_LOST=1`、
    整卷 `VERIFY_OK=0`，而被删掉的东西**一个都没有**（`git diff` 里 0 条删除行）。
    一把会把"我加了代码"读成"我丢了断言"的尺，下一轮就会被想去放宽它的人拿掉。
    """
    depth = 1
    i = start
    n = len(text)
    while i < n:
        c = text[i]
        if c == "\"":
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == "\"":
                    break
                j += 1
            return text[i + 1:j]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return None
        i += 1
    return None


def extract(text):
    """返回 (断言 key 的多重集, 读数 TAG 的多重集)。"""
    a = Counter()
    for m in ASSERT_HEAD.finditer(text):
        body = first_string_in_call(text, m.end())
        a[(m.group(1), normalize(body)[:KEY_LEN] if body else "<无消息>")] += 1
    e = Counter()
    for m in EMIT_TAG.finditer(text):
        e[m.group(1)] += 1
    return a, e


def git_show(ref, path):
    r = subprocess.run(["git", "show", "%s:%s" % (ref, path)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write("git show 失败：%s:%s\n%s\n" % (ref, path, r.stderr.strip()))
        sys.exit(2)
    return r.stdout


def diff_counts(before, after):
    """返回 after 里比 before 少的条目（含数量差）。"""
    lost = []
    for k, n in before.items():
        m = after.get(k, 0)
        if m < n:
            lost.append((k, n, m))
    return sorted(lost, key=lambda t: (-t[1], str(t[0])))


def report(path, ref, repo):
    before_text = git_show(ref, str(path.relative_to(repo)).replace("\\", "/"))
    after_text = Path(path).read_text(encoding="utf-8")
    ba, be = extract(before_text)
    aa, ae = extract(after_text)
    lines = ["CONTAINMENT ref=%s file=%s" % (ref, path.name)]
    for label, b, a in (("断言", ba, aa), ("读数TAG", be, ae)):
        lost = diff_counts(b, a)
        gained = [(k, n, a[k]) for k, n in a.items() if n > b.get(k, 0)]
        lines.append("  %s：改前 %d 种/%d 处 ⇒ 改后 %d 种/%d 处 ⇒ 丢失=%d 新增=%d"
                     % (label, len(b), sum(b.values()), len(a), sum(a.values()),
                        len(lost), len(gained)))
        for k, n, m in lost:
            lines.append("    LOST   %-14s ×%d→×%d  %s" % (keyname(k)[:14], n, m, keybody(k)))
        for k, n, m in sorted(gained, key=lambda z: -z[2])[:6]:
            lines.append("    GAINED %-14s ×%d→×%d  %s" % (keyname(k)[:14], n, m, keybody(k)))
    n_lost = sum(1 for l in lines if l.strip().startswith("LOST"))
    print("\n".join(lines))
    return n_lost


def selftest():
    """正对照：**构造**一次丢失，工具必须只抓到那一条（否则它是恒 0 的假守卫）。"""
    old = '''
        XCTAssertEqual(control.count, 2, "系统参照必须亮暗两档各一条（借来的常数没有这个性质）")
        XCTAssertFalse(aboveRoster.isEmpty, "名单空了")
        emit("CARD_ABOVE_CAPABILITY settings格=\\(x)")
    '''
    new = '''
        XCTAssertFalse(aboveRoster.isEmpty, "名单空了")
        emit("CARD_ABOVE_CAPABILITY settings格=\\(x)")
    '''
    oa, oe = extract(old)
    na, ne = extract(new)
    lost = diff_counts(oa, na)
    ok_lost = len(lost) == 1 and lost[0][0][1].startswith("系统参照必须亮暗两档各一条")
    # 反面对照①：同一句话里插值的**变量名**变了，不该算丢失
    old2 = 'XCTAssertEqual(a, 1, "边距=\\(d)pt 这一屏只有一张卡片")'
    new2 = 'XCTAssertEqual(a, 1, "边距=\\(d.count)pt 这一屏只有一张卡片")'
    ok_quiet = not diff_counts(extract(old2)[0], extract(new2)[0])
    # 反面对照②：折插值会把两条并成同一个 key，所以**数量差**必须仍然算丢失
    old3 = ('XCTAssertGreaterThan(x, 1, "边距=\\(d)pt 这一格要有对象")\n'
            'XCTAssertGreaterThan(y, 1, "边距=\\(d)pt 这一格要有对象")')
    new3 = 'XCTAssertGreaterThan(x, 1, "边距=\\(d)pt 这一格要有对象")'
    ok_count = len(diff_counts(extract(old3)[0], extract(new3)[0])) == 1
    print("SELFTEST 构造丢失被抓=%s 改插值不误报=%s 少一条同文断言要报=%s"
          % (ok_lost, ok_quiet, ok_count))
    return 0 if (ok_lost and ok_quiet and ok_count) else 1


def lines_mode(paths, ref):
    """**HEAD 的每一行是否都还在工作树里**（R100 / U-278 立的固定动作，R102 落盘成工具）。

    为什么需要它：`git diff --numstat` 看不出来 —— 一个纯移动块会显示成"删 + 增"，
    而"编辑台账时 `old_string` 取了上一节的标题行"这种事故（R99 的 `## Round 99`、
    本轮的 `- **U-295：…**` 与 CHANGELOG 的 154 那一格）在 numstat 里长得跟正常改写一样。
    它**不判"该不该丢"** —— 丢掉的每一行都要人逐条归因（R101：102 行里逐条数过才发现 U-289 那条被吃掉的断言），
    它只保证「丢掉的行有几条、分别是什么」这件事不是靠印象。
    """
    repo = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"],
                               capture_output=True, text=True).stdout.strip())
    total_lost = 0
    for f in paths:
        path = repo / f if not Path(f).is_absolute() else Path(f)
        rel = str(path.relative_to(repo))
        try:
            before = git_show(ref, rel)
        except SystemExit:
            print("SKIP %s（%s 里没有这一支文件 ⇒ 新增文件，无历史可比）" % (rel, ref))
            continue
        from collections import Counter
        b = Counter(l for l in before.splitlines() if l.strip())
        a = Counter(l for l in path.read_text(encoding="utf-8").splitlines() if l.strip())
        lost = sorted((b - a).elements())
        total_lost += len(lost)
        print("LOSTLINES %-34s HEAD=%d 工作树=%d 丢掉=%d" % (Path(rel).name, sum(b.values()), sum(a.values()), len(lost)))
        for l in lost[:12]:
            print("    - %s" % l[:150])
        if len(lost) > 12:
            print("    …另有 %d 行" % (len(lost) - 12))
    print("TOTAL_DROPPED=%d（每一行都要人工归因：是有意改写，还是被 old_string 吃掉）" % total_lost)
    return 0


def main():
    args = sys.argv[1:]
    if not args or "--selftest" in args:
        return selftest()
    if args[0] == "--lines":
        repo = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"],
                                   capture_output=True, text=True).stdout.strip())
        rest = args[1:]
        ref = "HEAD"
        if "--ref" in rest:
            i = rest.index("--ref")
            ref = rest[i + 1]
            rest = rest[:i] + rest[i + 2:]
        return lines_mode(rest, ref)
    repo = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"],
                               capture_output=True, text=True).stdout.strip())
    ref = "HEAD"
    if "--ref" in args:
        i = args.index("--ref")
        ref = args[i + 1]
        del args[i:i + 2]
    total_lost = 0
    for f in args:
        p = Path(f)
        if not p.is_absolute():
            p = repo / f
        if not p.exists():
            sys.stderr.write("文件不存在：%s\n" % p)
            return 2
        total_lost += report(p, ref, repo)
    print("CONTAINMENT_LOST=%d" % total_lost)
    return 1 if total_lost else 0


if __name__ == "__main__":
    sys.exit(main())
