#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R298 / BACKLOG 350：轮标题声明的 U 区间必须与该节真的定义的 id 对得上。

为什么现在才上门（顺序本身就是这一单的结论）：先量形状，再定门。现读 `AGENT_UI_AUDIT.md`
289 节里 213 节标题带 `U-a…U-b` 区间形；其中 31 节是**旧式叙述节**（整节没有一条规范定义行，
U id 只出现在标题与散文里）。一上来按「区间里的每个 id 都要有定义行」判，会造出 34 个假正例
（R94 那一课：守卫的定义行正则要按台账实际形状写，只认一种形状会漏掉一批真的东西）。

分箱之后再判，形状问题又露出第二层：定义行的粗体里可以夹一个括注 ——
`- **U-351（做对的一格）：…**` 与 `- **U-344（做对的一格）**：…`（冒号在粗体外面），
旧正则 `^- \\*\\*U-(\\d+)：` 对它们恒不匹配，于是第 110 / 111 轮被误判成「缺 U-344 / U-351」。
本支的 `DEF` 因此认三种形状（纯 id 后紧跟冒号、id 后带括注再冒号、括注在粗体内而冒号在粗体外）。

分箱 + 并集形状之后，结构化节里真不符的只剩 **1 节**：第 103 轮标题写 `U-280…U-289`，
而它规范定义的是 282…289（280 / 281 只以散文形式出现：`- **R100 我装的能力闸门是坏的**（U-280 / D-164）`）。
这一处登记在 `KNOWN` 里并**要求名单恰好等于它** —— 名单不许长（新的不符必须当场处理），
也不许空转（判据坏掉时名单会算不出来而红）。正对照：删掉一条定义行 ⇒ 必须被点名。
"""
import io
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UI = os.path.join(ROOT, "AGENT_UI_AUDIT.md")

# 三种定义行形状（并集）。第 3 种是「括注在粗体内、冒号在粗体外」。
DEF = re.compile(u"(?m)^- \\*\\*U-(\\d+)(?:（[^）]*）)?\\*{0,2}[：:]")
RANGE = re.compile(u"U-(\\d+)…U-(\\d+)")
HEAD = re.compile(u"(?m)^## 第 (\\d+) 轮")

# 已知且登记在册的不符：{节标题里的轮次: (声明区间, 实定义区间, 原因)}
KNOWN = {
    103: (u"U-280…U-289", u"实定义 282…289",
          u"280 / 281 只以散文形式出现在本节（`- **R100 我装的能力闸门是坏的**（U-280 / D-164）`），"
          u"它们作为规范定义行属于更早的节 ⇒ 标题区间多写了两个号。留着是因为改历史标题会牵动 "
          u"round_batch / ledger_ids 两把守卫，处理方案记在 350 的追记里。"),
}


def read(path):
    with io.open(path, encoding="utf-8") as h:
        return h.read()


def sections(text):
    starts = [(m.group(1), m.start()) for m in HEAD.finditer(text)]
    out = []
    for i, (num, start) in enumerate(starts):
        end = starts[i + 1][1] if i + 1 < len(starts) else len(text)
        out.append((int(num), text[start:end]))
    return out


def check(text):
    """返回 (结构化节数, 叙述形节数, 不符列表)。"""
    struct = narr = 0
    bad = []
    for num, body in sections(text):
        title = body.splitlines()[0]
        m = RANGE.search(title)
        if not m:
            continue
        ids = sorted(set(int(x) for x in DEF.findall(body)))
        if not ids:
            narr += 1
            continue
        struct += 1
        a, b = int(m.group(1)), int(m.group(2))
        missing = [x for x in range(a, b + 1) if x not in ids]
        extra = [x for x in ids if not (a <= x <= b)]
        if missing or extra:
            bad.append((num, u"U-%d…U-%d" % (a, b), missing, extra))
    return struct, narr, bad


class UiRoundIntervalParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read(UI)
        cls.struct, cls.narr, cls.bad = check(cls.text)

    def test_the_ruler_sees_the_three_definition_shapes(self):
        """先钉尺自己：三种形状都要能数出来 —— 漏一种就会把「有定义」误判成「缺定义」。"""
        sample = (u"## 第 1 轮 · R1：x（U-1…U-3）\n"
                  u"- **U-1：甲**\n"
                  u"- **U-2（做对的一格）：乙**\n"
                  u"- **U-3（做对的一格）**：丙\n")
        self.assertEqual([1, 2, 3], [int(x) for x in DEF.findall(sample)],
                         u"并集正则没认全三种形状 ⇒ 350 的分箱会退回假正例")

    def test_bins_are_measured_not_assumed(self):
        self.assertGreater(self.struct, 150, u"结构化节只数到 %d ⇒ 分箱的尺坏了" % self.struct)
        self.assertGreater(self.narr, 0, u"叙述形节数读成 0 ⇒ 这一箱不见了（旧节被改写或正则变了）")

    def test_mismatches_equal_the_named_roster(self):
        got = {num: (rng, missing, extra) for num, rng, missing, extra in self.bad}
        self.assertEqual(sorted(KNOWN), sorted(got),
                         u"不符名单变了。现读：%s；在册：%s" % (
                             sorted((n, r, mi, ex) for n, r, mi, ex in self.bad),
                             sorted(KNOWN)))
        for num, rng, missing, extra in self.bad:
            self.assertTrue(missing or extra, u"第 %d 轮被登记成不符却既不缺也不多" % num)

    def test_positive_control_deleting_a_definition_is_caught(self):
        """正对照：删掉最新一节的一条规范定义行 ⇒ 必须被点名（否则门是恒绿的）。"""
        newest = sections(self.text)[0][0]
        m = list(re.finditer(DEF, self.text))
        self.assertTrue(m, u"整本台账数不出一条规范定义行 ⇒ 正对照没有对象")
        first = m[0]
        forged = self.text[:first.start()] + self.text[first.start():].replace(
            first.group(0), first.group(0).replace(u"**U-", u"**U9-x-", 1), 1)
        _, _, bad = check(forged)
        self.assertTrue(bad, u"删掉一条定义行却不点名 ⇒ 这一格没有牙")

    def test_the_newest_section_is_structured(self):
        """新轮次不许退回叙述形 —— 否则「分箱豁免」会变成新的漏口。"""
        num, body = sections(self.text)[0]
        m = RANGE.search(body.splitlines()[0])
        self.assertIsNotNone(m, u"最新一节（第 %d 轮）标题没有 U 区间" % num)
        self.assertTrue(DEF.findall(body),
                        u"最新一节声明了区间却一条定义行都没有 ⇒ 新节退化成叙述形")


if __name__ == "__main__":
    unittest.main()
