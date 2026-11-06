#!/usr/bin/env python3
"""存档之神监视器 - 盯游戏日志,死亡自动补血量,崩溃检测

用法:
  python3 mc-watch.py                           默认:ludwigxu 死亡后自动把最大血量补到 1000000
  python3 mc-watch.py --player 朋友名 --hp 2000 加监控玩家并设血量(--hp 跟随最近的 --player)
  python3 mc-watch.py --no-hp                   只检测崩溃,不补血

特性:日志轮转自动跟随(最新日志文件)、补血失败自动重试 2 次、中文玩家名支持。
"""
import subprocess, sys, time, os, re

GAME_DIR = os.path.expanduser("~/Library/Application Support/minecraft")
RCON = os.path.expanduser("~/Documents/Projects/mc-lzmx/mc-rcon.py")

PLAYERS = {"ludwigxu": 1000000}   # 玩家 -> 最大血量
DO_HP = True

# 死亡消息识别:冒号后玩家名 + 死亡关键词(支持中文名)
DEATH_RE = re.compile(
    r"\[Server thread/[A-Z]+]: ([\w一-鿿]+) .*?"
    r"(died|was slain|was shot|was blown|was killed|burned to death|drowned|"
    r"suffocated|starved to death|fell from|fell off|hit the ground|"
    r"experienced kinetic energy|went off with a bang|was pricked|"
    r"walked into a cactus|was squashed|was impaled|was stung|was poked|"
    r"was skewered|was obliterated|blew up|melted|roasted|froze|was burnt|"
    r"withered|was melted|was smitten|was doomed to fall|was knocked out)"
)

# 崩溃/异常关键词
CRASH_KEYS = ("Unexpected error", "Failed to load", "Game crashed",
              "Exception in server tick loop", "Ticking entity", "Ticking block",
              "OutOfMemoryError", "Internal Exception", "Fatal error")


def rcon(cmd):
    r = subprocess.run([sys.executable, RCON, cmd], capture_output=True, text=True)
    return r.stdout.strip()


def on_death(player):
    hp = PLAYERS.get(player)
    if hp is None:
        return
    time.sleep(3)  # 等重生完成
    cmd = "attribute %s minecraft:generic.max_health base set %d" % (player, hp)
    for attempt in range(3):
        r = rcon(cmd)
        if r.startswith("OK"):
            print("[watch] %s 死亡,已自动补最大血量 %d" % (player, hp), flush=True)
            return
        time.sleep(4)
    print("[watch] %s 补血失败(RCON 未就绪?): %s" % (player, r), flush=True)


def follow_log():
    """tail -F:自动跟随日志轮转(inode 变化后重开),返回行生成器"""
    last_ino = None
    while True:
        try:
            st = os.stat(GAME_DIR + "/logs/latest.log")
            if last_ino is None:
                last_ino = st.st_ino
                f = open(GAME_DIR + "/logs/latest.log")
                f.seek(0, os.SEEK_END)
            elif st.st_ino != last_ino:  # 日志轮转
                f.close()
                last_ino = st.st_ino
                f = open(GAME_DIR + "/logs/latest.log")
        except FileNotFoundError:
            print("[watch] 日志不存在(游戏未启动),5s 后重试...", flush=True)
            time.sleep(5)
            continue
        line = f.readline()
        if not line:
            time.sleep(1)
            continue
        yield line.rstrip("\n")


def main():
    args = sys.argv[1:]
    cur = "ludwigxu"
    i = 0
    while i < len(args):
        if args[i] == "--hp":
            PLAYERS[cur] = int(args[i + 1]); i += 2
        elif args[i] == "--player":
            cur = args[i + 1]; PLAYERS.setdefault(cur, 1000000); i += 2
        elif args[i] == "--no-hp":
            DO_HP = False; i += 1
        else:
            i += 1

    print("[watch] 监视启动: %s" % ("补血 " + str(PLAYERS) if DO_HP else "仅崩溃检测"), flush=True)
    for line in follow_log():
        if DO_HP:
            m = DEATH_RE.search(line)
            if m:
                on_death(m.group(1))
        if any(k in line for k in CRASH_KEYS):
            print("[watch] 疑似崩溃/异常: %s" % line[:120], flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
