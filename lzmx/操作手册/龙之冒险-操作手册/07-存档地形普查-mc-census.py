#!/usr/bin/env python3
"""存档地形普查 —— 直接读 Minecraft 存档 region 文件,离线得出某片区域的地形与占用情况。

用途(不需要开游戏、不需要 bot、不消耗服务器传包):
  - 动大工程(大规模 /fill、铺地基、盖建筑)之前,先离线确认目标区域里有什么:
    地面最高点、水面、地下矿脉,以及**玩家留下的东西**(箱子/告示牌/刷怪笼)。
  - 「可疑方块」一栏就是「非自然方块」,即玩家放置或 mod 结构;真出现箱子之类,
    开填前必须先问过玩家,别把人家仓库埋了(填掉的箱子会连内容一起消失)。

用法:
  python3 07-存档地形普查-mc-census.py <存档目录> <x0> <x1> <z0> <z1> <y0> <y1>

例(查 166×100 城堡占地):
  python3 07-存档地形普查-mc-census.py \
    "/Users/ludwigxu/Library/Application Support/minecraft/saves/呢松的世界-回档前备份-20260818-0916" \
    -732 -564 -348 -246 0 120

注意存档目录要选**正在被游戏写入的那一份**(看 mtime)。

三个必须知道的格式坑(本脚本已经处理好,改动时别踩回去):

  1) region 表头:4096 个 4 字节偏移项 + 4096 个 4 字节时间戳 = 8192 字节。
     每个条目 4 字节 = **前 3 字节大端扇区偏移 + 第 4 字节扇区数**。
     McRegion(.mcr)与 Anvil(.mca)的**表头完全同构**,区别只在**区块载荷**
     (.mcr 是单层 Blocks/Data,.mca 是 sections 数组 / 1.13+ 的 block_states 调色板)。
     原先这里写的是「本存档是旧版 McRegion 头…(Anvil 才是 4 字节偏移)」,**那句是错的** ——
     Anvil 根本没有「4 字节偏移」这种布局,照那样读会把偏移读大 ~256 倍、越界到文件尾,
     表现是每个 chunk 都返回 None。实测反驳(本存档 region/r.-2.-1.mca,9,912,320 字节 /
     2,420 扇区,1024 个非空条目):按 3+1 解**非法 0 个**;按「4 字节整数当偏移」解
     **非法 1020 个** —— 任何真 Anvil 文件都不可能是后者那种布局。
     文件头总长 = 4096 偏移 + 4096 时间戳 = 8192 字节(只读 4096 会 unpack 报错)。

  2) chunk 是个 gzip/zlib 流,解出来是 NBT。**根复合的名字没有类型字节前缀**
     (结构是 [0x0a][名字长度2][名字][条目...]),所以不能直接用通用的「先读类型字节」
     payload 解析器从第 0/1 字节开始啃 —— 会把名字长度当成 tag 类型,一路错位到全零区,
     结果是一个空 dict、普查全是 0。必须手工走根复合:读 0x0a → 读名字长度+名字 → 再循环条目。

  3) 方块索引的位序:1.18+ 的 section 里 `data` 是打包 long 数组,
     索引 k = (y*16 + z)*16 + x,**x 在最低 4 位、y 在最高 4 位**。
     写成 1.12 那种 x 最高的老顺序,会把 x 和 y 对调,普查出来是一片
     「高度每 16 格在 79/63 之间跳」的棋盘格假象 —— 自然地形不可能长这样,见到即知错。
"""
import struct, os, zlib, gzip, sys, collections

def rd(t, b, i):
    if t == 1: return struct.unpack('>b', b[i:i+1])[0], i+1
    if t == 2: return struct.unpack('>h', b[i:i+2])[0], i+2
    if t == 3: return struct.unpack('>i', b[i:i+4])[0], i+4
    if t == 4: return struct.unpack('>q', b[i:i+8])[0], i+8
    if t == 5: return struct.unpack('>f', b[i:i+4])[0], i+4
    if t == 6: return struct.unpack('>d', b[i:i+8])[0], i+8
    if t == 7:
        n = struct.unpack('>i', b[i:i+4])[0]; return b[i+4:i+4+n], i+4+n
    if t == 8:
        n = struct.unpack('>H', b[i:i+2])[0]; return b[i+2:i+2+n].decode('utf-8','replace'), i+2+n
    if t == 9:
        et = b[i]; n = struct.unpack('>i', b[i+1:i+5])[0]; i += 5; out = []
        for _ in range(n):
            v, i = rd(et, b, i); out.append(v)
        return out, i
    if t == 10:
        out = {}
        while True:
            tt = b[i]; i += 1
            if tt == 0: return out, i
            n = struct.unpack('>H', b[i:i+2])[0]; i += 2
            nm = b[i:i+n].decode('utf-8','replace'); i += n
            v, i = rd(tt, b, i); out[nm] = v
    if t == 11:
        n = struct.unpack('>i', b[i:i+4])[0]; i += 4
        return list(struct.unpack('>%di' % n, b[i:i+4*n])), i+4*n
    if t == 12:
        n = struct.unpack('>i', b[i:i+4])[0]; i += 4
        return list(struct.unpack('>%dq' % n, b[i:i+8*n])), i+8*n
    raise ValueError('bad tag %d' % t)

W = sys.argv[1]
_reg = {}
def chunk(cx, cz):
    k = (cx >> 5, cz >> 5)
    if k not in _reg:
        fn = os.path.join(W, 'region', 'r.%d.%d.mca' % k)
        _reg[k] = open(fn, 'rb').read() if os.path.exists(fn) else None
    b = _reg[k]
    if b is None: return None
    idx = (cx & 31) + (cz & 31) * 32
    raw = b[idx*4:idx*4+4]
    if len(raw) < 4 or raw[:3] == b'\0\0\0': return None
    off = int.from_bytes(raw[:3], 'big')
    if off*4096 + 5 > len(b): return None
    ln = struct.unpack('>I', b[off*4096:off*4096+4])[0]
    comp = b[off*4096+4]
    body = b[off*4096+5:off*4096+5+ln-1]
    d = zlib.decompress(body) if comp == 2 else (gzip.decompress(body) if comp == 1 else body)
    try:
        # 根复合: [0x0a][名字长度][名字][条目...] —— 名字没有类型字节前缀,必须单独读
        i = 1
        n = struct.unpack('>H', d[i:i+2])[0]; i += 2 + n
        root = {}
        while True:
            tt = d[i]; i += 1
            if tt == 0: break
            n = struct.unpack('>H', d[i:i+2])[0]; i += 2
            nm = d[i:i+n].decode('utf-8','replace'); i += n
            v, i = rd(tt, d, i); root[nm] = v
    except Exception:
        return None
    return root

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
        r = chunk(cx, cz)
        if r is None:
            continue
        for s in r.get('sections') or []:
            y0s = s.get('Y', 0)
            bs = s.get('block_states')
            if bs:
                pal = bs.get('palette') or []
                names = [p.get('Name', '?') for p in pal]
                idxs = None
                if len(names) > 1 or not names[0].endswith('air'):
                    data = bs.get('data'); nb = len(names)
                    if data is None:
                        idxs = [0] * 4096
                    else:
                        bits = max(4, (nb - 1).bit_length()); per = 64 // bits; mask = (1 << bits) - 1
                        idxs = []
                        for li in range((4096 + per - 1) // per):
                            v = data[li]
                            for kk in range(per):
                                if len(idxs) >= 4096: break
                                idxs.append((v >> (kk * bits)) & mask)
                if idxs is not None:
                    for kk in range(4096):
                        nm = names[idxs[kk]] if idxs[kk] < len(names) else '?'
                        if nm.endswith('air'): continue
                        # 索引 k = (y*16 + z)*16 + x ⇒ x 最低 4 位、z 次之、y 最高
                        lx = kk & 15; lz = (kk >> 4) & 15; yy = (kk >> 8) & 15
                        gx = cx*16 + lx; gz = cz*16 + lz; gy = y0s*16 + yy
                        if not (x0 <= gx <= x1 and z0 <= gz <= z1 and ylo <= gy <= yhi): continue
                        census[nm] += 1
                        cur = heights.get((gx, gz))
                        if cur is None or gy > cur: heights[(gx, gz)] = gy
                        short = nm.split(':')[-1]
                        if short not in NATURAL and not short.startswith(NATURE_PREFIX) and not any(nm.endswith(sfx) for sfx in NATURE_SUFFIX):
                            suspicious[nm] += 1
                            sus_pos.setdefault(nm, (gx, gy, gz))
        for be in (r.get('block_entities') or []):
            bx, by, bz = be.get('x'), be.get('y'), be.get('z')
            if bx is None: continue
            if x0 <= bx <= x1 and z0 <= bz <= z1 and ylo <= by <= yhi:
                bents.append((be.get('id'), bx, by, bz))

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
