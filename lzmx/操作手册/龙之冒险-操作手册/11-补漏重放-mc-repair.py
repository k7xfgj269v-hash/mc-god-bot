#!/usr/bin/env python3
"""重放服务端回了「No blocks were filled」的那些 /fill。

上一轮的教训:bot 的 tp 之后区块是异步加载的,司机只等 bot 侧 [exec] 回执就发下一批,
于是新站点边缘约 5% 的 fill 在目标区块尚未加载时执行,服务端静默回 "No blocks were filled"。

这条回执的歧义(别当成确定的失败判据):后来实测发现它**多数情况下是良性的** —— 盒子与
已填区域重叠、或该格本来就是目标态,重发一次仍然回 no-op,探针(10-探针核验-mc-verify.py)显示格子是
对的;只有少数是真没落地(区块未加载)。所以本脚本的策略是「宁可重发」:重发良性的那些
只是无害的 no-op,重发真漏的那些才是在修东西。

做法:发一批,按顺序把 fill 与服务端回执配对,凡配到 "No blocks were filled" 的记下来,
下一轮重发,直到清零 / 达到轮次上限 / 判定策略无效而停手。

用法:
  python3 11-补漏重放-mc-repair.py <指令文件> [每批条数] [最大轮次]

指令文件 = 每行一条完整 fill 指令(例如 09-投喂驱动-mc-drive.py 写出的 /tmp/mc-drive-noop.txt)。
修不掉的会落到 /tmp/refill-remain.txt。
"""
import json, os, re, sys, time

BRIDGE = os.path.expanduser('~/Library/Application Support/minecraft/mc-bridge')
OUTBOX = BRIDGE + '/outbox.jsonl'
LOG = '/tmp/mc-god-bot.log'

FILL_RE = re.compile(r'----+\s*$')
OK_S = 'Successfully filled'
BAD_S = 'No blocks were filled'


def send(cmds):
    with open(OUTBOX, 'a') as f:
        for c in cmds:
            f.write(json.dumps({'cmd': c}) + '\n')
        f.flush()
        os.fsync(f.fileno())


class Tail:
    def __init__(self, path):
        self.path = path
        self.pos = os.path.getsize(path) if os.path.exists(path) else 0
        self.buf = b''

    def new_lines(self):
        with open(self.path, 'rb') as f:
            f.seek(self.pos)
            data = f.read()
            self.pos = f.tell()
        self.buf += data
        out = []
        while b'\n' in self.buf:
            line, self.buf = self.buf.split(b'\n', 1)
            out.append(line.decode('utf-8', 'replace'))
        return out


def bbox(cmds):
    xs, zs = [], []
    for c in cmds:
        p = c.split()
        xs += [int(p[1]), int(p[4])]
        zs += [int(p[3]), int(p[6])]
    return (min(xs) + max(xs)) // 2, (min(zs) + max(zs)) // 2, min(xs), max(xs), min(zs), max(zs)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        sys.stderr.write('用法: python3 11-补漏重放-mc-repair.py <指令文件> [每批条数] [最大轮次]' + '\n')
        sys.exit(2)
    path = sys.argv[1]
    batch = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    maxround = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    todo = [l.strip() for l in open(path) if l.strip()]
    print('待修 %d 条' % len(todo), flush=True)

    for rnd in range(1, maxround + 1):
        if not todo:
            break
        cx, cz, x0, x1, z0, z1 = bbox(todo)
        print('-- 第 %d 轮:%d 条,bbox x[%d..%d] z[%d..%d],tp 到 (%d,?,%d)'
              % (rnd, len(todo), x0, x1, z0, z1, cx, cz), flush=True)
        send(['tp ludwiggod %d 110 %d' % (cx, cz)])
        time.sleep(6)
        tail = Tail(LOG)
        tail.new_lines()

        bad = []
        for i in range(0, len(todo), batch):
            grp = todo[i:i + batch]
            send(grp)
            # 等这一批的服务端回执全部到齐
            got, ack = 0, []
            t0 = time.time()
            while got < len(grp) and time.time() - t0 < 30:
                for l in tail.new_lines():
                    m = re.match(r'\[msg\] (Successfully filled|No blocks were filled)', l)
                    if m:
                        ack.append(m.group(1))
                        got += 1
                if got < len(grp):
                    time.sleep(0.1)
            for j, cmd in enumerate(grp):
                if j >= len(ack) or ack[j] == BAD_S:
                    bad.append(cmd)
            print('   批 %d/%d:回执 %d/%d,累计待重发 %d'
                  % (i // batch + 1, (len(todo) + batch - 1) // batch, got, len(grp), len(bad)), flush=True)
            time.sleep(0.4)

        print('== 第 %d 轮结束:仍失败 %d 条' % (rnd, len(bad)), flush=True)
        if len(bad) == len(todo):
            print('!! 一条都没修好,判定为策略无效,停手', flush=True)
            todo = bad
            break
        todo = bad

    if todo:
        with open('/tmp/refill-remain.txt', 'w') as f:
            f.write('\n'.join(todo) + '\n')
        print('!! 仍有 %d 条未修复,已写 /tmp/refill-remain.txt' % len(todo))
    else:
        print('== 全部修复')


main()
