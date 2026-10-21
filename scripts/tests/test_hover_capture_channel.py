#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""悬停取证通道的名册：每一个会画 hover 的产品视图，要么接了取证键，要么在名册里点名为什么没接。

为什么这一卷存在（R248 / BACKLOG 251 第三处）：`MultiFileRow`（`DetailView.swift:609` 那一族）的悬停
**量不到**，成因不是"没有夹具"，是捕获键从来没接到它 —— `.onHover` 的 `isHovered` 在离屏渲染里恒 false，
所以两态帧永远拍不出差别，而"拍不出差别"很容易被记成"这一位没问题"（R90 那一族：量不到 ≠ 没问题）。
本轮把这件事变成一条按文件计数、且能被红掉的守卫：新增一个悬停位点而**没**接通道 ⇒ 名册少一行 ⇒ 红。

形状照仓库的既有做法（`SEAM_READER_ISOLATION` 同一族）：现读文件、现数、结论行先打、判定后做，
名册按**方向**给（未接的才要理由），每条理由 ≥20 字。
"""
import io
import os
import re
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
VIEWS = os.path.join(REPO, 'ClipboardHistory', 'Sources', 'ClipboardHistoryApp', 'Views')
KEY = 'hoveredForCapture'

# 现读（R248）：这四个文件画悬停却没有把键接进来。这张表是**欠账名册**，不是豁免 ——
# 每一行必须写清"这一位的悬停今天靠什么被看见"，以及"接上键要动哪里"；下一轮做完一项就从表里删掉一行。
# 名册与代码按**集合**对账：新增未接位点却不登记 ⇒ 红；登记了却已经接上 ⇒ 也红（名册过期）。
DEBT = {
    'DailyCopyHeatmapView.swift': '不接键是有意的：夹具走 `heatmapCellStrip(hoveredIndex:)` 那条入参，产品路径不读键。'
                                  '两态帧在盘上（heatmap-cell-strip-still / -hover，亮暗各一张），'
                                  '判据是 HeatmapHoverEvidenceTests 那五格（逐档可辨、只动圈带、不许盖过数据深浅）。'
                                  'R280 现读更正：这一行以前写的是一句否定（说 hover 那一档拍不到），'
                                  '而基线里一直有四张 ⇒ 散文没人对账，假话挂了三十几轮。'
                                  '注意：这张表的否定词是被**字面**读的（守卫分不清引用与断言），'
                                  '所以旧原话只进台账，不进这里',
    'GlassControls.swift': '欠账：这里只剩注释与 .pressedStyle(hoverLevel:) 的委托，真正的悬停墨换算在 PressableStyle（已接键）里；'
                           '登记的理由是"本文件不再有独立的悬停画法"，若哪天又自己画一层就必须接键',
    # R263 删掉 `HistoryRowViews.swift` 那一行（"做完一行删一行"）：它自己直读 `isHovered` 的画法
    # 只有一处 —— `RowFavoriteButton.tint` 的 0.55↔0.78 字形墨，现已与 `.pressedStyle` 那一层
    # 一样走 `isHoveredForDrawing`，判据是 `UICaptureTests.testFavoriteGlyphInkClearsTheInteractiveFloor`
    # （从帧里读静置/悬停两态的字形墨，并把注释里那句"两边都过 3:1"升成会红的地板）。
    # 留在这里的是**没被删掉的那半句**：当年"120 行的 .onHover 还驱动着什么画法，本轮没量"
    # 是猜，R263 数清了：一处（tint）+ 一条 animation value。
    'VideoPreview.swift': '欠账：两处 .pressedStyle(hoverLevel:) 委托给已接键的 PressableStyle，'
                          '但预览卡自身没有两态夹具帧；登记是因为它从未进过帧基线，不是因为不需要',
}

# R280：名册理由里「有没有两态帧」那一半，此前只是散文 —— 盘上明明有 `heatmap-cell-strip-{still,hover}`
# 四张，理由却写着"没有独立的两态帧"，而双向守卫看不见它（它比的是"文件读没读键"，不是"理由里那句可复查的话"）。
# 现在把那半句抽成表：**前缀必须在帧基线名单里真的有两张不同状态的帧**，理由文本也不许再写与它对矛盾的否定句。
TWO_STATE_CLAIMS = {
    'DailyCopyHeatmapView.swift': 'heatmap-cell-strip',
    'GlassControls.swift': 'NO_INK',   # 本文件没有独立悬停画法：两态在 PressableStyle 那一位（已接键）
    'VideoPreview.swift': None,        # 现读：预览卡从未进过帧基线 ⇒ 这一位确实没有两态帧
}
NEGATIONS = (u'没有独立的两态帧', u'没有两态夹具帧', u'从未进过帧基线', u'没有两态帧')
DELEGATIONS = (u'委托', u'PressableStyle')
BASELINE = os.path.join(REPO, 'docs', 'frame_baseline.json')


def frame_manifest():
    """帧基线的名单（基名）。读不到就抛 —— 这把尺不许在"没有对象"时给出"没问题"。"""
    import json
    with io.open(BASELINE, encoding='utf-8') as h:
        data = json.load(h)
    frames = data.get('frames') or {}
    if not frames:
        raise AssertionError('帧基线里没有帧表 ⇒ 「有没有两态帧」无从判定，不许读成没问题：键='
                             + ','.join(list(data)[:6]))
    return sorted(os.path.basename(k) for k in frames)


def claim_problems(rows, manifest, debt=None, claims=None):
    """名册的**第二条轴**：理由里那句关于两态帧的话，要与帧名单对账。"""
    debt = DEBT if debt is None else debt
    claims = TWO_STATE_CLAIMS if claims is None else claims
    bad = []
    unwired = set(n for n, w in rows if not w)
    if unwired != set(claims):
        bad.append(('HOVER_CLAIM_SET_DRIFT',
                    '未接键的文件集合与两态声明表不相交等：名册缺 %s / 多 %s（R76：豁免名册必须双向相等）'
                    % (sorted(unwired - set(claims)), sorted(set(claims) - unwired))))
    for name in sorted(unwired & set(claims)):
        prefix = claims[name]
        reason = debt.get(name, '')
        negated = [w for w in NEGATIONS if w in reason]
        if prefix == 'NO_INK':
            if not [w for w in DELEGATIONS if w in reason]:
                bad.append(('HOVER_CLAIM_NO_INK_WITHOUT_DELEGATION',
                            '%s 声明"本文件没有独立悬停画法"，理由里却没有点名画法搬到哪里去了 ⇒ 撤项没有去处'
                            % name))
            continue
        if prefix:
            hits = [f for f in manifest if f.startswith(prefix)]
            states = sorted(set(f[len(prefix):].lstrip('-').split('-')[0] for f in hits))
            if len(states) < 2:
                bad.append(('HOVER_CLAIM_FRAMES_MISSING',
                            '%s 声明靠 %s* 那组两态帧被看见，而帧基线里只数到状态 %s（%s）⇒ 声明不成立'
                            % (name, prefix, states or '无', hits)))
            if negated:
                bad.append(('HOVER_REASON_CONTRADICTS_FRAMES',
                            '%s 的两态帧在名单里（%s），理由却还写着「%s」⇒ 散文与读数相反'
                            % (name, prefix, negated[0])))
        elif not negated:
            bad.append(('HOVER_CLAIM_UNDECLARED_GAP',
                        '%s 没有声明两态帧前缀，理由里也没有一句点名"没有两态帧"⇒ 这一位的缺席没人记账'
                        % name))
    return bad



def hover_files(views=VIEWS):
    out = []
    for name in sorted(os.listdir(views)):
        if not name.endswith('.swift'):
            continue
        text = io.open(os.path.join(views, name), encoding='utf-8').read()
        code = strip_line_comments(text)
        if any(tok in code for tok in ('.onHover', 'hoverLevel', 'HoverInk')):
            out.append(name)
    return out


def strip_line_comments(text):
    """R249 / M813 现读出来的坏法：`KEY in text` 会被**引用了键名的注释**喂饱 —— 我自己记过这条规矩
    （整文件 contains 命中自己引用的注释，扫前剥行注释），却还是把它写错了。M813 摘掉真正的声明时
    名册那格不红，就是这条假绿的证人。剥注释比的是"代码里有没有"，不是"文件里提没提"。"""
    return '\n'.join(l.split('//')[0] for l in text.split('\n'))


def wiring(views=VIEWS):
    """返回 [(文件, 是否接键)]，按文件名排序 —— 结论行要打印的就是这张表（只看代码，不看注释）。"""
    rows = []
    for name in hover_files(views):
        text = strip_line_comments(io.open(os.path.join(views, name), encoding='utf-8').read())
        rows.append((name, KEY in text))
    return rows


def problems(rows):
    bad = []
    for name, wired in rows:
        if wired:
            if name in DEBT:
                bad.append(('HOVER_CHANNEL_DOUBLE', '%s 既接了键又在豁免名册里 ⇒ 名册过期' % name))
            continue
        if name not in DEBT:
            bad.append(('HOVER_CHANNEL_UNPAIRED',
                        '%s 画悬停却没有取证键 ⇒ 这一位拍不出两态帧（量不到不许当没问题）' % name))
        elif len(DEBT[name]) < 20:
            bad.append(('HOVER_CHANNEL_REASON_TOO_SHORT', '%s 的豁免理由不足 20 字' % name))
    return bad


class HoverCaptureChannelTests(unittest.TestCase):
    def test_the_roster_covers_every_hover_bearing_view(self):
        rows = wiring()
        self.assertTrue(rows, 'Views/ 里一个悬停位点都没读到 ⇒ 识别器坏了，不许当成通过')
        codes = [c for c, _ in problems(rows)]
        self.assertEqual([], codes, '取证通道名册与代码不同步：%s' % codes[:6])

    def test_the_declined_roster_is_not_a_trash_bin(self):
        """负对照：把已接通道的文件塞进豁免名册 ⇒ 必须红（名册只登记"故意不接"，不是"没做"）。"""
        rows = wiring()
        wired = [n for n, w in rows if w]
        self.assertTrue(wired, '没有任何已接通道的文件 ⇒ 这张对照没有对象')
        saved = DEBT.pop('DetailView.swift', None)
        try:
            DEBT[wired[0]] = '故意不接（这一格是把名册当垃圾桶的对照，理由本身不算数）'
            codes = [c for c, _ in problems(rows)]
            self.assertIn('HOVER_CHANNEL_DOUBLE', codes,
                          '已接键的文件进豁免名册时不许红 ⇒ 这一格是假的')
        finally:
            DEBT.pop(wired[0], None)
            if saved is not None:
                DEBT['DetailView.swift'] = saved

    def test_an_unrostered_missing_channel_is_named(self):
        """正对照：从表里删掉一行（模拟新增悬停位点却没接键也没登记）⇒ 必须点名。"""
        rows = [r for r in wiring() if r[1]]
        self.assertTrue(rows, '没有已接通道的行可拿来造对照')
        broken = [(rows[0][0], False)] + rows[1:]
        codes = [c for c, _ in problems(broken)]
        self.assertIn('HOVER_CHANNEL_UNPAIRED', codes, '把接了键的说成没接时不许静默通过')


class TwoStateClaimTests(unittest.TestCase):
    """R280：名册理由里那句「有没有两态帧」必须与帧名单对账 —— 它此前挂了三十几轮没人发现是假的。"""

    def test_every_undeclared_hover_file_declares_its_two_state_evidence(self):
        rows = wiring()
        manifest = frame_manifest()
        codes = [c for c, _ in claim_problems(rows, manifest)]
        self.assertEqual([], codes, '两态声明与帧基线名单不同步：%s' % codes[:4])

    def test_a_prefix_that_no_frame_manifest_contains_is_caught(self):
        """正对照（尺有牙）：把声明的前缀改成一个名单里不存在的东西 ⇒ 必须点名。"""
        rows = wiring()
        manifest = frame_manifest()
        saved = dict(TWO_STATE_CLAIMS)
        try:
            for name, prefix in saved.items():
                if prefix:
                    TWO_STATE_CLAIMS[name] = prefix + '_NOT_ON_DISK'
                    codes = [c for c, _ in claim_problems(rows, manifest)]
                    self.assertIn('HOVER_CLAIM_FRAMES_MISSING', codes,
                                  '声明指向不存在的帧时不许静默通过（这一格是假的）')
                    break
            else:
                self.fail('名册里没有任何带前缀的声明 ⇒ 这把对照没有对象，先补声明再谈牙')
        finally:
            TWO_STATE_CLAIMS.clear()
            TWO_STATE_CLAIMS.update(saved)

    def test_prose_denying_frames_that_exist_is_caught(self):
        """正对照（散文与读数相反）：帧在名单里，理由却写「没有两态帧」⇒ 必须点名。

        这一格钉的正是本轮修掉的那个原罪：`DailyCopyHeatmapView` 的理由以前写着"hover 那一档
        没有独立的两态帧"，而 `heatmap-cell-strip-{still,hover}` 四张一直在基线里。
        """
        rows = wiring()
        manifest = frame_manifest()
        prefix = [p for p in TWO_STATE_CLAIMS.values() if p]
        self.assertTrue(prefix, '没有前缀可拿来造对照')
        name = [k for k, v in TWO_STATE_CLAIMS.items() if v][0]
        saved = DEBT[name]
        try:
            DEBT[name] = saved + u'（人造反驳：hover 那一档没有独立的两态帧）'
            codes = [c for c, _ in claim_problems(rows, manifest)]
            self.assertIn('HOVER_REASON_CONTRADICTS_FRAMES', codes,
                          '理由与名单相反时不许绿 ⇒ 这条守卫只是在读散文，不是在读对象')
        finally:
            DEBT[name] = saved

    def test_a_missing_frame_claim_without_a_negation_is_caught(self):
        """反方向也要有牙：声明为"没有两态帧"的文件，理由里必须真的点名那份缺席。"""
        rows = wiring()
        name = [k for k, v in TWO_STATE_CLAIMS.items() if v is None]
        self.assertTrue(name, '没有 None 声明可拿来造对照')
        saved = DEBT[name[0]]
        try:
            DEBT[name[0]] = u'这一位的理由被换成了一句不含任何缺席陈述的话，只讲它接了委托。'
            codes = [c for c, _ in claim_problems(rows, frame_manifest())]
            self.assertIn('HOVER_CLAIM_UNDECLARED_GAP', codes,
                          '没有两态帧却不在理由里写明 ⇒ 这一位的缺席会静默消失（R100：有键无值）')
        finally:
            DEBT[name[0]] = saved


class SearchFieldChannelTests(unittest.TestCase):

    def test_search_field_ink_honours_the_capture_channel(self):
        """R249 / BACKLOG 291：这一位是名册里唯一"画法本身拍不到"的真缺陷，现已接上。

        断言打在**画法**上而不是文件里有没有键：图标墨与清除按钮的可见性都必须读同一层
        `isHoveredForDrawing`；谁再退回裸 `isHovered`，这一格就红。
        """
        text = io.open(os.path.join(VIEWS, 'SearchField.swift'), encoding='utf-8').read()
        self.assertIn('@Environment(\\.hoveredForCapture) private var hoveredForCapture', text,
                      'SearchField 里没有取证键 ⇒ 291 没做完')
        self.assertIn('.foregroundStyle(isHoveredForDrawing ? VisualInk.controlTargeted : VisualInk.control)', text,
                      '图标墨又读回裸 isHovered ⇒ 两态帧拍不到这一条（量不到 ≠ 没问题）')
        self.assertIn('isHoveredForDrawing || !text.isEmpty', text,
                      '清除按钮的可见性又读回裸 isHovered ⇒ 悬停时它出现不出现，帧里读不到')
        self.assertNotIn('isHovered || !text.isEmpty', text, '残留一处直读 isHovered')


class HoverChannelReadingsTests(unittest.TestCase):
    def test_the_channel_is_present_where_the_hover_is_drawn(self):
        """R248 的那笔产品改动：`MultiFileRow` 的填充与描边共用一个判定。"""
        text = io.open(os.path.join(VIEWS, 'DetailView.swift'), encoding='utf-8').read()
        self.assertIn('@Environment(\\.hoveredForCapture) private var hoveredForCapture', text,
                      'DetailView 里没有取证键 ⇒ 251 第三处仍未接')
        self.assertGreaterEqual(text.count('isHoveredForDrawing'), 3,
                                'isHoveredForDrawing 应当被声明一次、用在填充与描边两处（<3 ⇒ 只接了一半）')
        self.assertNotIn('.fill(.primary.opacity(isHovered\n', text,
                         '还有一处填充直接读 isHovered ⇒ 两态帧里那一半不会亮')


if __name__ == '__main__':
    rows = wiring()
    print('HOVER_CHANNEL_ROSTER 悬停位点=%d 已接键=%d 未接=%d 豁免=%d' % (
        len(rows), sum(1 for _, w in rows if w), sum(1 for _, w in rows if not w), len(DEBT)))
    for name, wired in rows:
        print('  %s %s' % ('接' if wired else '未', name))
    unittest.main(verbosity=2)
