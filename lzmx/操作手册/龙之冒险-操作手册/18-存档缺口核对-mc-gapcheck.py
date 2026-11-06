#!/usr/bin/env python3
"""穷尽核对:计划里每一格期望的方块,存档里在不在。

聊天探针只能抽样,58,573 格探不完。存档是权威结果 —— 直接读 region 逐格比。
只比「方块名」(不带 Properties):要抓的是「该有方块的地方是空气」,
状态串(facing/axis)的比对留作第二步。

用法: python3 mc-gapcheck.py <计划.jsonl> <存档目录> [输出补漏指令文件]
"""
import json, sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mc_lib import Save, iter_blocks

plan, world = sys.argv[1], sys.argv[2]
outp = sys.argv[3] if len(sys.argv) > 3 else '/tmp/gap-refill.txt'

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
    st = p[7]
    for x in range(x1, x2 + 1):
        for y in range(y1, y2 + 1):
            for z in range(z1, z2 + 1):
                exp[(x, y, z)] = st
print('计划格数 %d' % len(exp))

x0 = min(k[0] for k in exp); x1 = max(k[0] for k in exp)
y0 = min(k[1] for k in exp); y1 = max(k[1] for k in exp)
z0 = min(k[2] for k in exp); z1 = max(k[2] for k in exp)
print('范围 x[%d..%d] y[%d..%d] z[%d..%d]' % (x0, x1, y0, y1, z0, z1))

sv = Save(world)
actual = {}
nchunk = 0
for cx in range(x0 >> 4, (x1 >> 4) + 1):
    for cz in range(z0 >> 4, (z1 >> 4) + 1):
        ch = sv.chunk(cx, cz)
        if ch is None:
            continue
        nchunk += 1
        for gx, gy, gz, name in iter_blocks(ch):
            if x0 <= gx <= x1 and y0 <= gy <= y1 and z0 <= gz <= z1:
                actual[(gx, gy, gz)] = name

missing = []
namebad = []
for k, want in exp.items():
    wantname = want.split('[')[0]
    got = actual.get(k, 'minecraft:air')
    if got.endswith('air'):
        missing.append((k, want))
    elif got != wantname:
        namebad.append((k, want, got))

print('读入区块 %d,存档内该范围内非空气格 %d' % (nchunk, len(actual)))
print('缺失(计划要有、实际空气) %d 格' % len(missing))
print('方块名不符 %d 格' % len(namebad))
for k, want, got in namebad[:10]:
    print('   %s 期望 %s 实际 %s' % (k, want, got))

cells = collections.defaultdict(set)
for k, want in missing:
    cells[want].add(k)
out = []
for want, cs in cells.items():
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
print('补漏指令 %d 条 → %s' % (len(out), outp))
