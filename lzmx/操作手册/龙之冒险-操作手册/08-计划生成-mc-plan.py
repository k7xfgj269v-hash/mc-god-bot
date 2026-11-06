#!/usr/bin/env python3
"""把 MCEdit .schematic 转成一批 /fill 指令(贪心长方体合并),并生成支撑填充。

用法:
  python3 08-计划生成-mc-plan.py <schematic> <存档目录> <x0> <z0> <base_y> <输出计划> [--no-support]

x0/z0 = 建筑 x=0/z=0 落在世界里的坐标; base_y = 建筑 y=0 落在世界里的 y。
输出 = /tmp/fill-plan.jsonl,每行 {"tp":[x,y,z]} 或 {"fill":"fill ..."}。

分工:本脚本只**离线算**(读 schematic + 读存档算列顶高度),一条指令都不发;
投喂给 bot 是 09-投喂驱动-mc-drive.py 的事(它负责 tp、分批、核对回执)。

依赖: pip3 install --break-system-packages --user nbtlib==2.0.4 anvil-parser2==0.10.6
      解析层(含格式坑与实测记录)见 mc_lib.py。

关于 --no-support(**两件事别混成一件**):支撑填充默认是**开**的,关掉它只有一个途径 ——
命令行显式加 --no-support。生产那份 /tmp/fill-plan.jsonl 就是**显式关了**的:用户要求只放
建筑文件自身的方块、不许自造地形,所以主动关的。

但要注意:在本锚点(-732 -347 73)上,就算**不关**,落地也同样是 0 个支撑方块 ——
实测打印「建筑方块 58573,支撑列 0(地基 0 + 土台 3316),支撑方块 0」,即选中了 3,316 个
土台候选列(3,317 减掉 PROTECT 那 1 列),却一块都没生成。逐列量过原因:这些列的**天然
地面顶已经全在 y≥94**(实测 48 列在 94、882 列在 95、1969 列在 96…),而补土上界
MOUND_TOP = by+22-1 = 94,于是下界 `start = max(by, 列顶+1)` 恒大于上界,range 为空。
原因是这座城堡**在这个存档里本来就建好了**,楼板直接坐在天然地面上,没有要补的土。
所以「生产计划里没有支撑 phase」在这份计划上**两种解释都成立**且结果相同:人是关掉了它,
同时这个场地也确实没东西可补。**别据此得出「支撑逻辑不产出」的结论** —— 换个还没建好的
场地(或山坡原始地形)就会真的产出方块。要验证支撑真的干活,得拿一份未建成的场地跑。

两条硬约束:
  - Minecraft /fill 单条上限 32768 格,split_box() 就是为此把超大的盒子对半切。
    改 LIMIT 或改切分方向,都会让驱动侧「fill ↔ 服务端回执」的顺序配对错位。
  - 每个站点(tp)之后的区块是**异步加载**的:tp 落地 ≠ 区块可写。驱动侧必须在
    发该站点的 fill 之前留观察窗(09-投喂驱动-mc-drive.py 里是 sleep(4)),否则站点边缘的
    区块会成片静默返回 "No blocks were filled"。
"""
import collections
import json
import sys

from mc_lib import Save, load_schematic, schematic_cells

# ============ 传统数字 ID → 现代方块状态 ============
STAIR_FACING = {0: 'east', 1: 'west', 2: 'south', 3: 'north'}
TRAP_FACING  = {0: 'south', 1: 'north', 2: 'east', 3: 'west'}
FLOWER = {0: 'poppy', 3: 'azure_bluet', 4: 'red_tulip', 5: 'orange_tulip',
          6: 'white_tulip', 7: 'pink_tulip', 8: 'oxeye_daisy'}

def modern(bid, m):
    if bid == 5:   return 'minecraft:spruce_planks'
    if bid == 1:   return 'minecraft:stone'
    if bid == 4:   return 'minecraft:cobblestone'
    if bid == 2:   return 'minecraft:grass_block'
    if bid == 3:   return 'minecraft:dirt'
    if bid == 21:  return 'minecraft:lapis_ore'
    if bid == 89:  return 'minecraft:glowstone'
    if bid == 102: return 'minecraft:glass_pane'
    if bid == 188: return 'minecraft:spruce_fence'
    if bid == 139: return 'minecraft:cobblestone_wall'
    if bid == 31:  return 'minecraft:grass'            # 1.20.1 里短草就叫 grass
    if bid == 37:  return 'minecraft:dandelion'
    if bid == 18:  return 'minecraft:oak_leaves[persistent=true]'   # 防落叶
    if bid == 38:  return 'minecraft:' + FLOWER.get(m & 7, 'poppy')
    if bid == 17:
        wood = 'spruce' if (m & 3) == 1 else 'oak'
        axis = 'y' if (m & 12) == 0 else ('x' if (m & 4) else 'z')
        return 'minecraft:%s_log[axis=%s]' % (wood, axis)
    if bid == 126:                                       # 木台阶
        return 'minecraft:spruce_slab[type=%s]' % ('top' if (m & 8) else 'bottom')
    if bid == 134:                                       # 云杉楼梯
        return 'minecraft:spruce_stairs[facing=%s,half=%s]' % (
            STAIR_FACING.get(m & 3, 'north'), 'top' if (m & 4) else 'bottom')
    if bid == 67:                                        # 石楼梯
        return 'minecraft:stone_stairs[facing=%s,half=%s]' % (
            STAIR_FACING.get(m & 3, 'north'), 'top' if (m & 4) else 'bottom')
    if bid == 96:                                        # 橡木活板门
        return 'minecraft:oak_trapdoor[facing=%s,half=%s,open=%s,powered=false]' % (
            TRAP_FACING.get(m & 3, 'south'), 'top' if (m & 8) else 'bottom',
            'true' if (m & 4) else 'false')
    return None

# ============ 贪心长方体合并 ============
def merge(cells):
    """贪心长方体合并:每次在 x/y/z 三个方向里挑「新增面最大」的方向扩,直到扩不动。"""
    rem = dict(cells); boxes = []
    for key in sorted(cells):
        if key not in rem: continue
        x, y, z = key; st = cells[key]
        x1, y1, z1, x2, y2, z2 = x, y, z, x, y, z
        while True:
            best = None; bestn = 0
            for axis in (0, 1, 2):
                if axis == 0:
                    face = [(x2+1, yy, zz) for yy in range(y1, y2+1) for zz in range(z1, z2+1)]
                    nb = (x1, y1, z1, x2+1, y2, z2)
                elif axis == 1:
                    face = [(xx, y2+1, zz) for xx in range(x1, x2+1) for zz in range(z1, z2+1)]
                    nb = (x1, y1, z1, x2, y2+1, z2)
                else:
                    face = [(xx, yy, z2+1) for xx in range(x1, x2+1) for yy in range(y1, y2+1)]
                    nb = (x1, y1, z1, x2, y2, z2+1)
                if len(face) > bestn and all(rem.get(p) == st for p in face):
                    bestn = len(face); best = nb
            if best is None: break
            x1, y1, z1, x2, y2, z2 = best
        for xx in range(x1, x2+1):
            for yy in range(y1, y2+1):
                for zz in range(z1, z2+1):
                    rem.pop((xx, yy, zz), None)
        boxes.append((x1, y1, z1, x2, y2, z2, st))
    return boxes

LIMIT = 32768                     # 服务端 /fill 单条硬上限,超了直接拒
def split_box(b):
    x1, y1, z1, x2, y2, z2, st = b
    out = [b]; res = []
    while out:
        x1, y1, z1, x2, y2, z2, st = out.pop()
        vol = (x2-x1+1) * (y2-y1+1) * (z2-z1+1)
        if vol <= LIMIT:
            res.append((x1, y1, z1, x2, y2, z2, st)); continue
        dims = [(x2-x1+1, 0), (y2-y1+1, 1), (z2-z1+1, 2)]
        dims.sort(reverse=True)
        ax = dims[0][1]
        if ax == 0:
            mid = (x1+x2)//2
            out.append((x1, y1, z1, mid, y2, z2, st)); out.append((mid+1, y1, z1, x2, y2, z2, st))
        elif ax == 1:
            mid = (y1+y2)//2
            out.append((x1, y1, z1, x2, mid, z2, st)); out.append((x1, mid+1, z1, x2, y2, z2, st))
        else:
            mid = (z1+z2)//2
            out.append((x1, y1, z1, x2, y2, mid, st)); out.append((x1, y1, mid+1, x2, y2, z2, st))
    return res

# ============ 主流程 ============
USAGE = ('用法: python3 08-计划生成-mc-plan.py <schematic> <存档目录> <x0> <z0> <base_y> <输出计划> '
         '[--no-support]')
if len(sys.argv) < 7 or sys.argv[1] in ('-h', '--help'):
    sys.stderr.write(USAGE + '\n')
    sys.exit(2)

sch, worldpath, ox, oz, by, outpath = sys.argv[1], sys.argv[2], \
    int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]

root = load_schematic(sch)
W, H, L = int(root['Width']), int(root['Height']), int(root['Length'])

print('建筑 %d×%d×%d,锚点 世界(%d, %d, %d)' % (W, H, L, ox, by, oz))
print('TileEntities: %d  Entities: %d' % (
    len(root.get('TileEntities') or []), len(root.get('Entities') or [])))
for te in (root.get('TileEntities') or [])[:20]:
    print('   TE %s @ %s,%s,%s' % (te.get('id'), te.get('x'), te.get('y'), te.get('z')))

build = {}       # 世界坐标 -> 状态
unknown = collections.Counter()
for (x, y, z), bid, meta in schematic_cells(root):
    if bid == 0: continue
    st = modern(bid, meta)
    if st is None:
        unknown[(bid, meta)] += 1; continue
    build[(ox + x, by + y, oz + z)] = st

if unknown:
    print('!! 未映射的 (id,meta):', dict(unknown))

# --- 支撑填充。两种,各自独立,都不与建筑方块重叠 ---
# 这份示意是「山坡上」盖的:南侧院落的地坪就是示意 y=0(天然地面当楼板,室内是空腔,
# 绝对不能填);北侧主楼的地坪在示意 y=22/23,底下那 22 层在原作里是山坡的土。
# 本场地是平的,所以要让主楼不悬空,只能自己造那段土台。
#   (a) 地基:锚点比地面高的列(东侧水面、凹坑),从地面顶补到锚点下一格。
#   (b) 土台:最低方块恰在示意 y=22/23 的列(=主楼楼层底下),补到楼层下一格。
# 判据用「最低方块的示意 y」而不是「比地面低就填」,后者会把院落那间空屋子灌满石头。
MOUND_SY = {22, 23}
w = Save(worldpath)
lowest = {}
for (bx, byy, bz) in build:
    key = (bx, bz)
    if byy < lowest.get(key, 1 << 30): lowest[key] = byy

# 土台只铺在「主楼楼层矩形」内,不能按「最低方块在 22/23」全图扫 —— 院墙顶上也有
# 一圈 y=22/23 的装饰腰线,那样扫会把院墙下层的门洞/窗洞灌成实心石头。
# 楼层矩形 = 主楼区内 y∈{22,23} 那层方块的包围盒。
sx_of = lambda bx: bx - ox
sz_of = lambda bz: bz - oz
kc = [(bx, bz) for (bx, yy, bz) in build
      if 16 <= sx_of(bx) <= 138 and 0 <= sz_of(bz) <= 46 and (yy - by) in MOUND_SY]
if kc:
    mx0 = min(p[0] for p in kc); mx1 = max(p[0] for p in kc)
    mz0 = min(p[1] for p in kc); mz1 = max(p[1] for p in kc)
else:
    mx0 = mx1 = mz0 = mz1 = 0
print('土台矩形:世界 x[%d..%d] z[%d..%d]  (示意 x[%d..%d] z[%d..%d])' % (
    mx0, mx1, mz0, mz1, sx_of(mx0), sx_of(mx1), sz_of(mz0), sz_of(mz1)))

# 保护名单:玩家留下的容器所在列,一律不填(填掉会连内容一起没)。宁可留一道 1×1 的
# 石缝(从外面看不见),也不动别人的东西。要覆盖请明确说。
PROTECT = {(-646, -310)}                                  # ironchest:dirt_chest @ y=73
MOUND_TOP = by + min(MOUND_SY) - 1                        # 楼层下一格
NO_SUPPORT = '--no-support' in sys.argv

support = {}
nfound = 0
for (bx, bz) in (() if NO_SUPPORT else lowest):           # (a) 地基
    if (bx, bz) in PROTECT: continue
    t = w.top(bx, bz)
    if t < by - 1:
        nfound += 1
        for yy in range(t + 1, by):
            support[(bx, yy, bz)] = '__SUPPORT__'
nmound = 0
for bx in (() if NO_SUPPORT else range(mx0, mx1 + 1)):    # (b) 土台
    for bz in range(mz0, mz1 + 1):
        lo = lowest.get((bx, bz))
        # 两个条件缺一不可:
        #   矩形   —— 挡住院墙顶上那圈腰线(否则会把院墙下层的门洞窗洞灌成石头)
        #   最低方块 ≥ 楼层 —— 只补「脚下是空腔」的列;主楼自己的外墙墙脚本来就落到地面,
        #                      不需要土台,把它们算进来反而会把墙上的窗口糊死
        if lo is None or lo - by < min(MOUND_SY): continue
        if (bx, bz) in PROTECT: continue
        nmound += 1
        start = max(by, w.top(bx, bz) + 1)
        for yy in range(start, MOUND_TOP + 1):
            support[(bx, yy, bz)] = '__SUPPORT__'

print('建筑方块 %d,支撑列 %d(地基 %d + 土台 %d),支撑方块 %d' % (
    len(build), len(set((x, z) for x, y, z in support)), nfound, nmound, len(support)))
hist = collections.Counter(lowest.values())
print('各列「最低建筑方块」的世界 y 分布:')
for yy in sorted(hist):
    print('   y=%-4d %5d 列' % (yy, hist[yy]))

allsup = merge(support)
allbld = merge(build)
print('支撑合并 %d 个长方体,建筑合并 %d 个长方体' % (len(allsup), len(allbld)))

def emit(boxes, default_state):
    cmds = []
    for b in boxes:
        for (x1, y1, z1, x2, y2, z2, st) in split_box(b):
            cmds.append('fill %d %d %d %d %d %d %s' % (
                x1, y1, z1, x2, y2, z2, 'minecraft:stone' if st == '__SUPPORT__' else st))
    return cmds

sup_cmds = emit(allsup, 'minecraft:stone')
bld_cmds = emit(allbld, None)

# 按站点分组:4 个象限,先把 bot 传到象限中心,再发该象限的指令
cx = ox + W // 2; cz = oz + L // 2
def station(x, z):
    sx = 0 if x < cx else 1
    sz = 0 if z < cz else 1
    return (ox + W//4 + sx*(W//2), by + 30, oz + L//4 + sz*(L//2))

def parse_box(cmd):
    p = cmd.split()
    return int(p[1]), int(p[3])

def group(cmds):
    g = collections.defaultdict(list)
    for c in cmds:
        x0, z0 = parse_box(c)
        g[station(x0, z0)].append(c)
    return g

plan = []
for phase, cmds in (('支撑', sup_cmds), ('建筑', bld_cmds)):
    g = group(cmds)
    for st, lst in sorted(g.items()):
        plan.append({'tp': list(st), 'phase': phase, 'n': len(lst)})
        for c in lst:
            plan.append({'fill': c})

with open(outpath, 'w') as f:
    for step in plan:
        f.write(json.dumps(step) + '\n')

nfill = sum(1 for s in plan if 'fill' in s)
print('计划已写 %s: %d 条 fill,%d 个站点批次' % (
    outpath, nfill, sum(1 for s in plan if 'tp' in s)))
print('按 60 条/批 约需 %d 批' % ((nfill + 59) // 60))
