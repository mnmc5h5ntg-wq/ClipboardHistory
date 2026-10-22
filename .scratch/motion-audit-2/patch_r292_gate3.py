# -*- coding: utf-8 -*-
"""R292 生成器补丁 v3：把"就地更正"从**做字符串手术**换成**验结果**。

为什么换：更正本身已经落盘（按起止片段匹配，四个文件各命中 1 次），而生成器里那份 NEW 文本与盘上文本
差着几个字符（我后来把内嵌的反引号正则改成了中文描述）。继续让生成器去做替换，只会因为一个标点不同而
在"改过了"与"没改过"之间误判 —— 这正是 R100 那一课（编辑台账"插入"实为替换）的第三种形态。
所以：生成器只准检查，不准再动手。
"""
import ast
import io

P = '.scratch/motion-audit-2/ledgers_r292.py'
s = io.open(P, encoding='utf-8').read()

start = s.index(u'# ── 就地更正 R291 那四格假话')
end = s.index(u'for o, n, name, allow in')
block = s[start:end]
assert u'correct_in_section' in block

new_block = u'''# ── 验结果：R291 那格假话必须已经从四本账里消失，更正痕迹必须各在 1 处 ──
# 更正本身是上一笔手工落的（按起止片段匹配，四个文件各命中一次）。生成器不再做字符串手术：
# 它只准检查，改不动也不许假装改过。
CLAIM = u"差的那一颗**没有名字**"
MARK = u"R292 就地更正"
CHECKS = ((u"UI", lambda: ui_new), (u"ITERATION", lambda: it_new),
          (u"STATE", lambda: st_new), (u"CHANGELOG", lambda: cg_new))
for _nm, _get in CHECKS:
    _t = _get()
    if CLAIM in _t:
        die(_nm + u" 里那句电池假话还在盘上 ⇒ 撤回没落到它头上")
    if _t.count(MARK) < 1:
        die(_nm + u" 里没有「" + MARK + u"」的痕迹 ⇒ 更正不可复查（不许只把假话删掉不留痕）")
print(u"R291 四格更正复查通过：假话残留 0 处、痕迹各在位")


'''
s = s[:start] + new_block + s[end:]
# must_preserve 的 allow 归零：生成器不再改写任何历史行
s = s.replace(u'((ui_old, ui_new, "UI", 1), (cg_old, cg_new, "CHANGELOG", 1),', u'((ui_old, ui_new, "UI", 0), (cg_old, cg_new, "CHANGELOG", 0),')
s = s.replace(u'(bk_old, bk_new, "BACKLOG", 0), (st_old, st_new, "STATE", 1),', u'(bk_old, bk_new, "BACKLOG", 0), (st_old, st_new, "STATE", 0),')
s = s.replace(u'(it_old, it_new, "ITERATION", 1), (dc_old, dc_new, "DECISIONS", 0)):', u'(it_old, it_new, "ITERATION", 0), (dc_old, dc_new, "DECISIONS", 0)):')
ast.parse(s)
io.open(P, 'w', encoding='utf-8').write(s)
print('PATCH_V3_OK')
