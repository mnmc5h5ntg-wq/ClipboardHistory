#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R238 / BACKLOG 250：把 `test_ledger_ids` 的「定义行」从只认标题扩成「标题 ∪ 粗体定义行」，
并按 BACKLOG 要求配**正 / 负两格**对照。事务性：任何锚点没恰好命中就拒绝写盘。"""
import io

P = "scripts/tests/test_ledger_ids.py"
t = io.open(P, encoding="utf-8").read()
orig = t


def rep(old, new, n=1):
    global t
    c = t.count(old)
    assert c == n, "锚点命中 %d 次（要 %d）：%r" % (c, n, old[:70])
    t = t.replace(old, new, 1)


# ① 模块 docstring：把「什么算定义行」写进去，并留下本轮实测的形状数字
rep("  ③ 编号必须连续（中间空一号 = 有人手抄了一个还没落盘的号，或者删过一条没改引用）。",
    "  ③ 编号必须连续（中间空一号 = 有人手抄了一个还没落盘的号，或者删过一条没改引用）。\n"
    "\n"
    "R238（BACKLOG 250）：① 的「定义行」从**只认标题**扩成**标题 ∪ 粗体定义行**。\n"
    "现场数字（本轮在真台账上实测，不是估的）：标题形 201 条、粗体形 28 条、两集**零重叠**、\n"
    "并集 D-000…D-222 **无空洞**。在此之前那 28 条对 ① 完全隐形 —— R224 的电池红\n"
    "（`missing=['D-216']`）就是同一件事第一次露头，当时的处置是把标题里的引用撤掉（止血不是修）。\n"
    "扩正则**不配单独算结案**：`BoldDefinitionLineTests` 用同一份合成语料的两态对照，\n"
    "让「粗体那一半有没有接上」与「老标题那一半有没有被弄坏」各自能被证伪。")

# ② 正则：一支正则两种形状（不许写成两份实现互相掩盖 —— R108 那一族）
rep('DEC_DEF = re.compile(r"^#{2,3} (D-\\d{3})\\b", re.M)',
    '# R238 之前的字面，保留**只**给「老形状仍算定义」那格当对照用。\n'
    'DEC_DEF_HEADING_ONLY = re.compile(r"^#{2,3} (D-\\d{3})\\b", re.M)\n'
    'BOLD_DEF = re.compile(r"^\\*\\*(D-\\d{3})（", re.M)\n'
    '# 定义行 = 标题 ∪ 粗体定义行，写成**一支**正则：两半同生同死，\n'
    '# 不许出现「两份实现各自判、其中一份坏了另一份掩盖」那种形状。\n'
    'DEC_DEF = re.compile(r"^(?:#{2,3} (D-\\d{3})\\b|\\*\\*(D-\\d{3})（)", re.M)\n'
    '\n'
    '\n'
    'def ids_from(text):\n'
    '    """把 DEC_DEF 的两种形状收敛成一个号列表（组 1 = 标题形，组 2 = 粗体形）。"""\n'
    '    return [m.group(1) or m.group(2) for m in DEC_DEF.finditer(text)]')

# ③ defined_ids 走 ids_from
rep('def defined_ids(text=None):\n'
    '    if text is None:\n'
    '        text = DECISIONS.read_text(encoding="utf-8")\n'
    '    return [m.group(1) for m in DEC_DEF.finditer(text)]',
    'def defined_ids(text=None):\n'
    '    if text is None:\n'
    '        text = DECISIONS.read_text(encoding="utf-8")\n'
    '    return ids_from(text)')

# ④ 引用集也要能在合成语料上跑（两态对照的前提）
rep('def cited_ids(path):\n'
    '    text = path.read_text(encoding="utf-8")\n'
    '    out = []\n'
    '    for header in HEADER.findall(text):\n'
    '        out += CITED.findall(header)\n'
    '    return out',
    'def cited_in(text):\n'
    '    """轮次标题里引用到的号 —— 收文本，好让对照能喂合成语料。"""\n'
    '    out = []\n'
    '    for header in HEADER.findall(text):\n'
    '        out += CITED.findall(header)\n'
    '    return out\n'
    '\n'
    '\n'
    'def cited_ids(path):\n'
    '    return cited_in(path.read_text(encoding="utf-8"))')

# ⑤ 正对照的抹除要认两种形状（否则 victim 换成粗体的 D-222 就红在「抹不掉」上 —— 尺坏不是产品坏）
rep('def defined_ids(text=None):',
    'def strip_definition(text, victim):\n'
    '    """按**当前形状**抹掉一条决定的定义行：标题形或粗体形，两种都要能抹。\n'
    '\n'
    '    这一格以前只写 `^#{2,3} victim`。R238 把定义集扩成两种形状之后，编号最大的那条\n'
    '    被引用决定是**粗体**的（D-222）⇒ 只抹标题形的话 stripped 与 text 一模一样，\n'
    '    正对照会红在「抹不掉」那一句上 —— 那说的是尺，不是台账。\n'
    '    """\n'
    '    for pat in (r"^#{2,3} " + victim + r"\\b", r"^\\*\\*" + victim + r"（"):\n'
    '        out = re.sub(pat, "## 已删（" + victim + "）", text, count=1, flags=re.M)\n'
    '        if out != text:\n'
    '            return out\n'
    '    return text\n'
    '\n'
    '\n'
    'def defined_ids(text=None):')

rep('        stripped = re.sub(r"^#{2,3} " + victim + r"\\b", "## 已删（" + victim + "）", text, count=1, flags=re.M)',
    '        stripped = strip_definition(text, victim)')

rep('        after = set(m.group(1) for m in DEC_DEF.finditer(stripped))',
    '        after = set(ids_from(stripped))')

# ⑥ 正文不许命中：顺手把「粗体但不在行首」也纳入这一格的范围
rep('        sample = "正文里提到 D-034 与 D-999，但它们不是定义行\\n### D-034（R7）标题\\n"\n'
    '        self.assertEqual(["D-034"], [m.group(1) for m in DEC_DEF.finditer(sample)])',
    '        sample = ("正文里提到 D-034 与 D-999，但它们不是定义行\\n"\n'
    '                  "句子里有 **D-998（R9）** 这种加粗引用，行首不是星号 ⇒ 不算定义\\n"\n'
    '                  "### D-034（R7）标题\\n")\n'
    '        self.assertEqual(["D-034"], ids_from(sample))')

# ⑦ 新表：两态对照 + 老形状仍算 + 真台账的负格（现有粗体条一条都不许被读成缺失）
rep('if __name__ == "__main__":',
    'class BoldDefinitionLineTests(unittest.TestCase):\n'
    '    """R238 / BACKLOG 250：扩出来的那半正则，必须**各自**能被证伪。\n'
    '\n'
    '    为什么不能只改正则就算结案：这条守卫在过去若干轮里一直是**绿的**，而它看不见 28 条决定\n'
    '    ——「绿的守卫」不等于「有效的守卫」（R85 那一族：只在自家夹具上成立的理由比没做决定更贵）。\n'
    '    所以这里用**同一份合成语料、两态对照**：给粗体正文 ⇒ ① 不许报缺失；不给 ⇒ ① 必须只报那一条。\n'
    '    再加两格管住反向风险：老标题形状不许被扩正则弄坏、真台账里现有的粗体条不许被读成缺失。\n'
    '    """\n'
    '\n'
    '    FORGED = "D-223"          # 合成号：仓库里不存在，专门用来伪造「被引用却没正文」\n'
    '    OLD_SHAPE = "D-000"       # 真台账里最老的那条，标题形，用来证明老形状仍算定义\n'
    '\n'
    '    def corpus(self, with_bold):\n'
    '        text = ("## Round 999 · 假轮次（R999）：" + self.FORGED + "\\n"\n'
    '                + "## 第 999 轮（R999）：假标题 " + self.FORGED + "\\n"\n'
    '                + "### " + self.OLD_SHAPE + " 老形状仍在（2026-10-08）\\n")\n'
    '        if with_bold:\n'
    '            text += "**" + self.FORGED + "（R999）：伪造的决定正文**\\n"\n'
    '        return text\n'
    '\n'
    '    def test_bold_definition_line_makes_the_citation_land(self):\n'
    '        """两态之一：给了粗体定义行 ⇒ 引用集与定义集的差必须为空。"""\n'
    '        text = self.corpus(with_bold=True)\n'
    '        self.assertIn(self.FORGED, ids_from(text),\n'
    '                      "粗体定义行没进定义集 ⇒ DEC_DEF 的粗体那一半没接上")\n'
    '        self.assertEqual([], sorted(set(cited_in(text)) - set(ids_from(text))),\n'
    '                         "给了正文却仍报缺失 ⇒ ① 与这份台账的形状不一致")\n'
    '\n'
    '    def test_without_any_definition_line_it_is_red(self):\n'
    '        """两态之二：同一份语料**不给**粗体正文 ⇒ 必须只报那一条伪造号。\n'
    '\n'
    '        少了这一格，上面那格可以靠「引用集 = 定义集 = 空」永远绿（初值即期望）。\n'
    '        """\n'
    '        text = self.corpus(with_bold=False)\n'
    '        self.assertNotIn(self.FORGED, ids_from(text))\n'
    '        self.assertEqual([self.FORGED], sorted(set(cited_in(text)) - set(ids_from(text))),\n'
    '                         "没给正文也不报缺失 ⇒ ① 是恒真的")\n'
    '\n'
    '    def test_the_older_heading_shape_is_still_a_definition(self):\n'
    '        """扩正则的反向风险：老标题形状一条都不许因为这次放宽而丢掉。\n'
    '\n'
    '        对照用 `DEC_DEF_HEADING_ONLY`（R238 之前的字面）在真台账上跑：\n'
    '        老集合必须是新集合的子集，而且**多出来的那批恰好等于**粗体定义行 ——\n'
    '        不等于就说明有第三种形状混进了定义集（那才是下一次假绿的入口）。\n'
    '        """\n'
    '        text = DECISIONS.read_text(encoding="utf-8")\n'
    '        new = set(defined_ids(text))\n'
    '        old = set(DEC_DEF_HEADING_ONLY.findall(text))\n'
    '        self.assertTrue(old, "标题形一条都没抓到 ⇒ 正则坏了")\n'
    '        self.assertTrue(old <= new,\n'
    '                        "老形状里的号现在读不到：%s ⇒ 这次改动把守卫弄坏了" % sorted(old - new))\n'
    '        self.assertEqual(set(BOLD_DEF.findall(text)), new - old,\n'
    '                         "新增可见的号不等于粗体定义行 ⇒ 定义集里混进了别的形状")\n'
    '\n'
    '    def test_recent_bold_decisions_are_not_read_as_missing(self):\n'
    '        """负格（BACKLOG 250 要的那一半）：现有粗体条一条都不许被读成「没正文」。\n'
    '\n'
    '        地板 20 是**量出来的**（本轮实测 28 条），不是我估的：这份账只会更长，\n'
    '        掉了说明形状变了，守卫该红。\n'
    '        """\n'
    '        text = DECISIONS.read_text(encoding="utf-8")\n'
    '        bold = BOLD_DEF.findall(text)\n'
    '        self.assertGreaterEqual(len(bold), 20,\n'
    '                                "只数到 %d 条粗体定义行 ⇒ 与这份台账的形状不一致（本轮实测 28）" % len(bold))\n'
    '        missing = sorted({("D-" + n) for n in bold} - set(defined_ids(text)))\n'
    '        self.assertEqual([], missing, "粗体决定被读成缺失：%s" % missing)\n'
    '        # 这一格还要真的**改过判据**：把粗体那一半从正则里摘掉（只留标题形），\n'
    '        # 上面那条负格必须红 —— 否则它只是在陈述「正则现在能匹配」，没有牙。\n'
    '        blind = set(DEC_DEF_HEADING_ONLY.findall(text))\n'
    '        would_be_missing = sorted({("D-" + n) for n in bold} - blind)\n'
    '        self.assertEqual(len(bold), len(would_be_missing),\n'
    '                         "只用老标题形时这些粗体条没全部变成缺失 ⇒ 这 28 条里有的其实是标题形")\n'
    '        self.assertGreaterEqual(len(would_be_missing), 20,\n'
    '                                "摘掉粗体那一半之后缺失数少于 20 ⇒ 正对照样本不够")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":')

assert t != orig, "什么都没改"
io.open(P, "w", encoding="utf-8").write(t)
print("PATCH_R238 写了 7 处锚点：docstring / DEC_DEF / defined_ids / cited_in / strip_definition / 正文样例 / 新表")
