# -*- coding: utf-8 -*-
"""R313 / BACKLOG 367 的正对照夹具：一臂**两根**针，一根活在盘上、一根已经死了。

要钉的就是"漏报"这一件事：
· 旧估计量（`any(候选命中)`）看这一臂 ⇒ 只要有一根还在就报**活的**，rot 不 +1 ⇒ 漏报；
· 新那一箱（表自己声明了 `NEEDLES`）⇒ 逐根判，必须报**恰好一根**死掉。

判据卷（`scripts/tests/test_hidden_arms.py`）给 `scan()` 传**显式 text**（不依赖仓库此刻的盘上内容），
所以这根"活针"永远活、那根"死针"永远死 —— 夹具的期望不随别的表改动而漂。
"""

TARGET = 'scripts/hidden_arms.py'

LIVE_NEEDLE = u"    judged = rot = opaque = 0\n"
DEAD_NEEDLE = u"    judged = rot = opaque = declared_dead = 999\n"

ARMS = [
    ('M997', u'合成：一臂两针、一活一死 ⇒ 只有"逐根判"那一箱会报出来', TARGET,
     [LIVE_NEEDLE, DEAD_NEEDLE], u"", 'test_declared_bin_counts_dead_needles_individually',
     u'已声明死针'),
]

NEEDLES = {
    "M997": [LIVE_NEEDLE, DEAD_NEEDLE],
}
