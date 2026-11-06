# -*- coding: utf-8 -*-
"""R588 / 靶 1：台账里「第③段已经落了件」这类断言，必须由第②段闸门的全过证人陪着，否则红。

来历（不是修辞问题）：R587 的收口自陈写「规格 §3 第②③段各落一件」，而同一笔里
`git diff --name-only HEAD~2 HEAD -- Sources/` 为空、两条具名阻塞（646 签字口径、647 穿透机制、
`STAGE3_FRAME_CRITERIA_HAVE_NO_RUNNER_WITNESS`）一条没撤 ⇒ 那句话是假的。
台账是下一轮唯一的事实源，一句「③落了一件」会被后面轮次读成闸门已过 ⇒ 直接撞
`docs/FOLD_DUO_SPEC_2026-11-03.md` §3 那句「顺序是闸门 / 三问任一不过 ⇒ 停在这里，不写着色器」。

两种坏法分开钉：
①**明写的断言**：「第③段」与 已开工/落地/完成/做了/推进/落了一件 同句 ⇒ 断言。
②**冒充段号的小节编号**：STATE 那一族的正文小节本来就按 ⓪①②③⑦⑧⑨ 编号（本轮的第几小节），
  而 R586/R587 把它写成 `段号=③` —— 那三个字与规格 §3 的「第③段」同字 ⇒ 下一轮分不清。
  ⇒ 规矩：小节编号写「本节③」，`段号=` 只许跟规格 §3 的真实段号，且必须与证人同句。

判法写成纯函数 `classify_line` / `verdict`（注释里的分类法等于没有，见记忆那条），
证人只从**两处**来：规格文档 §3 那一段里有没有「三问全过」的句子，以及台账里那两条具名阻塞
是否已被撤（撤了要有名，不许静默消失）。

范围为什么是**最新一节**：这一支只管未来（同 `red_name_reconciliation.py` 的形状）。
历史节里那句 `段号=③` 仍然在盘上 ⇒ 按「改账不删原文」不回头改，但这里要**数出来**并印成读数，
否则「历史里还有几处在冒充段号」这件事又变成没人知道的量。

用法：python3 scripts/stage_gate_claims.py [--state PATH] [--spec PATH]
退出码：0=判过且没有无证断言；1=有无证断言（红）；2=读不到台账或规格（通道缺席，不算通过）。
"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(REPO, "AGENT_STATE.md")
ITER = os.path.join(REPO, "AGENT_VISUAL_ITERATION.md")
SPEC = os.path.join(REPO, "docs", "FOLD_DUO_SPEC_2026-11-03.md")

# 第②段那两条具名阻塞：撤了才算闸门过；只要还有一条在，任何第③段断言都是无证。
BLOCKERS = (u"STAGE2_CLICKTHROUGH_BLOCKED", u"STAGE3_FRAME_CRITERIA_HAVE_NO_RUNNER_WITNESS")
STAGE3_TOKEN = u"第③段"
# 枚举写法也要认得：`第②③段` 里并不含子串 `第③段`，第一版就是这么漏掉 ITERATION 那一行的
# ⇒ 段号一律按「第 + 若干圈码 + ③ + 段」认，不按子串认（R586 靶 B 那一课的同一族：**名字不是属性，段才是**）。
STAGE3_RX = re.compile(u"第[①②③④]*③段")
CLAIM_WORDS = (u"已开工", u"开工", u"落地", u"落了", u"完成", u"做了", u"推进", u"已写", u"动笔")
# 两种坏法各一条正则：
# A **小节编号冒充段号**：`段号=③`（STATE 那一族的正文小节按 ⓪②③ 编号，写成 `段号=` 就与 §3 的段号同字）
FAKE_STAGE_NUM = re.compile(u"段号[=＝]\\s*[①②③④]")
# B **把第③段说成本轮的段**：`段号…第③段`（含 `段号仍是第②③段` 这种并列写法），或 `第③段` 同句跟一个推进词
STAGE3_IS_CURRENT = re.compile(u"段号[^。\\n]{0,12}" + STAGE3_RX.pattern)
STAGE3_CLAIM = re.compile(u"[^。\\n]{0,40}" + STAGE3_RX.pattern + u"[^。\\n]{0,40}(已开工|开工|落地|落了|完成|做了|推进|已写|动笔)")
# 「第③段没开工 / 未开工 / 一字未写 / 继续不开工 / 一字未动」是**反向**陈述，不算断言
NEGATED = re.compile(u"(没开工|未开工|不开工|一字未写|一字没写|一字未动|一字没动|仍未|继续不)")


QUOTED = re.compile(u"「[^」]*」")


def unquote(line):
    """把「…」里的**引用**摘掉再判谓词。

    为什么必须有这一步：守卫搜的两个串（段号 + 段号字样）也是**讲这条规矩本身**时无法避免的词。
    没有这一步，写手只能靠改措辞躲守卫（那是把门调松），而有了这一步，规矩是：
    **引用里的段号字样不算断言，句子主干里的才算**。代价也说清：把一句真断言整段包进「」可以躲过
    这一支 —— 但 `冒充段号` 那一支仍走原文（不摘引用），所以"段号=圈码"这种形状无论如何红。
    """
    return QUOTED.sub(u"", line)


def sentence_tail(body, start):
    """从匹配点起到**句末**（句号或行尾）——反向词的管辖范围是句子，不是正则那一段。
    少了这一步，「段号仍是第②段（第③段一字未动）」会被读成断言：反向词在括号里、在匹配段之外。
    """
    rest = body[start:]
    cut = rest.find(u"。")
    return rest if cut < 0 else rest[:cut + 1]


def classify_line(line):
    """一行 → 五种之一（先否后肯：「第③段着色器一字未写」不许被读成断言）。"""
    if FAKE_STAGE_NUM.search(line):
        return u"冒充段号"
    body = unquote(line)
    if not STAGE3_RX.search(body):
        return u"无关"
    m = STAGE3_IS_CURRENT.search(body) or STAGE3_CLAIM.search(body)
    if not m:
        # 没配上断言式，但整行带着反向词 ⇒ 归"反向陈述"（守卫要能说出它是**哪一种**不是断言：
        # 一句「第③段一字未写」和一句「§4 提到第③段的着色器」在账上的分量不同，混成"提及"就丢了这条）
        return u"反向陈述" if NEGATED.search(body) else u"提及"
    if NEGATED.search(sentence_tail(body, m.start())):
        return u"反向陈述"
    return u"断言"


HEAD_ALL = re.compile(u"(?m)^## (?:R(\\d{3}) 状态|R(\\d{3}) 补记|Round \\d+ · (R\\d{3}))")


def sections(text):
    """按**轮次标题**切节，三种形状一起认（STATE 的主节、STATE 的补记、ITERATION 的 Round 节）。
    只认第一种会漏掉补记节 —— 而补记里同样会写「段号=…」；三种形状各自试、命中第一个就返回，
    则是另一件坏法（同一本台账里两种标题混着切，最新一节就切错）。
    切不出来 ⇒ 返回空表，调用方必须**不判并点名**（不许退回全文去判历史）。
    """
    marks = []
    for m in HEAD_ALL.finditer(text):
        raw = next(g for g in m.groups() if g)
        # 三种标题的捕获不一样（前两种只捕获到数字，第三种带 R）⇒ 统一成 `Rnnn`，
        # 否则 latest() 比的是 "900" 与 "R587"，字符串比较会把 R 排在数字后面。
        name = raw if raw.startswith(u"R") else u"R" + raw
        marks.append((m.start(), name))
    out = []
    for i, (start, name) in enumerate(marks):
        stop = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        out.append((name, text[start:stop]))
    return out


def latest(sections_, key=int):
    """**同一轮**可能有主节 + 补记两节 ⇒ 取号最大的那一轮，并把这一轮的所有节并起来判，
    否则「最新一节」会只挑到补记而把主节里那句假话放过。"""
    if not sections_:
        return (u"", u"")
    top = max(s[0] for s in sections_)
    bodies = u"\n".join(b for n, b in sections_ if n == top)
    return (top, bodies)


def scan(text, only_latest=True, section=None):
    """返回 (逐行分类结果, 断言行, 冒充段号行, 范围)。only_latest ⇒ 只判最新那一轮，历史只数不判。
    section="R587" ⇒ 判**指定那一轮**（测试要用它把「历史证人」钉成永久读数，而不是跟着轮次漂）。"""
    secs = sections(text)
    if not secs:
        # 切不出轮次节 ⇒ 不判、并点名（不许退回全文去判历史）
        return [(u"（没切出轮次节）", u"通道缺席", text[:80])], [], [], u"未切节_不判"
    if section:
        pick = [b for n, b in secs if n == section]
        if not pick:
            return [], [], [], u"没这一节_%s" % section
        target, scope = u"\n".join(pick), section
    elif only_latest:
        scope, target = latest(secs)
    else:
        target, scope = text, u"全文"
    rows, claims, fakes = [], [], []
    for raw in target.splitlines():
        kind = classify_line(raw)
        if kind != u"无关":
            rows.append((scope, kind, raw.strip()[:160]))
        if kind == u"断言":
            claims.append(raw.strip()[:160])
        if kind == u"冒充段号":
            fakes.append(raw.strip()[:160])
    return rows, claims, fakes, scope


def witnesses(spec_text, state_text):
    """闸门全过的证人：规格里有一句「三问全过」（不含「未/仍不/没」），且两条阻塞都已具名撤除。"""
    passed = False
    for line in spec_text.splitlines():
        if u"三问全过" in line and not re.search(u"(未|仍不|没|不)", line.split(u"三问全过")[0][-12:]):
            passed = True
    still = [b for b in BLOCKERS if b in state_text]
    return {"三问全过在规格里": passed, "仍挂着的阻塞": still}


def verdict(claims, fakes, wit):
    """判法：无证断言红；有断言但证人齐 ⇒ 绿；冒充段号一律红（它让下一轮分不清小节编号与段号）。"""
    reds = []
    if fakes:
        # ⚠ 消息本身不许含被它搜的那两个串：守卫的输出会被抄进台账，而台账正是它判的对象
        # （R562「守卫搜的串不许出现在自己正文」的这一支：中招的是**仪器自己的措辞**）。
        reds.append(u"冒充段号=%d 处（小节编号被写成段号的样子 ⇒ 改成「本节③」）" % len(fakes))
    if claims:
        if not wit[u"三问全过在规格里"]:
            reds.append(u"段号无证断言=%d 条：规格里读不到「三问全过」那一句 ⇒ 闸门未过" % len(claims))
        if wit[u"仍挂着的阻塞"]:
            reds.append(u"段号无证断言=%d 条：两条具名阻塞仍挂着：%s"
                        % (len(claims), u",".join(wit[u"仍挂着的阻塞"])))
    return reds


def main(argv=None):
    ap = argparse.ArgumentParser(description="台账里第③段断言的闸门对账")
    ap.add_argument("--state", default=STATE)
    ap.add_argument("--iter", default=ITER)
    ap.add_argument("--spec", default=SPEC)
    ap.add_argument("--all-sections", action="store_true",
                    help="历史节也数（只报数不判，默认只判最新一节）")
    ap.add_argument("--section", default=None,
                    help="只判这一节（例如 R587 ⇒ 把「这条守卫抓得住当年那句假话」钉成永久证人）")
    args = ap.parse_args(argv)
    for p, label in ((args.state, u"STATE"), (args.spec, u"规格")):
        if not os.path.exists(p):
            print(u"STAGE_GATE_INPUT_MISSING %s 读不到 %s ⇒ 这一格记未读到，不算通过" % (label, p))
            return 2
    state = io.open(args.state, encoding="utf-8").read()
    itertext = io.open(args.iter, encoding="utf-8").read() if os.path.exists(args.iter) else u""
    spec = io.open(args.spec, encoding="utf-8").read()
    wit = witnesses(spec, state)

    rows_s, claims_s, fakes_s, scope = scan(state, only_latest=not args.all_sections, section=args.section)
    rows_i, claims_i, fakes_i, _ = scan(itertext, only_latest=not args.all_sections, section=args.section) \
        if itertext else ([], [], [], u"（ITER 没读到）")
    claims = claims_s + claims_i
    fakes = fakes_s + fakes_i
    reds = verdict(claims, fakes, wit)

    print(u"STAGE_GATE_CLAIMS 判的范围=STATE %s + ITER 最新一节 三问全过证人=%s 仍挂着的阻塞=%d%s"
          % (scope, u"有" if wit[u"三问全过在规格里"] else u"无",
             len(wit[u"仍挂着的阻塞"]),
             u"（%s）" % u",".join(wit[u"仍挂着的阻塞"]) if wit[u"仍挂着的阻塞"] else u""))
    print(u"STAGE_GATE_COUNT 断言=%d 冒充段号=%d 提及或反向=%d"
          % (len(claims), len(fakes), len(rows_s) + len(rows_i) - len(claims) - len(fakes)))
    for row in (claims_s + fakes_s + claims_i + fakes_i)[:6]:
        print(u"  逐字：%s" % row)
    if args.all_sections:
        hist = scan(state, only_latest=False)
        print(u"STAGE_GATE_HISTORY 全文 断言=%d 冒充段号=%d（历史按「改账不删原文」只数不判）"
              % (len(hist[1]), len(hist[2])))
    for r in reds:
        print(u"STAGE_GATE_RED " + r)
    if reds:
        print(u"STAGE_GATE_RESULT=red 拦路=%d" % len(reds))
        return 1
    print(u"STAGE_GATE_RESULT=ok 无证断言=0（本轮没有段号形状的断言，或有断言而两个证人齐）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
