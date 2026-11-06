#!/usr/bin/env python3
"""存档地形普查 —— 直接读 Minecraft 存档 region 文件,离线得出某片区域的地形与占用情况。

用途(不需要开游戏、不需要 bot、不消耗服务器传包):
  - 动大工程(大规模 /fill、铺地基、盖建筑)之前,先离线确认目标区域里有什么:
    地面最高点、水面、地下矿脉,以及**玩家留下的东西**(箱子/告示牌/刷怪笼)。
  - 「可疑方块」一栏就是「非自然方块」,即玩家放置或 mod 结构;真出现箱子之类,
    开填前必须先问过玩家,别把人家仓库埋了(填掉的箱子会连内容一起消失)。

用法:
  python3 16-存档地形普查-库版-mc-census.py <存档目录> <x0> <x1> <z0> <z1> <y0> <y1>

例(查 166×100 城堡占地):
  python3 16-存档地形普查-库版-mc-census.py \
    "/Users/ludwigxu/Library/Application Support/minecraft/saves/呢松的世界-回档前备份-20260818-0916" \
    -732 -564 -348 -246 0 120

注意存档目录要选**正在被游戏写入的那一份**(看 mtime)。

依赖: pip3 install --break-system-packages --user nbtlib==2.0.4 anvil-parser2==0.10.6
region / NBT / 方块调色板那一层已经全部交给库(见 mc_lib.py,格式坑与实测记录都在那)。
本文件只剩普查口径本身。

唯一还需要留意的诊断信号:方块索引 i = (y*16+z)*16+x,**x 在最低 4 位**。
位序若写反,输出会是一片「高度每 16 格在 79/63 之间跳」的棋盘格 —— 自然地形不可能
长这样,见到即知位序反了(见 mc_lib.py 头部坑 3)。
"""
import collections
import sys

from mc_lib import Save, iter_blocks, tile_entities

if len(sys.argv) < 8 or sys.argv[1] in ('-h', '--help'):
    sys.stderr.write('用法: python3 16-存档地形普查-库版-mc-census.py <存档目录> <x0> <x1> <z0> <z1> <y0> <y1>' + '\n')
    sys.exit(2)

W = sys.argv[1]
save = Save(W)

NATURAL = ('grass_block','dirt','stone','cobblestone','andesite','diorite','granite','deepslate',
           'gravel','sand','water','oak_leaves','spruce_leaves','birch_leaves','oak_log','spruce_log',
           'birch_log','short_grass','tall_grass','fern','poppy','dandelion','snow','ice','clay',
           'oak_planks','mossy_cobblestone','coal_ore','iron_ore','copper_ore','gold_ore','redstone_ore',
           'lapis_ore','diamond_ore','tuff','calcite','basalt','smooth_basalt','magma_block','lava',
           'oak_sapling','spruce_sapling','birch_sapling','sugar_cane','pumpkin','melon','moss_carpet',
           'azalea','flowering_azalea','beech_leaves','vine','brown_mushroom','red_mushroom','dead_bush',
           'podzol','coarse_dirt','rooted_dirt','mud','mangrove_roots','muddy_mangrove_roots','lily_pad')
NATURE_PREFIX = ('minecraft:oak_','minecraft:spruce_','minecraft:birch_','minecraft:deepslate_')
NATURE_SUFFIX = ('_leaves','_log','_wood','_sapling','_grass','_ore','_flower','_dirt','_sand','_stone','_bush','_roots')

x0, x1, z0, z1, ylo, yhi = map(int, sys.argv[2:8])
heights = {}
census = collections.Counter()
suspicious = collections.Counter()
sus_pos = {}
bents = []
for cx in range(x0 >> 4, (x1 >> 4) + 1):
    for cz in range(z0 >> 4, (z1 >> 4) + 1):
        chunk = save.chunk(cx, cz)
        if chunk is None:
            continue
        for gx, gy, gz, nm in iter_blocks(chunk):
            if not (x0 <= gx <= x1 and z0 <= gz <= z1 and ylo <= gy <= yhi):
                continue
            census[nm] += 1
            cur = heights.get((gx, gz))
            if cur is None or gy > cur:
                heights[(gx, gz)] = gy
            short = nm.split(':')[-1]
            if (short not in NATURAL and not short.startswith(NATURE_PREFIX)
                    and not any(nm.endswith(sfx) for sfx in NATURE_SUFFIX)):
                suspicious[nm] += 1
                sus_pos.setdefault(nm, (gx, gy, gz))
        for eid, bx, by, bz in tile_entities(chunk):
            if x0 <= bx <= x1 and z0 <= bz <= z1 and ylo <= by <= yhi:
                bents.append((eid, bx, by, bz))

print('=== 占地普查 x[%d,%d] z[%d,%d] y[%d,%d]' % (x0,x1,z0,z1,ylo,yhi))
ys = sorted(heights.values())
if ys:
    print('地面 y: min=%d max=%d 中位=%d 均值=%.1f  采样列 %d' % (ys[0], ys[-1], ys[len(ys)//2], sum(ys)/len(ys), len(ys)))
nat = sum(v for k,v in census.items() if k.split(':')[-1] in NATURAL or any(k.endswith(s) for s in NATURE_SUFFIX))
print('方块总计 %d  其中判定为自然 %d  可疑(非自然) %d' % (sum(census.values()), nat, sum(suspicious.values())))
print('--- 可疑方块 top20:')
for k, v in suspicious.most_common(20):
    print('   %-42s ×%-7d 首见 %s' % (k, v, sus_pos.get(k)))
print('--- 方块实体(箱子/告示牌/刷怪笼等)在占地区内: %d' % len(bents))
for b in bents[:40]:
    print('   %-38s @ %s %s %s' % b)
print('--- 高度分布(每 8 格采样):')
xs = sorted({x for x,_ in heights}); zs = sorted({z for _,z in heights})
print('     ' + ''.join('%5d' % x for x in xs[::8]))
for z in zs[::8]:
    print('%5d ' % z + ''.join(('%5d' % heights[(x,z)]) if (x,z) in heights else '    .' for x in xs[::8]))
