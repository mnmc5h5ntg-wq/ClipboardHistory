# R239 补记：把「重复编号」守卫的 ITEM 从只认 `^NNN. ` 扩成 `^NNN. ∪ **^NNN. `
import io, re, json, pathlib
G = 'scripts/tests/test_ledger_ids.py'
t = io.open(G, encoding='utf-8').read()
orig = t
hits = []

def rep(old, new, n=1):
    global t
    c = t.count(old)
    assert c == n, '锚点命中 %d 次（要 %d）：%r' % (c, n, old[:70])
    t = t.replace(old, new, n)
    hits.append(old[:40])

# ① 模块 docstring：在文档串结尾的 """ 之前插一段本轮说明
s0 = t.index('"""', t.index('"""') + 3)
NOTE = (
    'R239 补记（BACKLOG 270）：同一族的第二处隐形 —— ②「BACKLOG 编号唯一」的 ITEM 只认行首\n'
    '`^NNN. `，而这份账近一半条目写成 `**NNN. `（R239 实测：标题形 72 条、粗体形 90 条，\n'
    '并集 162 条、零重叠、无重复）。⇒ R102 立这条守卫的那次事故（同号两份正文）若发生在粗体形那批里，\n'
    '守卫一路绿着。**只扩正则、不放宽地板**，并把地板从 40 抬到量出来的 150（绝对锚点：\n'
    '正则退回只认标题形就只剩 72 条，这一格立刻红）。老那一半用子集格守：标题形集合必须仍是并集的子集。\n'
)
t = t[:s0] + NOTE + t[s0:]
hits.append('docstring')

# ② ITEM 正则：一支、两种形状（不写两份实现互相掩盖）
rep('ITEM = re.compile(r"^(\\d{3})\\. ", re.M)   # 只数这一代的三位号（早期快照用的是"快照 N"那种形状）',
    'ITEM = re.compile(r"^(?:\\*\\*)?(\\d{3})\\. ", re.M)   # R239：标题形 ∪ 粗体形（一支正则两种形状）\n'
    'ITEM_HEADING_ONLY = re.compile(r"^(\\d{3})\\. ", re.M)   # 老字面，只当对照用\n'
    'ITEM_BOLD = re.compile(r"^\\*\\*(\\d{3})\\. ", re.M)      # 新认的那一半，也只当对照用')

# ③ 地板抬到量出来的绝对锚点（原 40 对 162 条无牙）
rep('        self.assertGreater(len(nums), 40, "只数到 %d 条 ⇒ 正则与这份账的形状不一致（今天实测 53）" % len(nums))',
    '        # 地板 150 是**量出来的绝对锚点**（R239：标题形 72 + 粗体形 90 = 162）：\n'
    '        # 正则若退回只认标题形，这里只剩 72 条 ⇒ 不靠"两态对照"也能红。\n'
    '        self.assertGreater(len(nums), 150, "只数到 %d 条 ⇒ 正则与这份账的形状不一致（R239 实测 162 = 72 + 90）" % len(nums))')

# ④ 正对照改成形状感知（挑靶子的规则本身会变 —— D-223 附则一）
rep('''        nums = backlog_items()
        victim, other = nums[-1], nums[-5]
        text = BACKLOG.read_text(encoding="utf-8")
        forged = re.sub(r"^" + other + r"\\. ", victim + ". ", text, count=1, flags=re.M)
        self.assertNotEqual(text, forged, "造重复失败 ⇒ 条目行的形状与正则不一致")''',
    '''        nums = backlog_items()
        victim, other = nums[-1], nums[-5]
        text = BACKLOG.read_text(encoding="utf-8")
        forged = forge_duplicate(text, victim, other)
        self.assertNotEqual(text, forged, "造重复失败 ⇒ 条目行的形状与正则不一致")''')

# ⑤ 追加：形状感知的造重复尺 + 四种形状覆盖格（两态、子集、真台账负格、两形各自被抓住）
t = t.rstrip('\n') + '\n\n\n' + '''# ---------- R239 / BACKLOG 270：条目行的两种形状，各自要能被证伪 ----------
# 为什么现在才加：与 R238 的 DEC_DEF 同族 —— 守卫声称"BACKLOG 编号唯一"，
# 实际只看得见其中一种写法。这一批 `**NNN. ` 条目从 187 一直排到 269，
# 也就是说"最近这一整代条目"都不在那条守卫的覆盖面里。

def forge_duplicate(text, victim, other):
    """把 other 那条改成 victim，**两种形状都要能造**（否则正对照会随台账形状失效）。"""
    for pat, tpl in ((r"^" + other + r"\\. ", victim + ". "),
                     (r"^\\*\\*" + other + "\\. ".replace('\\.', '.'), "**" + victim + ". ")):
        out = re.sub(pat, tpl, text, count=1, flags=re.M)
        if out != text:
            return out
    return text


class BacklogItemShapeTests(unittest.TestCase):
    """②（编号唯一）扩出来的那半：新形状有证人，老形状没被弄坏，两者都能被红。"""

    def test_the_bold_item_shape_is_counted(self):
        text = "**268. 甲一条\\n\\n**269. 乙一条\\n\\n"
        self.assertEqual(["268", "269"], backlog_items(text),
                         "粗体形条目没被数到 ⇒ ITEM 又退回只认标题形了（R238 的 D-223 同族）")

    def test_the_heading_item_shape_is_still_counted(self):
        text = "268. 甲一条\\n\\n269. 乙一条\\n\\n"
        self.assertEqual(["268", "269"], backlog_items(text), "标题形条目不掉 ⇒ 这条不许被新形状挤掉")
        self.assertEqual(["268", "269"], ITEM_HEADING_ONLY.findall(text), "老字面必须还认这种形状")

    def test_real_ledger_bold_items_are_an_extra_set(self):
        text = BACKLOG.read_text(encoding="utf-8")
        head = ITEM_HEADING_ONLY.findall(text)
        bold = ITEM_BOLD.findall(text)
        union = backlog_items(text)
        self.assertGreater(len(bold), 80, "只数到 %d 条粗体形条目 ⇒ 这份账的写法变了，先改这一格" % len(bold))
        self.assertEqual(sorted(head + bold), sorted(union),
                         "并集不等于「标题形 + 粗体形」⇒ 有第三种形状混进来了，或两集有重叠")
        self.assertEqual(set(), set(bold) & set(head), "同一号在两种形状里各写了一遍，先去重再扩守卫")

    def test_forging_a_duplicate_on_either_shape_is_caught(self):
        """两形各自配一格正对照：挑 victim 的规则不依赖"最大号是哪一种形状"。"""
        text = BACKLOG.read_text(encoding="utf-8")
        for shape, finder in ((u'标题形', ITEM_HEADING_ONLY), (u'粗体形', ITEM_BOLD)):
            ids = finder.findall(text)
            self.assertGreater(len(ids), 3, "%s 样本不够，无法造重复" % shape)
            victim, other = ids[0], ids[-1]
            forged = forge_duplicate(text, victim, other)
            self.assertNotEqual(text, forged, "%s 造重复失败 ⇒ forge_duplicate 不认这种形状" % shape)
            after = backlog_items(forged)
            self.assertEqual([victim], sorted({n for n in after if after.count(n) > 1}, key=int),
                             "%s 造出一个重复号而守卫没只抓到它" % shape)
'''
assert t != orig
io.open(G, 'w', encoding='utf-8').write(t)
json.dump({'cells_added': 4, 'anchors': len(hits)}, io.open('/tmp/r239_numbers.json', 'w', encoding='utf-8'))
print('PATCH_R239 写了 %d 处锚点，文件 %d 字符' % (len(hits), len(t)))
