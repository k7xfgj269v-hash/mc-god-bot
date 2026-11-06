#!/usr/bin/env python3
"""存档分层 ASCII 查看 —— 把一个固定小盒子里的非空气方块打成逐层俯视图。

用法:
  python3 12-存档分层查看-mc-look.py <存档目录>

盒子写死在下面的 CX/CY/CZ(-646/73/-310)周边 17×17×9 —— 那次是为了确认玩家留下的
ironchest:dirt_chest 会不会被支撑填充埋掉(箱子被填掉会连内容一起没)。换地方就改这三个常量。
存档目录要选**正在被游戏写入的那一份**(看 mtime)。

依赖: pip3 install --break-system-packages --user nbtlib==2.0.4 anvil-parser2==0.10.6
      解析层见 mc_lib.py。

诊断信号:方块索引 i = (y*16+z)*16+x,x 在最低 4 位。位序写反的话,俯视图会变成一片
棋盘格 —— 见到即知位序反了(见 mc_lib.py 头部坑 3)。
"""
import collections
import sys

from mc_lib import Save, iter_blocks

if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
    sys.stderr.write('用法: python3 12-存档分层查看-mc-look.py <存档目录>' + '\n')
    sys.exit(2)

save = Save(sys.argv[1])

def blocks(x0, x1, z0, z1, ylo, yhi):
    """返回 {(x,y,z): 方块名} 仅非空气"""
    out = {}
    for cx in range(x0 >> 4, (x1 >> 4) + 1):
        for cz in range(z0 >> 4, (z1 >> 4) + 1):
            chunk = save.chunk(cx, cz)
            if chunk is None:
                continue
            for gx, gy, gz, nm in iter_blocks(chunk):
                if x0 <= gx <= x1 and z0 <= gz <= z1 and ylo <= gy <= yhi:
                    out[(gx, gy, gz)] = nm
    return out

CX, CY, CZ = -646, 73, -310   # 可疑箱子
print('=== 箱子周边 17×17×9 逐层非空气方块 ===')
b = blocks(CX-8, CX+8, CZ-8, CZ+8, CY-4, CY+4)
cnt = collections.Counter(v for v in b.values())
print('方块种类:', dict(cnt))
print()
print('--- 逐层俯视 (列 x=-654..-638, 行 z=-318..-302)  "." = 空气')
for y in range(CY+4, CY-5, -1):
    print('y=%d' % y)
    for z in range(CZ-8, CZ+9):
        row = ''
        for x in range(CX-8, CX+9):
            n = b.get((x, y, z))
            if n is None: row += ' .'
            else:
                s = n.split(':')[-1]
                row += {'dirt_chest':' C','chest':' C','cobblestone':' #','oak_planks':' p',
                        'spruce_planks':' P','stone':' S','gravel':' g','oak_log':' L',
                        'spruce_log':' L','crafting_table':' T','furnace':' F','torch':' t',
                        'dirt':' d','grass_block':' G','water':' ~','oak_stairs':' a',
                        'oak_slab':'_','oak_fence':'|','glass':'o','oak_door':'D','water':'~'
                       }.get(s, ' ' + (s[0] if s[0] in 'abcdefghijklmnopqrstuvwxyz' else '?'))
        print(row)
