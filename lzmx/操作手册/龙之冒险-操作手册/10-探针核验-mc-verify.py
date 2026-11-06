#!/usr/bin/env python3
"""探针验证:逐点核对世界里实际是什么方块(不依赖服务端给我们回话)。

读一个点表文件(每行 "<x> <y> <z> <期望方块>"),对每点发三条 execute positioned:
  if block ~ ~ ~ <期望>                             → xp add <code+0>
  if block ~ ~ ~ air                                → xp add <code+1>
  unless block ~ ~ ~ <期望> unless block ~ ~ ~ air  → xp add <code+2>
xp add 的回执只发给 bot 自己,不会在服务器里刷屏 —— 拿它当「私密探针」。

编号编码:第 i 个点的三条指令各自加 (i+1)*100000 + y*10 + {0,1,2} 点经验;回执从日志里
按 "Gave (\\d+) experience" 抓回来,整除 100000 得第几个点、取个位得 0=命中 / 1=是空气 /
2=是别的方块。所以**同一次运行里点数不能超过 99999**。

两个前提,不满足会成片「? 无回执」:
  - 被探的区块必须是已加载的,所以开头先 tp 到所有点的中心(execute positioned 只改
    执行位置,不会加载区块);
  - 结尾要 xp set ludwiggod 0 points 归零,否则经验累积会污染下一轮编码。

用法:
  python3 10-探针核验-mc-verify.py <点表文件>

点表文件里空行和 # 开头的行会被跳过。
"""
import json, os, re, sys, time

BRIDGE = os.path.expanduser('~/Library/Application Support/minecraft/mc-bridge')
OUTBOX = BRIDGE + '/outbox.jsonl'
LOG = '/tmp/mc-god-bot.log'


def send(cmds):
    with open(OUTBOX, 'a') as f:
        for c in cmds:
            f.write(json.dumps({'cmd': c}) + '\n')
        f.flush()
        os.fsync(f.fileno())


if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
    sys.stderr.write('用法: python3 10-探针核验-mc-verify.py <点表文件>' + '\n')
    sys.exit(2)

pts = []
for ln in open(sys.argv[1]):
    ln = ln.strip()
    if not ln or ln.startswith('#'):
        continue
    p = ln.split()
    pts.append((int(p[0]), int(p[1]), int(p[2]), p[3]))

# 先确保区块加载:传到所有点的中心
cx = sum(p[0] for p in pts) // len(pts)
cz = sum(p[2] for p in pts) // len(pts)
send(['tp ludwiggod %d 100 %d' % (cx, cz)])
time.sleep(4)

start = os.path.getsize(LOG) if os.path.exists(LOG) else 0
cmds = []
for i, (x, y, z, exp) in enumerate(pts):
    base = (i + 1) * 100000 + y * 10
    cmds.append('execute positioned %d %d %d if block ~ ~ ~ %s run xp add ludwiggod %d points' % (x, y, z, exp, base + 0))
    cmds.append('execute positioned %d %d %d if block ~ ~ ~ air run xp add ludwiggod %d points' % (x, y, z, base + 1))
    cmds.append('execute positioned %d %d %d unless block ~ ~ ~ %s unless block ~ ~ ~ air run xp add ludwiggod %d points' % (x, y, z, exp, base + 2))
cmds.append('xp set ludwiggod 0 points')
send(cmds)
time.sleep(3 + len(pts) * 0.15)

txt = open(LOG, errors='replace').read()[start:]
got = {}
for m in re.finditer(r'Gave (\d+) experience', txt):
    n = int(m.group(1))
    col = n // 100000
    tag = n % 10
    got.setdefault(col, set()).add(tag)

ok = bad = 0
for i, (x, y, z, exp) in enumerate(pts, 1):
    tags = got.get(i, set())
    if 0 in tags:
        r = 'OK  %s' % exp; ok += 1
    elif 1 in tags:
        r = '空气 ✗'; bad += 1
    elif 2 in tags:
        r = '别的方块 ✗'; bad += 1
    else:
        r = '? 无回执'; bad += 1
    print('(%5d,%4d,%5d) 期望 %-42s → %s' % (x, y, z, exp, r))
print('--- 命中 %d / 异常 %d' % (ok, bad))
