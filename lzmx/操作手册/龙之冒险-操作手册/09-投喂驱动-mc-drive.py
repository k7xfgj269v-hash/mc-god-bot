#!/usr/bin/env python3
"""按计划文件逐步投喂 bot 的 outbox,并按顺序核对「bot 侧 + 服务端」两级回执。

为什么要两级回执:
  - bot 的 outbox 轮询是 readFileSync → rmSync,中间有极小的竞态窗口(刚写入的行可能
    随 rm 一起消失),所以数 bot 日志里的 [exec] fill 条数,确认这批真被读走了。
  - 但 [exec] 只证明 bot **发出**了指令,不证明服务端**执行**了。/fill 打到尚未加载的
    区块时,服务端会静默回 "No blocks were filled"。所以还要按序配对服务端 [msg] 回执。

关于 "No blocks were filled" 的歧义(**别把它当成确定的失败判据**):
  实测它多数情况下是**良性**的 —— 盒子与已填区域重叠、或该格本来就是目标态,重发一次
  仍然回 no-op,而探针(10-探针核验-mc-verify.py)显示格子是对的;但它**确实**有一部分是真没落地
  (区块未加载时执行)。所以本脚本把它记成「需要复核的信号」,写进 /tmp/mc-drive-noop.txt,
  交给 11-补漏重放-mc-repair.py 重发或人工核查,而不是当场判定失败。

tp 之后的观察窗不能省:tp 落地 ≠ 区块加载好。见下面 tp 分支里的 sleep(4)。

用法:
  python3 09-投喂驱动-mc-drive.py <计划> <起始行> <条数> [每批条数] [批间隔秒]

计划文件由 08-计划生成-mc-plan.py 生成:每行 {"tp":[x,y,z]} 或 {"fill":"fill ..."}。
"""
import json, os, time, sys

BRIDGE = os.path.expanduser('~/Library/Application Support/minecraft/mc-bridge')
OUTBOX = BRIDGE + '/outbox.jsonl'
LOG = '/tmp/mc-god-bot.log'

ACK_WAIT = 30        # 等一批服务端回执的上限(秒)。正常都在 1 秒内回齐,只有异常才吃满
NOOP_OUT = '/tmp/mc-drive-noop.txt'   # 配到 "No blocks were filled" 的 fill,供复核/重发


class Tail:
    def __init__(self, path):
        self.path = path
        self.pos = os.path.getsize(path) if os.path.exists(path) else 0
        self.buf = b''

    def new_lines(self):
        if not os.path.exists(self.path):
            return []
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


def send(cmds):
    with open(OUTBOX, 'a') as f:
        for c in cmds:
            f.write(json.dumps({'cmd': c}) + '\n')
        f.flush()
        os.fsync(f.fileno())


def main():
    if len(sys.argv) < 4 or sys.argv[1] in ('-h', '--help'):
        sys.stderr.write('用法: python3 09-投喂驱动-mc-drive.py <计划> <起始行> <条数> [每批条数] [批间隔秒]' + '\n')
        sys.exit(2)
    plan, start = sys.argv[1], int(sys.argv[2])
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 10 ** 9
    batch = int(sys.argv[4]) if len(sys.argv) > 4 else 120
    gap = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
    loss = 0
    steps = [json.loads(l) for l in open(plan) if l.strip()]
    steps = steps[start:start + count]
    tail = Tail(LOG)
    pending = []
    sent = []          # 已发出的 fill,按发出顺序 —— 服务端回执与它一一对位
    acks = []          # 服务端回执,按到达顺序:'OK' = Successfully filled,'NO' = No blocks were filled
    exec_seen = [0]    # 已看到的 bot 侧 [exec] fill 条数(用 list 是为了在闭包里改)

    def drain():
        """把日志里新到的相关行读进来记账。tp/xp 等无关行一律丢弃。"""
        for l in tail.new_lines():
            if l.startswith('[exec] fill'):
                exec_seen[0] += 1
            elif l.startswith('[msg] Successfully filled'):
                acks.append('OK')
            elif l.startswith('[msg] No blocks were filled'):
                acks.append('NO')

    def wait_for(cond, tmo):
        t0 = time.time()
        while True:
            drain()
            if cond() or time.time() - t0 >= tmo:
                return
            time.sleep(0.1)

    def flush():
        nonlocal pending, loss
        if not pending:
            return
        want = len(pending)
        send(pending)
        sent.extend(pending)
        # ① bot 侧回执:这批真的被 bot 读走了吗(读走才会写 [exec] fill)
        base = exec_seen[0]
        wait_for(lambda: exec_seen[0] - base >= want, 25)
        got = exec_seen[0] - base
        if got < want:
            print('   !! 只回执 %d/%d 条,疑似丢行' % (got, want), flush=True)
            loss += want - got
        # ② 服务端回执:与「已发出的 fill」按序配对。等不齐也不阻塞 —— 没到的下一批接着收,
        #    因为配对是全局按位的,迟到只会推后配对,不会错位。
        wait_for(lambda: len(acks) >= len(sent), ACK_WAIT)
        pending = []
        if gap:
            time.sleep(gap)

    done = 0
    for st in steps:
        if 'tp' in st:
            flush()
            send(['tp ludwiggod %d %d %d' % tuple(st['tp'])])
            time.sleep(0.3)
            drain()          # 丢掉 tp 自己的回执噪声,但迟到的 fill 回执照常记账
            time.sleep(4)    # 观察窗:tp 落地 ≠ 区块加载好,不留就会成片 no-op
            print('-- 站点 %-14s %s %d 条' % (st['tp'], st.get('phase', ''), st.get('n', 0)), flush=True)
            continue
        pending.append(st['fill'])
        done += 1
        if len(pending) >= batch:
            flush()
            print('   %d/%d' % (done, len([s for s in steps if 'fill' in s])), flush=True)
    flush()
    # 全部发完后统一按序配对:第 i 条 fill ↔ 第 i 条服务端回执
    pair = min(len(sent), len(acks))
    noop = [sent[i] for i in range(pair) if acks[i] == 'NO']
    print('完成 %d 条 fill,%d 条疑似丢失' % (done, loss))
    print('服务端回执 %d 条(成功 %d / no-op %d),还有 %d 条没配到回执' % (
        len(acks), acks.count('OK'), len(noop), len(sent) - pair))
    if noop:
        with open(NOOP_OUT, 'w') as f:
            f.write('\n'.join(noop) + '\n')
        print('!! %d 条回了 "No blocks were filled"(多数是良性重叠,少数是真没落地),'
              '已写 %s' % (len(noop), NOOP_OUT))


main()
