#!/usr/bin/env python3
"""把「我们加进去、但清除计划没覆盖到」的东西一并收拾掉,顺带修疤。

背景:清单式清除只删了建造计划里登记过的 58,573 格。用 8/18 的老存档当基线逐格比才发现
还有一大坨没登记的东西 —— 最初那版「带支撑」方案留下的石台(3,316 根柱 × 22 层 ≈ 7.3 万格),
以及被上方方块压成泥土的草皮。

三批动作,按顺序:
  ① 石台清除 —— 基线没有、现在实心,且不在保护格。整批都填空气,所以**不按方块名分**,
     全部扔进一个集合一起合并(能并出更大的盒子)。
  ② 疤修补   —— 基线实心、现在空气 = 我们把天然地形删了。按原方块名补回去。
  ③ 草皮还原 —— 基线是草方块、现在是泥土(被上方方块压死)。补回草方块,草会自己接回去。

站点沿用 mc-plan.py 的四象限口径(否则 bot 传过去区块没加载,fill 全成 no-op)。

用法: python3 mc-leftover.py <live存档> <基线存档> <建造计划.jsonl> <输出计划.jsonl> [保护格 x y z]
"""
import json, sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mc_lib import Save, iter_blocks

live_d, base_d, planf, outp = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
protect = tuple(int(v) for v in sys.argv[5:8]) if len(sys.argv) >= 8 else None

# ---- 建造计划的范围与四象限站点(与 mc-plan.py 同一口径)----
xs, zs, ys = [], [], []
for line in open(planf):
    line = line.strip()
    if not line:
        continue
    s = json.loads(line)
    if 'fill' not in s:
        continue
    p = s['fill'].split()
    xs += [int(p[1]), int(p[4])]; ys += [int(p[2]), int(p[5])]; zs += [int(p[3]), int(p[6])]
ox, ex_ = min(xs), max(xs); oz, ez = min(zs), max(zs); by = min(ys)
W = ex_ - ox + 1; L = ez - oz + 1
# 比对面往下多一层:疤就在建筑底面正下方那层(实测 y=72)
y0, y1 = by - 1, max(ys)

cx = ox + W // 2; cz = oz + L // 2
def station(x, z):
    sx = 0 if x < cx else 1
    sz = 0 if z < cz else 1
    return (ox + W // 4 + sx * (W // 2), by + 30, oz + L // 4 + sz * (L // 2))

def read_all(world):
    sv = Save(world); got = {}
    for ccx in range(ox >> 4, (ex_ >> 4) + 1):
        for ccz in range(oz >> 4, (ez >> 4) + 1):
            ch = sv.chunk(ccx, ccz)
            if ch is None:
                continue
            for gx, gy, gz, name in iter_blocks(ch):
                if ox <= gx <= ex_ and y0 <= gy <= y1 and oz <= gz <= ez:
                    got[(gx, gy, gz)] = name
    return got

print('读存档…', flush=True)
liv = read_all(live_d)
base = read_all(base_d)
print('现状 %d 格,基线 %d 格' % (len(liv), len(base)), flush=True)

leftover = [k for k in liv if k not in base and k != protect]
scar = [(k, v) for k, v in base.items() if k not in liv]
grass = [k for k, v in base.items() if v.endswith('grass_block') and liv.get(k, '').endswith('dirt')]
print('① 石台/杂留 %d 格   ② 疤 %d 格   ③ 草皮被压 %d 格' % (len(leftover), len(scar), len(grass)), flush=True)

LIMIT = 32768
def merge(keys):
    """贪心长方体合并(不区分方块名 —— 调用方保证同一批是同一种处理)。"""
    rem = set(keys); boxes = []
    for key in sorted(keys):
        if key not in rem: continue
        x, y, z = key
        x1, y1_, z1, x2, y2_, z2 = x, y, z, x, y, z
        while True:
            best = None; bestn = 0
            for axis in (0, 1, 2):
                if axis == 0:
                    face = [(x2+1, yy, zz) for yy in range(y1_, y2_+1) for zz in range(z1, z2+1)]
                    nb = (x1, y1_, z1, x2+1, y2_, z2)
                elif axis == 1:
                    face = [(xx, y2_+1, zz) for xx in range(x1, x2+1) for zz in range(z1, z2+1)]
                    nb = (x1, y1_, z1, x2, y2_+1, z2)
                else:
                    face = [(xx, yy, z2+1) for xx in range(x1, x2+1) for yy in range(y1_, y2_+1)]
                    nb = (x1, y1_, z1, x2, y2_, z2+1)
                if len(face) > bestn and all(p in rem for p in face):
                    bestn = len(face); best = nb
            if best is None: break
            x1, y1_, z1, x2, y2_, z2 = best
        for xx in range(x1, x2+1):
            for yy in range(y1_, y2_+1):
                for zz in range(z1, z2+1):
                    rem.discard((xx, yy, zz))
        boxes.append((x1, y1_, z1, x2, y2_, z2))
    return boxes

def split_box(b):
    x1, y1_, z1, x2, y2_, z2 = b
    out = [b]; res = []
    while out:
        x1, y1_, z1, x2, y2_, z2 = out.pop()
        vol = (x2-x1+1) * (y2_-y1_+1) * (z2-z1+1)
        if vol <= LIMIT:
            res.append((x1, y1_, z1, x2, y2_, z2)); continue
        dims = sorted([(x2-x1+1, 0), (y2_-y1_+1, 1), (z2-z1+1, 2)], reverse=True)
        ax = dims[0][1]
        if ax == 0:
            mid = (x1+x2)//2
            out.append((x1, y1_, z1, mid, y2_, z2)); out.append((mid+1, y1_, z1, x2, y2_, z2))
        elif ax == 1:
            mid = (y1_+y2_)//2
            out.append((x1, y1_, z1, x2, mid, z2)); out.append((x1, mid+1, z1, x2, y2_, z2))
        else:
            mid = (z1+z2)//2
            out.append((x1, y1_, z1, x2, y2_, mid)); out.append((x1, y1_, mid+1, x2, y2_, z2))
    return res

groups = [('石台清除', leftover, 'minecraft:air')]
by_state = collections.defaultdict(list)
for k, v in scar:
    by_state[v].append(k)
for v, ks in sorted(by_state.items()):
    groups.append(('疤修补', ks, v))
if grass:
    groups.append(('草皮还原', grass, 'minecraft:grass_block'))

plan = []
total_fill = 0
for phase, keys, state in groups:
    boxes = merge(set(keys))
    cmds = []
    for b in boxes:
        for (a, b2, c, d, e, f) in split_box(b):
            cmds.append('fill %d %d %d %d %d %d %s' % (a, b2, c, d, e, f, state))
    g = collections.defaultdict(list)
    for c in cmds:
        p = c.split()
        g[station(int(p[1]), int(p[3]))].append(c)
    for st, lst in sorted(g.items()):
        plan.append({'tp': list(st), 'phase': phase, 'n': len(lst)})
        for c in lst:
            plan.append({'fill': c})
    total_fill += len(cmds)
    print('%s: %d 格 → %d 个盒子 → %d 条指令' % (phase, len(keys), len(boxes), len(cmds)), flush=True)

with open(outp, 'w') as f:
    for step in plan:
        f.write(json.dumps(step) + '\n')
print('计划已写 %s: %d 条 fill,%d 个 tp' % (outp, total_fill, sum(1 for s in plan if 'tp' in s)))
if protect:
    print('保护格 %s 在石台集合内:%s(已排除)' % (protect, protect in liv))
