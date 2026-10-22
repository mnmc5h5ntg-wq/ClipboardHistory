# -*- coding: utf-8 -*-
"""R304 的守卫：七本台账里不许留下**没被替换的占位符**。

为什么这条守卫存在（两笔实测，不是我猜的形状）：

· `AGENT_BACKLOG.md` 346 的「R296 结案」追记落盘时留着七个洞（GW / GINC / GCOLD / GTARGET / KC / KN / KREST），
  也就是说那句「本机基线现读 warnings=…」在账上从来没被读过。
· 同一本 305 的「R295」追记留着四个洞（OL / RL / OD / RD 的变颗平均）。

两处都由本轮就地更正，值从别处的同一批现读记录取回（见那两行的注记）。

成因不是手滑，是**写台账那一次没有任何东西读它**：台账生成器把替换键注册成复数（`TOUCHES`）而正文写单数
（`@TOUCH@`）时，插入照常成功、事后电池照常绿 —— 这一族正是 348 那一单说的「写台账本身没有门」。
所以本文件的形状是：先证明这把尺**会红**（注入桩），再证明它**不冤枉真实文本**（属性标注 `@MainActor`、
`@objc`、倍率写法 `@1x` 对 `@2x`、邮箱一类都不算占位符），最后才拿它扫盘上的七本。
"""
import io
import os
import re
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 七本台账（与 audit-round-verification-loop 声明的那一套同一份名单）。
BOOKS = [
    'AGENT_UI_AUDIT.md',
    'AGENT_VISUAL_ITERATION.md',
    'AGENT_DECISIONS.md',
    'AGENT_BACKLOG.md',
    'CHANGELOG.md',
    'AGENT_STATE.md',
    'AGENT_FINAL_REPORT.md',
]

# 占位符的形状：一对 at 号夹着一个**全大写**的词（生成器的替换键一律是大写）。
# 刻意不收小写 —— 真实的 Swift 属性标注（`@MainActor`、`@objc`、`@Environment`）与倍率写法（`@1x`、`@2x`）
# 都带 at 号，把它们算进去会让这门天天红、于是天天被绕。
TOKEN_RX = re.compile(r'@([A-Z][A-Z0-9_]{1,24})@')


def read(name):
    return io.open(os.path.join(REPO, name), encoding='utf-8').read()


def find_tokens(text):
    """返回 [(行号, 整串)]，按行号升序。逐行数以保证报出来的行号能直接跳过去。"""
    hits = []
    for number, line in enumerate(text.split(u'\n'), 1):
        for match in TOKEN_RX.finditer(line):
            hits.append((number, match.group(0)))
    return hits


def scan_books():
    """扫七本台账，返回 {文件名: [(行号, 串)]}。文件不在盘上**不算扫过**（抛出去 = 名单不许空转）。"""
    found = {}
    for name in BOOKS:
        path = os.path.join(REPO, name)
        if not os.path.exists(path):
            raise AssertionError(u'台账名单里的一份不在盘上：%s ⇒ 扫描对象漂了，不是"没找到洞"' % name)
        found[name] = find_tokens(read(name))
    return found


class LedgerTokenTests(unittest.TestCase):

    def test_positive_control_the_estimator_fires_on_injected_stubs(self):
        """先让这把尺在**已知答案**的桩上红：两种真实漏法（键写成复数 / 值整段没替换）。"""
        stub = (u'本机基线现读 warnings=@GW@ incremental=@GINC@；'
                u'一次搬动要同步 @TOUCH@。\n第二行没有洞。\n还有带下划线的 @OL_CMEAN@。\n')
        hits = find_tokens(stub)
        self.assertEqual(
            [(1, u'@GW@'), (1, u'@GINC@'), (1, u'@TOUCH@'), (3, u'@OL_CMEAN@')], hits,
            u'注入的三个洞没被数出来 ⇒ 盘上那七本就算有洞也会报绿')

    def test_negative_control_real_at_signs_are_not_placeholders(self):
        """反方向：真实的属性标注、倍率写法、邮箱一律不算洞（冤枉人的门会被绕）。"""
        prose = (u'@MainActor static func emit(_ line: String) { }\n'
                 u'@objc private final class TableProbe\n'
                 u'@Environment(\\.colorScheme) var scheme 与 @AppStorage("x")\n'
                 u'颗数 332 对 1290 差约 4 倍（@1x 对 @2x 的面积比）\n'
                 u'联系 maintainer@example.com，@unknown default 也要覆盖\n'
                 u'两道门抢同一标签时读各自比较式：`warnings=@GCOLD@` 这一类**才是**洞，但 '
                 u'`@MainActor` 不是。\n')
        self.assertEqual([
            (6, u'@GCOLD@'),
        ], find_tokens(prose), u'反方向的真实文本被数进来了 ⇒ 这门会天天红，然后天天被放宽')

    def test_the_scan_targets_a_non_empty_book_roster(self):
        """名单不许空转：七本都要在盘上且都不是一页空纸（否则「零个洞」是假的）。"""
        self.assertEqual(7, len(BOOKS), u'台账名单应当是七本，现读 %d' % len(BOOKS))
        sizes = dict((name, len(read(name))) for name in BOOKS)
        thin = dict((k, v) for k, v in sizes.items() if v < 20000)
        self.assertEqual({}, thin, u'这几本薄得不像台账（%s）⇒ 扫描对象漂了' % sorted(thin))

    def test_no_unsubstituted_placeholder_survives_in_the_ledgers(self):
        """正题：七本台账里没有一处「at 号夹着的大写词」留下的洞。"""
        found = scan_books()
        stray = []
        for name in BOOKS:
            for number, token in found[name]:
                stray.append(u'%s:%d %s' % (name, number, token))
        # 读数落在这里：绿的时候也要能说清"扫了几本、扫了多少字符"（只印不拦 = 没有读数，但拦了也要留数）
        total_chars = sum(len(read(name)) for name in BOOKS)
        print(u'LEDGER_TOKENS books=%d chars=%d stray=%d' % (len(BOOKS), total_chars, len(stray)))
        self.assertEqual(
            [], stray,
            u'台账里有没被替换的占位符（生成器的键与正文不一致 ⇒ 那一格记的是原文而不是读数）：'
            + u'；'.join(stray[:12]))


if __name__ == '__main__':
    unittest.main(verbosity=2)
