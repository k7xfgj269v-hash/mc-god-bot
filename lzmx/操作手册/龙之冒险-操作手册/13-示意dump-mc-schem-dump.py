#!/usr/bin/env python3
"""schematic 结构 dump —— 打印一个 MCEdit .schematic 的尺寸、顶层键、方块直方图与竖直分层。

用法:
  python3 13-示意dump-mc-schem-dump.py [schematic]        # 不给就用下面的默认路径

⚠️ 默认路径是 /tmp/chateau2.schematic —— **在 /tmp 里,跨会话/重启可能已被清掉**。
   换会话后先 `ls -l /tmp/chateau2.schematic` 确认还在,不在就显式把路径传进来。
   (默认值没改,是为了不动已验证的行为;要长期用建议把 schematic 放到固定位置。)

「竖直分层:非空方块数」一栏是找地坪用的:某一层方块数突然掉下来,那一层往往就是楼板。

依赖: pip3 install --break-system-packages --user nbtlib==2.0.4 anvil-parser2==0.10.6
      .schematic = gzip 过的 NBT,由 nbtlib 读;AddBlocks 半字节解包在 mc_lib 里统一处理。
"""
import collections
import sys

from mc_lib import load_schematic, schematic_cells

if sys.argv[1:2] in (['-h'], ['--help']):
    sys.stderr.write('用法: python3 13-示意dump-mc-schem-dump.py [schematic]   # 不给就用 /tmp/chateau2.schematic' + '\n')
    sys.exit(2)
P = sys.argv[1] if len(sys.argv) > 1 else '/tmp/chateau2.schematic'
root = load_schematic(P)

W, H, L = int(root['Width']), int(root['Height']), int(root['Length'])
print('尺寸 W×H×L = %d × %d × %d  Materials=%s' % (W, H, L, root.get('Materials')))
print('顶层键:', sorted(root.keys()))

cnt = collections.Counter()
per_y = collections.Counter()
for (x, y, z), bid, meta in schematic_cells(root):
    cnt[(bid, meta)] += 1
    if bid:
        per_y[y] += 1

print('\n总计 %d 方块, 不同 (id,meta) %d 种' % (sum(cnt.values()), len(cnt)))
for (bid, m), c in sorted(cnt.items(), key=lambda kv: -kv[1]):
    print('  id=%-5d meta=%-3d  ×%-7d' % (bid, m, c))

# 竖直剖面:每层非空方块数,看哪一层是地坪
print('\n竖直分层(y=0 为最底层):非空方块数')
for y in range(H):
    c = per_y[y]
    print('  y=%-3d %6d %s' % (y, c, '#' * min(60, c // 120)))
