#!/usr/bin/env python3
"""schematic 分层 ASCII 查看 —— 打印指定若干层的俯视图(每 2 格采样)。

用法:
  python3 14-示意分层查看-mc-schem-layer.py <y> [y ...]       # 层号是示意坐标,y=0 为最底层

例:python3 14-示意分层查看-mc-schem-layer.py 22 23         # 看主楼那两层地坪

注意:被读的 schematic 路径写死在下面的 P,**不在命令行里** —— 命令行位置全留给层号了。
      这个 P 当前是 /tmp/chateau2.schematic,⚠️ **在 /tmp 里,跨会话/重启可能已被清掉**;
      文件不在时会直接报 FileNotFoundError,那时改 P 指到实际位置即可(改这里不算改行为,
      因为它本来就没有命令行入口)。

依赖: pip3 install --break-system-packages --user nbtlib==2.0.4 anvil-parser2==0.10.6
      解析层见 mc_lib.py。
"""
import sys

from mc_lib import load_schematic, schematic_cells

P = '/tmp/chateau2.schematic'

if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
    sys.stderr.write('用法: python3 14-示意分层查看-mc-schem-layer.py <y> [y ...]   # 层号是示意坐标,y=0 为最底层' + '\n')
    sys.exit(2)

root = load_schematic(P)
W, H, L = int(root['Width']), int(root['Height']), int(root['Length'])

CH = {5:'p',126:'_',1:'S',4:'#',17:'L',102:'o',188:'|',2:'G',31:',',134:'/',18:'T',89:'%',
      67:'/',96:'d',37:'y',38:'*',139:'=',3:'D',21:'B'}

want = [int(a) for a in sys.argv[1:]]
wanted = set(want)
bid_of = {}                                   # (y, z, x) -> id,只收命令行点名的层
for (x, y, z), bid, meta in schematic_cells(root, ys=wanted):
    bid_of[(y, z, x)] = bid

for y in want:
    print('=== 第 y=%d 层 (x 0→%d, z 0→%d, 每 2 格采样) ===' % (y, W-1, L-1))
    print('    ' + ''.join('%d' % ((x // 10) % 10) for x in range(0, W, 2)))
    for z in range(0, L, 2):
        row = ''
        for x in range(0, W, 2):
            b = bid_of.get((y, z, x), 0)
            row += ' ' if b == 0 else CH.get(b, '?')
        print('%3d %s' % (z, row))
    print()
