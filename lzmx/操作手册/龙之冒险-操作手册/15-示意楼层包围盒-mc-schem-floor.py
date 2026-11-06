#!/usr/bin/env python3
"""schematic 楼层包围盒统计 —— y=22/23 那两层(主楼地坪)铺到哪,以及逐列最低方块分布。

用法:
  python3 15-示意楼层包围盒-mc-schem-floor.py [schematic]        # 不给就用下面的默认路径

⚠️ 默认路径是 /tmp/chateau2.schematic —— **在 /tmp 里,跨会话/重启可能已被清掉**。
   换会话后先 `ls -l /tmp/chateau2.schematic` 确认还在,不在就显式把路径传进来。
   (默认值没改,是为了不动已验证的行为;要长期用建议把 schematic 放到固定位置。)

「keep 区」的 x18..136 / z0..44 是当年定的裁剪窗,为了把院墙那圈装饰腰线排除在外。

依赖: pip3 install --break-system-packages --user nbtlib==2.0.4 anvil-parser2==0.10.6
      解析层见 mc_lib.py(旧版这里是从 schem2fill.py 里 exec 出解析器来蹭的,已去掉)。
"""
import collections
import sys

from mc_lib import load_schematic, schematic_cells

if sys.argv[1:2] in (['-h'], ['--help']):
    sys.stderr.write('用法: python3 15-示意楼层包围盒-mc-schem-floor.py [schematic]   # 不给就用 /tmp/chateau2.schematic' + '\n')
    sys.exit(2)
P = sys.argv[1] if len(sys.argv) > 1 else '/tmp/chateau2.schematic'
root = load_schematic(P)

W, H, L = int(root['Width']), int(root['Height']), int(root['Length'])

FLOOR_SY = (22, 23)
layer = {y: [] for y in FLOOR_SY}      # y -> [(x, z)] 非空
lo = {}                                # (x, z) -> 最低非空方块的示意 y
for (x, y, z), bid, meta in schematic_cells(root):
    if bid == 0:
        continue
    if (x, z) not in lo:               # 生成顺序是 y 递增 ⇒ 首次见到即为最低
        lo[(x, z)] = y
    if y in layer:
        layer[y].append((x, z))

for y in FLOOR_SY:
    xs = [p[0] for p in layer[y]]; zs = [p[1] for p in layer[y]]
    print('层 y=%d: %d 块   x[%d..%d]  z[%d..%d]' % (y, len(xs), min(xs), max(xs), min(zs), max(zs)))

# 逐列最低建筑方块(示意 y),只统计 x20..134、z0..43 的 keep 区
xs = [p[0] for p in lo]; zs = [p[1] for p in lo]
print('\n整个建筑最低方块覆盖: x[%d..%d] z[%d..%d] 列数 %d' % (min(xs), max(xs), min(zs), max(zs), len(lo)))

sub = {p: v for p, v in lo.items() if 18 <= p[0] <= 136 and 0 <= p[1] <= 44}
vals = sorted(sub.values())
print('keep 区(x18..136,z0..44) 列数 %d, 最低 y 分布:' % len(sub))
for k, v in sorted(collections.Counter(vals).items()):
    print('   y=%-3d %5d' % (k, v))
xs2 = [p[0] for p in sub]; zs2 = [p[1] for p in sub]
print('keep 区 bbox: x[%d..%d] z[%d..%d]' % (min(xs2), max(xs2), min(zs2), max(zs2)))
