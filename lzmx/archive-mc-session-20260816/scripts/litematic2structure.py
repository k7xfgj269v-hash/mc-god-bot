#!/usr/bin/env python3
"""litematic -> Minecraft structure .nbt 转换器
用法: litematic2structure.py <in.litematic> <out.nbt> [namespace]
输出 gzip 压缩的结构文件,可直接放入 datapack data/<ns>/structures/
"""
import sys, math, gzip
import nbtlib
from nbtlib.tag import Byte, Short, Int, Long, Float, Double, String, List, Compound, IntArray

def tag_xyz(tag):
    """Size/Position 兼容 IntArray 和 Compound{x,y,z} 两种写法"""
    if isinstance(tag, IntArray):
        return [int(tag[0]), int(tag[1]), int(tag[2])]
    return [int(tag['x']), int(tag['y']), int(tag['z'])]

def convert(infile, outfile):
    data = nbtlib.load(infile)
    all_states = []      # [(x,y,z, palette_index)]
    all_palette = []     # [{Name, Properties}] 全局 palette
    index_of = {}        # 字符串描述 -> palette index
    tile_by_pos = {}     # (x,y,z) -> nbt compound

    for rn, r in data['Regions'].items():
        size = tag_xyz(r['Size'])
        pos  = tag_xyz(r['Position'])
        pal  = r['BlockStatePalette']
        # palette 字符串化(含属性,用于去重)
        pal_desc = []
        for p in pal:
            name = str(p.get('Name', ''))
            props = p.get('Properties', Compound())
            desc = name + ('[' + ','.join(f"{k}={v}" for k, v in props.items()) + ']' if props else '')
            pal_desc.append(desc)
        # size 可为负 = 翻转区域(litematic 表示法);用绝对值迭代,负轴反向映射世界坐标
        abs_size = [abs(s) for s in size]
        flip = [1 if s > 0 else -1 for s in size]
        # 解码位压缩 BlockStates
        states = [int(x) & 0xFFFFFFFFFFFFFFFF for x in r['BlockStates']]
        volume = abs_size[0] * abs_size[1] * abs_size[2]
        bits = max(2, (len(states) * 64) // volume) if volume else 2
        mask = (1 << bits) - 1
        def get_value(i):
            p = i * bits                 # 位偏移 = 块索引 × 每块位数
            word = p >> 6
            off  = p & 63
            lo = (states[word] >> off) if word < len(states) else 0
            hi = (states[word + 1] << (64 - off)) if (word + 1 < len(states) and off) else 0
            return (lo | hi) & mask
        # 方块实体按位置索引(此版 litematic 用 x/y/z 键)
        for te in r.get('TileEntities', []):
            tp = (int(te['x']), int(te['y']), int(te['z']))
            tile_by_pos[tp] = te
        idx = 0
        for y in range(abs_size[1]):
            for z in range(abs_size[2]):
                for x in range(abs_size[0]):
                    si = get_value(idx); idx += 1
                    if si == 0:
                        continue
                    wx = pos[0] + flip[0] * x
                    wy = pos[1] + flip[1] * y
                    wz = pos[2] + flip[2] * z
                    desc = pal_desc[si]
                    if desc not in index_of:
                        index_of[desc] = len(all_palette)
                        p = pal[si]
                        entry = Compound(Name=p.get('Name', String('minecraft:air')))
                        if p.get('Properties'):
                            entry['Properties'] = p['Properties']
                        all_palette.append(entry)
                    all_states.append((wx, wy, wz, index_of[desc]))

    # 计算整体包围盒并归一化坐标
    xs = [s[0] for s in all_states]; ys = [s[1] for s in all_states]; zs = [s[2] for s in all_states]
    if not all_states:
        raise SystemExit("empty build")
    minx, maxx = min(xs), max(xs); miny, maxy = min(ys), max(ys); minz, maxz = min(zs), max(zs)
    size = [maxx - minx + 1, maxy - miny + 1, maxz - minz + 1]
    blocks = []
    for (x, y, z, si) in all_states:
        entry = Compound(state=Int(si), pos=List[Int]([x - minx, y - miny, z - minz]))
        te = tile_by_pos.get((x, y, z))
        if te is not None:
            # 结构格式: nbt 字段存方块实体数据(去掉冗余坐标字段)
            n = Compound()
            for k, v in te.items():
                if k not in ('x', 'y', 'z'):
                    n[k] = v
            entry['nbt'] = n
        blocks.append(entry)

    root = Compound({
        'DataVersion': Int(3465),           # 1.20.1(注意大写 D,原版格式)
        'size': List[Int]([size[0], size[1], size[2]]),
        'palette': List[Compound](all_palette),
        'blocks': List[Compound](blocks),
        'entities': List[Compound]([]),
    })
    payload = nbtlib.File(root)
    import io
    buf = io.BytesIO()
    payload.write(buf)
    with gzip.open(outfile, 'wb') as f:
        f.write(buf.getvalue())
    print(f"blocks={len(blocks)} palette={len(all_palette)} size={size} tileEntities={len(tile_by_pos)}")
    print(f"output: {outfile}")

if __name__ == '__main__':
    convert(sys.argv[1], sys.argv[2])
