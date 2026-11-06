#!/usr/bin/env python3
"""清除之后,拿「建城前的老存档」当基线,逐格比出我们到底改动了天然地形的哪些格。

为什么需要它:清单式清除只能删掉「我们放过的格子」,删完留下的是空气 —— 如果那一格
本来就有天然地形(我们在原地表之上盖、或替换过地表),空气就顶替了原地形,那就是疤。
没有建城前快照时只能猜;这里发现 saves/呢松的世界 冻结在 8 月 18 日,比建城早近一个月,
所以它可以当基线(前提:该区域在 8/18 之后没有人另行动土,输出里会把可疑的挑出来)。

三类差异:
  A 基线实心 → 现在空气   = 我们毁掉的地形(疤)。这是要修的。
  B 基线空气 → 现在实心   = 8/18 之后新出现的东西(清除没清干净的、玩家新盖的、草长出来的)
  C 两边都实心但方块名不同 = 被替换过

用法: python3 mc-scarcheck.py <live存档> <基线存档> <建造计划.jsonl> [输出修补指令]
"""
import json, sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mc_lib import Save, iter_blocks

live_d, base_d, plan = sys.argv[1], sys.argv[2], sys.argv[3]
outp = sys.argv[4] if len(sys.argv) > 4 else '/tmp/scar-restore.txt'

exp = {}
for line in open(plan):
    line = line.strip()
    if not line:
        continue
    s = json.loads(line)
    if 'fill' not in s:
        continue
    p = s['fill'].split()
    x1, y1, z1, x2, y2, z2 = (int(v) for v in p[1:7])
    for x in range(x1, x2 + 1):
        for y in range(y1, y2 + 1):
            for z in range(z1, z2 + 1):
                exp[(x, y, z)] = 1

x0 = min(k[0] for k in exp); x1 = max(k[0] for k in exp)
y0 = min(k[1] for k in exp); y1 = max(k[1] for k in exp)
z0 = min(k[2] for k in exp); z1 = max(k[2] for k in exp)
print('比对面 x[%d..%d] y[%d..%d] z[%d..%d],计划格 %d' % (x0, x1, y0, y1, z0, z1, len(exp)))


def read_all(world):
    """把 bbox 内所有非空气格读成 dict。用迭代顺序初始化,保证两边 key 口径一致。"""
    sv = Save(world)
    got = {}
    for cx in range(x0 >> 4, (x1 >> 4) + 1):
        for cz in range(z0 >> 4, (z1 >> 4) + 1):
            ch = sv.chunk(cx, cz)
            if ch is None:
                continue
            for gx, gy, gz, name in iter_blocks(ch):
                if x0 <= gx <= x1 and y0 <= gy <= y1 and z0 <= gz <= z1:
                    got[(gx, gy, gz)] = name
    return got


# 注意:y 下限取计划下限-1,因为「毁掉的地形」可能正好在计划层之下
y0 = y0 - 1
A = Save(live_d)
base = read_all(base_d)
liv = read_all(live_d)
print('基线非空气格 %d,现状非空气格 %d' % (len(base), len(liv)))

air = []
for k, v in base.items():
    if k not in liv:
        air.append((k, v))
B = [(k, v) for k, v in liv.items() if k not in base]
C = [(k, base[k], v) for k, v in liv.items() if k in base and base[k] != v]

print('A 基线实心→现在空气(疤) %d 格' % len(air))
for k, v in sorted(air)[:15]:
    print('   %s 原本 %s' % (k, v))
print('B 基线空气→现在实心 %d 格' % len(B))
for k, v in sorted(B)[:15]:
    print('   %s 现在 %s' % (k, v))
print('C 实心但被换过 %d 格' % len(C))
for k, b, v in sorted(C)[:15]:
    print('   %s %s → %s' % (k, b, v))

# 计划格里现在还是空气的有多少(清除是否真生效)
print('计划格中现在仍是实心的 %d 格' % sum(1 for k in exp if k in liv))

# 按方块名统计疤,并把 A 合并成 fill 指令(同种方块贪心并块)
by = collections.defaultdict(set)
for k, v in air:
    by[v].add(k)
out = []
for want, cs in by.items():
    rem = set(cs)
    for key in sorted(cs):
        if key not in rem:
            continue
        x, y, z = key
        a, b, c, d, e, f = x, y, z, x, y, z
        while True:
            best = None; bestn = 0
            for axis in (0, 1, 2):
                if axis == 0:
                    face = [(d + 1, yy, zz) for yy in range(b, e + 1) for zz in range(c, f + 1)]
                    nb = (a, b, c, d + 1, e, f)
                elif axis == 1:
                    face = [(xx, e + 1, zz) for xx in range(a, d + 1) for zz in range(c, f + 1)]
                    nb = (a, b, c, d, e + 1, f)
                else:
                    face = [(xx, yy, f + 1) for xx in range(a, d + 1) for yy in range(b, e + 1)]
                    nb = (a, b, c, d, e, f + 1)
                if len(face) > bestn and all(p in rem for p in face):
                    bestn = len(face); best = nb
            if best is None:
                break
            a, b, c, d, e, f = best
        for xx in range(a, d + 1):
            for yy in range(b, e + 1):
                for zz in range(c, f + 1):
                    rem.discard((xx, yy, zz))
        out.append('fill %d %d %d %d %d %d %s' % (a, b, c, d, e, f, want))
with open(outp, 'w') as f:
    for c in out:
        f.write(c + '\n')
print('疤修补指令 %d 条 → %s' % (len(out), outp))
print('疤按方块名:%s' % dict(sorted(((k, len(v)) for k, v in by.items()), key=lambda t: -t[1])))
