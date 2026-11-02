# -*- coding: utf-8 -*-
import io

p = 'AGENT_BACKLOG.md'
s = io.open(p, encoding='utf-8').read()

old569 = u'星标尺寸本轮**没再动**（禁碰第 ⑥ 面）。runner 那一格的结论见 `AGENT_STATE.md` 的 R555 节 ⑤。'
assert s.count(old569) == 1
new569 = (u'星标尺寸本轮**没再动**（禁碰第 ⑥ 面）。\n'
          u'    runner 签收（R555，`41431129208 ↔ 5a943e7`）：该步自己打的结论行 = `CAPTURE_GATE_RESULT=ok 红=0`'
          u'（连挂四轮的收藏星红在这一格消失），1x 现读 `QUICKPICK_STAR_HEIGHT light 7.0pt 星墨=29 / dark 6.0pt 星墨=23`、'
          u'`QUICKPICK_STAR_FULLROWS light 整行=7 / dark 整行=6` ⇒ 两档都在 6.0 界内，**dark 恰在界上、余量 0**；'
          u'`QUICKPICK_STAR_SPAN_NOT_JUDGED=1x-lattice-has-no-half-row` 亮/暗各一行（具名不判，不是沉默）。'
          u'**569 的 runner 半格结案**；单内保留这一格监控：谁再把星缩小，dark 那一档立刻红（余量 0 是刻意的，不是巧合）。')
s = s.replace(old569, new569, 1)

old616 = (u'    修法：把 `(\\S+?)` 改成 `(.+?)`，并在合成正对照里加一条「中段带空格」的样本（配刀）；'
          u'在那之前按既有出口把 `3ebc7fc` 登记进 `UNPARSED_ROSTER`（退场条件见名单）。')
assert s.count(old616) == 1
new616 = (old616 + u'\n'
          u'    签收（R555）：本轮自己的两笔 subject（`6b70474` / `5a943e7`，中段带「 + 」）被旧尺读成 '
          u'`K_WITHOUT_ROUND_IDENTITY` ⇒ runner STEP[9] 红。按本条写好的退场条件修尺：`SUBJECT` 中段改 `(.+?)`、'
          u'合成正对照新增 `eeee555`（中段带空格，断言它必须被认出轮次与 K），刀 **M1439**（退回 `(\\S+?)` 即红）CAUGHT，'
          u'并按退场条件删掉 `3ebc7fc` / `f85aa21` 两条豁免（`fb2cea0` 的退场条件是"扫描窗滑过"，与本法无关，保留）。'
          u'已推的两笔标题不改（禁 amend）。**616 结案**（修法两支都落地了）。')
s = s.replace(old616, new616, 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('backlog patched')
