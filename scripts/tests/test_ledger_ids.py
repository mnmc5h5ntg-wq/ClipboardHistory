#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""台账编号一致性守卫（R94 开，R102 加"重复编号"两格）。

为什么会有这支：R94 要往 `AGENT_DECISIONS.md` 追加 D-152 时，先 grep 了一下现有编号，
发现最后一条是 **D-150（R92）** —— 而 R93 的两处轮次标题里都写着"D-151"：

    AGENT_UI_AUDIT.md:4771        ## 第 95 轮 · R93：… / D-151
    AGENT_VISUAL_ITERATION.md:7620 ## Round 93 · … / D-151

⇒ 那是一条**被引用却不存在的决定**。它比"少写一条决定"更坏：下一个人（或下一个我）
按编号去查依据，查到的是一个空号，而两处标题的措辞让人以为那里写着结论。
根因很朴素：`ledgers_r93.py` 的 `STAGES` 里根本没有 decisions 那一格，
标题里的"D-151"是手抄的（R89 那条"台账正文里的数字与轮次标签不许手抄"的同一个形状，
只是这次抄的是一个还不存在的号）。

判什么：
  ① 轮次标题里出现的每一个 `D-\\d{3}`，都必须在 `AGENT_DECISIONS.md` 里有 `### D-xxx（RNN）` 那条正文；
  ② 决定条目自己的轮次标签必须与它写在哪儿无关 —— 只查号存在，不查内容（内容归人读）；
  ③ 编号必须连续（中间空一号 = 有人手抄了一个还没落盘的号，或者删过一条没改引用）。
"""
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DECISIONS = REPO / "AGENT_DECISIONS.md"
ROUND_HEADERS = (REPO / "AGENT_UI_AUDIT.md", REPO / "AGENT_VISUAL_ITERATION.md")
# 只认真正的定义行。**第一版写成 `^### (D-\d{3})（(R\d+)）`，只匹配到 36 条**，
# 于是 92 条被引用的编号里 83 条"缺失" —— 那是一堵假正例的墙，会把守卫直接推回去删掉。
# 实测这份台账的形状：老条目是 `## D-000 基线与分支（2026-10-08）`（121 条），
# 近来的轮次写成 `### D-150（R92）标题`（36 条），另有 `### D-037 追补：…` 这种补记行。
# ⇒ 定义 = 二/三级标题 + 编号开头；轮次标签只写在括号里，不作为闸门的一部分。
DEC_DEF = re.compile(r"^#{2,3} (D-\d{3})\b", re.M)
# 轮次标题行：`## 第 95 轮 · R93：…` / `## Round 93 · …`
HEADER = re.compile(r"^## (?:第 \d+ 轮|Round \d+) ·.*$", re.M)
CITED = re.compile(r"\bD-(\d{3})\b")


def defined_ids(text=None):
    if text is None:
        text = DECISIONS.read_text(encoding="utf-8")
    return [m.group(1) for m in DEC_DEF.finditer(text)]


def cited_ids(path):
    text = path.read_text(encoding="utf-8")
    out = []
    for header in HEADER.findall(text):
        out += CITED.findall(header)
    return out


def cited_everywhere():
    return {('D-' + n) for path in ROUND_HEADERS for n in cited_ids(path)}


class LedgerIdTests(unittest.TestCase):
    def test_every_decision_cited_in_a_round_header_exists(self):
        """① 引用要能落到一条正文上。"""
        defined = set(defined_ids())
        self.assertTrue(defined, "一条决定都没抓到 ⇒ 正则坏了，这条守卫是空的")
        missing = sorted(cited_everywhere() - defined)
        self.assertEqual([], missing,
                         "这些编号被轮次标题引用，但 `AGENT_DECISIONS.md` 里没有对应条目："
                         + "、".join(missing)
                         + " ⇒ 要么补上那条决定，要么把标题里的号改成真实存在的那条；不许删守卫")

    def test_decision_numbers_have_no_gaps(self):
        """③ 连续编号：空一号说明有人抄了一个还没落盘的号，或删过一条却没改引用。"""
        nums = sorted(int(x[2:]) for x in defined_ids())
        self.assertTrue(nums, "没有决定条目")
        holes = [n for n in range(nums[0], nums[-1] + 1) if n not in set(nums)]
        self.assertEqual([], holes, f"D-xxx 有空号：{holes}（最后一条是 D-{nums[-1]:03d}）")

    def test_the_guard_itself_is_not_vacuous(self):
        """正对照：把一条**确实被标题引用过**的决定从定义里抹掉，①必须只抓到它。

        没有这一格，①可以靠"引用集与定义集同时为空"永远绿（R85 那一族：初值即期望）。
        选靶子不能拿"最后一条"随手当：它未必被引用过（那就什么都测不到），
        所以要挑一个确实在引用集里的 —— 这里取编号最大的那条。
        """
        defined = set(defined_ids())
        cited = cited_everywhere()
        pool = sorted(defined & cited)
        self.assertGreaterEqual(len(pool), 3, "被引用又落盘的决定少于 3 条 ⇒ 样本不够，这条测试是空的")
        victim = pool[-1]
        text = DECISIONS.read_text(encoding="utf-8")
        stripped = re.sub(r"^#{2,3} " + victim + r"\b", "## 已删（" + victim + "）", text, count=1, flags=re.M)
        self.assertNotEqual(text, stripped, f"抹掉 {victim} 的定义行没生效 ⇒ 定义行的形状与正则不一致")
        after = set(m.group(1) for m in DEC_DEF.finditer(stripped))
        # 判的是**增量**：抹掉它之后，缺失集只许多出它这一条。
        # （第一版写成"缺失集正好等于 [victim]"，而仓库此刻真的还缺 D-151 ⇒ 两条红叠在一起，
        #  读日志的人会以为正对照在报同一个缺陷 —— 增量形状让这两件事各说各的。）
        self.assertEqual(set(cited - defined) | {victim}, cited - after,
                         f"抹掉 {victim} 之后守卫没有恰好多抓它一条 ⇒ 它不是在判'引用有没有落盘'")

    def test_citation_regex_does_not_match_prose_ids(self):
        """守卫不许命中正文里的引用（R53 那一族：region() 先命中守卫自己写的名字）。"""
        sample = "正文里提到 D-034 与 D-999，但它们不是定义行\n### D-034（R7）标题\n"
        self.assertEqual(["D-034"], [m.group(1) for m in DEC_DEF.finditer(sample)])


# ---------- R102 加的两格：重复编号 ----------
# 为什么现在才加：R102 收尾时我把 BACKLOG 151 的"结案"写成**新追加一条 151**，
# 于是同一个号有两份正文（一份说"待查"，一份说"已结案"）。
# 本文件原本只查 D 编号（①③两条），所以这件事**没有任何守卫会红** ——
# 我是靠 `grep -n "^15[0-3]\."` 数出来的。守卫的覆盖面比它声称的窄，这本身就是缺陷。
BACKLOG = REPO / "AGENT_BACKLOG.md"
ITEM = re.compile(r"^(\d{3})\. ", re.M)   # 只数这一代的三位号（早期快照用的是"快照 N"那种形状）
U_DEF = re.compile(r"^- \*\*U-(\d{3})", re.M)
# 轮次标题里声明的区间：`U-290…U-299`（省略号是 U+2026，不是三个点）。
U_RANGE = re.compile(r"U-(\d{3})…U-(\d{3})")


def newest_section(text):
    """取**编号最大**的那一节，不取"文件里第一个"那一节。

    为什么：`AGENT_UI_AUDIT.md` 的排序**不是单一方向** —— 前一半是升序（第 3 轮往后写），
    近来的这一段是降序（最新一轮在上面）。第一版这里写成"取第一个 `## 第 N 轮` 块"，
    于是拿到的是**第 3 轮**（它当然没有 `- **U-xxx` 那种定义行）⇒ 正对照报"样本不够"，
    而真台账那一格报"标题里没有区间"。与 R100 的 U-278 同族（两份台账排序方向相反），
    只是这次相反的是**同一份文件的两段**。
    """
    best, best_n = None, -1
    for part in re.split(r"(?m)^(?=## )", text):
        m = re.match(r"## 第 (\d+) 轮", part)
        if m and int(m.group(1)) > best_n:
            best, best_n = part, int(m.group(1))
    if best is None:
        raise AssertionError("找不到任何 `## 第 N 轮` 标题 ⇒ 这份账的形状变了，先改这一格")
    return best


def missing_in_declared_u_range(section):
    """标题声明的 U 区间里，哪些号在那一节中**没有**定义行。没有区间 ⇒ None（形状变了）。"""
    heading = section.splitlines()[0]
    m = U_RANGE.search(heading)
    if not m:
        return None
    lo, hi = int(m.group(1)), int(m.group(2))
    defined = set(U_DEF.findall(section))
    return ["U-%03d" % n for n in range(lo, hi + 1) if "%03d" % n not in defined]



def backlog_items(text=None):
    if text is None:
        text = BACKLOG.read_text(encoding="utf-8")
    return ITEM.findall(text)


def u_ids(text=None):
    if text is None:
        text = (REPO / "AGENT_UI_AUDIT.md").read_text(encoding="utf-8")
    return U_DEF.findall(text)


class DuplicateIdTests(unittest.TestCase):
    def test_backlog_item_numbers_are_unique(self):
        nums = backlog_items()
        # 地板是**量出来的**（今天实测 53 条三位号条目），不是我估的：
        # 这两份账只会更长，所以掉了就意味着形状变了，守卫该红。
        self.assertGreater(len(nums), 40, "只数到 %d 条 ⇒ 正则与这份账的形状不一致（今天实测 53）" % len(nums))
        dup = sorted({n for n in nums if nums.count(n) > 1}, key=int)
        self.assertEqual([], dup,
                         "BACKLOG 里这些编号出现了不止一次：%s ⇒ 同一号两份正文，读者不知道哪份作数" % dup)

    def test_ui_audit_ids_are_unique(self):
        ids = u_ids()
        # 今天实测 56 条。**为什么这么少**：`U-xxx` 只有在"一条一个要点"的新写法里才是
        # 行首加粗的定义（`- **U-284：…**`），更早的轮次把 U 写在句中或表里
        # ⇒ 这一格**只覆盖新-era 的定义**，不是"全部 U 都查过"。写清边界，
        # 免得它被当成全量守卫（R102 / U-294：这一格的覆盖面是量出来的，不是猜的）。
        self.assertGreater(len(ids), 40, "只数到 %d 条 U ⇒ 正则与这份账的形状不一致（今天实测 56）" % len(ids))
        dup = sorted({i for i in ids if ids.count(i) > 1})
        self.assertEqual([], dup, "AGENT_UI_AUDIT.md 里这些 U 编号被定义了两次：%s" % dup)

    def test_the_duplicate_guard_is_not_vacuous(self):
        """正对照：把一条**确实存在**的 BACKLOG 编号改成与另一条重复，①必须只抓到那一个号。"""
        nums = backlog_items()
        victim, other = nums[-1], nums[-5]
        text = BACKLOG.read_text(encoding="utf-8")
        forged = re.sub(r"^" + other + r"\. ", victim + ". ", text, count=1, flags=re.M)
        self.assertNotEqual(text, forged, "造重复失败 ⇒ 条目行的形状与正则不一致")
        after = backlog_items(forged)
        self.assertEqual([victim], sorted({n for n in after if after.count(n) > 1}),
                         "造出一个重复号之后守卫没只抓到它 ⇒ 它不是在判'编号唯一'")


class ChangelogShapeTests(unittest.TestCase):
    """R109 / U-352：`CHANGELOG.md` 的 `[Unreleased]` 标题必须**恰好一个**。

    起因是本轮自己写坏过一次：R108 往文件里插新节时，替换串里已经带着
    `## [Unreleased]` 标题，于是文件顶部出现两行同样的标题 —— 而这一族的守卫
    过去只看 `AGENT_*` 台账的编号，不看 CHANGELOG 的形状，所以它一路绿着进了提交。
    """

    def test_unreleased_heading_is_unique(self):
        text = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
        hits = [ln for ln in text.splitlines() if ln.strip() == "## [Unreleased]"]
        self.assertEqual(1, len(hits),
                         "`## [Unreleased]` 出现了 %d 次（插入新节时替换串自带标题就会这样）" % len(hits))

    def test_the_guard_itself_has_a_tooth(self):
        """正对照：多插一行标题，上面那条必须只抓到这一格。"""
        text = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
        broken = text.replace("## [Unreleased]", "## [Unreleased]\n## [Unreleased]", 1)
        hits = [ln for ln in broken.splitlines() if ln.strip() == "## [Unreleased]"]
        self.assertEqual(2, len(hits), "正对照本身坏了：拼不出两行标题，守卫就是恒真的")

class NewestRoundIdRangeTests(unittest.TestCase):
    """最新那一轮的标题说"这一轮有 U-290…U-299"，那这十个号**每一个**都要在那一节里有正文。

    为什么现在补这一格（R102 / U-299 之后又犯了第三次同一族）：这一轮我三次用
    "把上一行的标题行当 `old_string`"的方式编辑台账，于是"插入"变成"替换"，
    被吃掉的那一行**正是编号的定义行**（`## Round 99` 一次、`- **U-295：…` 一次、
    CHANGELOG 的 154 那一格一次）。前两次分别靠"曲线仪器报 GAPS"和"我手工按编号列一遍"抓到的，
    第三次是我自己看见的 —— 三把都是人肉，而这一族的形状其实完全可以机器判：
    **标题声明的区间与正文里的定义集合必须吻合**。
    覆盖面边界（与 U-294 同一句话）：只查**最新一节**，因为更早的轮次把 U 写在句中、
    或标题里用的是别的写法 ⇒ 拿老账套这条会撞上一堵假正例的墙（第一版就报了 83 条"缺失"）。
    """

    def test_declared_range_is_fully_defined(self):
        text = (REPO / "AGENT_UI_AUDIT.md").read_text(encoding="utf-8")
        sec = newest_section(text)
        missing = missing_in_declared_u_range(sec)
        self.assertIsNotNone(missing, "最新一轮的标题里没有 `U-xxx…U-yyy` 这种区间 ⇒ 形状变了，先改这一格")
        self.assertEqual([], sorted(missing),
                         "标题声明了区间，但这些号在那一节里**没有定义行**：%s"
                         " ⇒ 十有八九是编辑时把标题行当 old_string 吃掉了" % missing)

    def test_the_range_guard_is_not_vacuous(self):
        """正对照：从最新一节里**删掉一条真实的定义行**，这一格必须只报那一个号。"""
        text = (REPO / "AGENT_UI_AUDIT.md").read_text(encoding="utf-8")
        sec = newest_section(text)
        ids = U_DEF.findall(sec)          # 捕获组只有三位数字，如 "299"
        self.assertGreaterEqual(len(ids), 3, "最新一节只有 %d 条定义 ⇒ 样本不够，正对照无意义" % len(ids))
        victim = ids[-1]
        forged = re.sub(r"(?m)^- \*\*U-%s：.*$\n?" % re.escape(victim), "", sec, count=1)
        self.assertNotEqual(sec, forged, "删不掉那条定义 ⇒ 正则与这份账的形状不一致")
        self.assertEqual(["U-%s" % victim], sorted(missing_in_declared_u_range(forged)),
                         "删了一条定义而守卫没只抓到它 ⇒ 它不是在判'区间与定义吻合'")


if __name__ == "__main__":
    unittest.main()
