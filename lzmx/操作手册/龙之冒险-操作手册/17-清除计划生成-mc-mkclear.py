#!/usr/bin/env python3
"""由建造计划生成「清除计划」:把当初每一条 fill 反成填空气。

只清我们放过的格子,不碰天然地形。唯一例外是玩家那口 dirt_chest(-646,73,-310),
它必须从清除范围里挖掉 —— 填空气会连箱子带内容一起没。

本脚本**只写文件,不发指令**。写完自动做恒等核对:
    清除覆盖的格子集合 == 建造放的格子集合 − {箱子那一格}
多一格或少一格都会报出来。核对通过再用 mc-drive 投喂。

用法: python3 mc-mkclear.py <建造计划.jsonl> <输出清除计划.jsonl> [保护格 x y z]
"""
import json
import sys
import collections

src, dst = sys.argv[1], sys.argv[2]
protect = None
if len(sys.argv) >= 6:
    protect = (int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]))


def split_out(a, b, c, d, e, f, ex):
    """把长方体 [a..d]×[b..e]×[c..f] 拆成**互不重叠**的若干块,去掉 ex 那一格。

    分解方式:先把 x=cx 那一层单独切出来,再把该层按 z 切,再把剩下的 z=cz 那条按 y 切。
    三段式切开后各块天然不相交 —— 这一点很容易写错:如果对 x/y/z 三方向各自
    相对原长方体取「左/右」六块,这六块是互相重叠的(左右两块都包含上下区域),
    结果是同一格被清好几遍。核对里「清除格数 > 建造格数」就是这个错的指纹。
    """
    cx, cy, cz = ex
    if not (a <= cx <= d and b <= cy <= e and c <= cz <= f):
        return [(a, b, c, d, e, f)]
    out = []
    if a <= cx - 1:
        out.append((a, b, c, cx - 1, e, f))
    if cx + 1 <= d:
        out.append((cx + 1, b, c, d, e, f))
    if c <= cz - 1:
        out.append((cx, b, c, cx, e, cz - 1))
    if cz + 1 <= f:
        out.append((cx, b, cz + 1, cx, e, f))
    if b <= cy - 1:
        out.append((cx, b, cz, cx, cy - 1, cz))
    if cy + 1 <= e:
        out.append((cx, cy + 1, cz, cx, e, cz))
    return out


def cells_of(step_list, key):
    """计划里所有 fill 覆盖的格子集合。"""
    out = set()
    for s in step_list:
        if key not in s:
            continue
        p = s[key].split()
        a, b, c, d, e, f = (int(v) for v in p[1:7])
        for x in range(a, d + 1):
            for y in range(b, e + 1):
                for z in range(c, f + 1):
                    out.add((x, y, z))
    return out


steps = [json.loads(l) for l in open(src) if l.strip()]
plan = []
n = 0
for s in steps:
    if 'tp' in s:
        plan.append(s)
        continue
    p = s['fill'].split()
    a, b, c, d, e, f = (int(v) for v in p[1:7])
    for (a2, b2, c2, d2, e2, f2) in (split_out(a, b, c, d, e, f, protect) if protect else [(a, b, c, d, e, f)]):
        plan.append({'fill': 'fill %d %d %d %d %d %d minecraft:air' % (a2, b2, c2, d2, e2, f2)})
        n += 1

with open(dst, 'w') as fh:
    for s in plan:
        fh.write(json.dumps(s) + '\n')

# ---------------- 恒等核对 ----------------
built = cells_of(steps, 'fill')
clear = cells_of(plan, 'fill')
want = built - ({protect} if protect else set())

print('建造计划: %d 条 fill,覆盖 %d 格' % (sum(1 for s in steps if 'fill' in s), len(built)))
print('清除计划: %d 条 fill,覆盖 %d 格(%d 个站点)' % (
    n, len(clear), sum(1 for s in plan if 'tp' in s)))
print('应为 = 建造格 − 保护格 = %d 格' % len(want))

extra = clear - want
lost = want - clear
print('多余(清到不该清的) %d 格' % len(extra))
for k in sorted(extra)[:10]:
    print('   多余 %s' % (k,))
print('漏掉(该清没清) %d 格' % len(lost))
for k in sorted(lost)[:10]:
    print('   漏掉 %s' % (k,))
if protect:
    print('保护格 %s 是否被清:%s' % (protect, '否(正确)' if protect not in clear else '是(错误!)'))
    print('保护格 %s 是否在建造覆盖内:%s' % (protect, '是' if protect in built else '否(箱子本来就不在任何 fill 盒子里)'))
print('结论: %s' % ('恒等,可执行' if not extra and not lost else '不一致,禁止执行'))
