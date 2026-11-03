# -*- coding: utf-8 -*-
"""项目记忆索引瘦身：R565/R566 两行压成一行短钩，并插入 R565 补全那一行（详细账在各自 topic 文件里）。"""
import io

PATH = u'/Users/wangziyi/.qoder-cn/projects/-Users-wangziyi-Codex-Project0/memory/MEMORY.md'
with io.open(PATH, encoding='utf-8') as handle:
    lines = handle.read().split('\n')

r566 = [i for i, l in enumerate(lines) if l.startswith(u'- [R566（2026-11-04）]')]
r565 = [i for i, l in enumerate(lines) if l.startswith(u'- [R565（2026-11-03）]')]
assert len(r566) == 1 and len(r565) == 1 and r566[0] < r565[0], (r566, r565)

new_line = (u'- [R565 补全（2026-11-04）](target-mode-status-2026-11-04-r565-buquan.md) — '
            u'**以此为准（`HEAD=origin/main=b3dca77`、ahead=0；三跑 `41708860764`/`41708303631`/`41704430816` 全 in_progress ⇒ 复核未到）**：'
            u'四格 ⓪ 读数到手、639 结掉"复核未到"（runner 1x 判到 3.84:1、三跑逐字同值、口径仍归用户）、'
            u'STEP[15]/[19] 同一朵 ⇒ 新开 643、STEP[11] 绿≠帧没变、三处改账（含 D-565 节内 ⑤⑥⑦ 撞号重编成 ①…⑩）、刀仍 M1476 起、禁碰 12 面')

lines[r566[0]] = (u'- [R566（2026-11-04）](target-mode-status-2026-11-04-r566.md) — 旧状态（已收口并推齐：'
                  u'`HEAD=origin/main=f538d2c`、ahead=0，后被 R565 补全两笔接上）：产品 0 文件 + 判据 1 格（现读真钥匙串）+ 刀 M1474/M1475；'
                  u'签名链 `SIGNATURE_KIND=local` 两跑 + 跨轮 `codesign -dvv` 逐字对拍；折叠规格 `docs/FOLD_DUO_SPEC_2026-11-03.md` 进仓；新开 642（安装条目 433→451）')

lines[r565[0]] = (u'- [R565（2026-11-03）](target-mode-status-2026-11-03-r565.md) — 旧状态（已收口并推齐，共 11 笔；'
                  u'产品 1 文件 = 浮层键盘提示颜色 tertiary→secondary，判据/守卫 3 支、刀 M1466–M1473、新开 638/639/640/641；'
                  u'补段把 STEP[9] 的绝对根扫干净并收成 `ci_channel_hygiene.py`；`HINT_CONTRAST` 的 runner 红排掉倍率后落在名义 vs 渲染两口径 ⇒ 639 归用户）')

lines.insert(r566[0], new_line)

with io.open(PATH, 'w', encoding='utf-8') as handle:
    handle.write('\n'.join(lines))
print('index updated; bytes=%d' % len('\n'.join(lines).encode('utf-8')))
