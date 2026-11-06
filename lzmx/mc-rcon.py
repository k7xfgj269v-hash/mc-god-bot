#!/usr/bin/env python3
"""RCON 神权通道 - 向游戏内发指令

用法:
  python3 mc-rcon.py "<指令>"                发一条指令,例:
    python3 mc-rcon.py "attribute @s minecraft:generic.max_health base set 1000000"
  python3 mc-rcon.py --check                 三态诊断:游戏在不在 / RCON 配置好没好 / 通道通不通
  python3 mc-rcon.py --retry 5 "<指令>"      失败自动重试 5 次(间隔 3s,等游戏重启)
  echo "cmd1" | python3 mc-rcon.py -         从 stdin 逐行批量执行
  python3 mc-rcon.py --world 新的世界 ...    指定世界(默认自动探测当前开的)

密码自动从 saves/<世界>/server.properties 读取,无临时文件依赖。
"""
import socket, struct, sys, os, subprocess, time, glob, re

SAVES_DIR = os.path.expanduser("~/Library/Application Support/minecraft/saves")
HOST, PORT = "127.0.0.1", 25575
GAME_PORT = 51620  # LAN Properties 固定的开房端口


def find_world():
    """自动探测当前使用的世界:优先 server-port==GAME_PORT 且开了 rcon 的,否则取最近修改的 rcon 世界。"""
    cands = []
    for sp in glob.glob(os.path.join(SAVES_DIR, "*", "server.properties")):
        try:
            with open(sp) as f:
                txt = f.read()
        except OSError:
            continue
        m_pass = re.search(r"^rcon\.password=(.+)$", txt, re.M)
        m_en = re.search(r"^enable-rcon=(true|false)$", txt, re.M)
        m_port = re.search(r"^server-port=(\d+)$", txt, re.M)
        if m_en and m_en.group(1) == "true" and m_pass and m_pass.group(1):
            world = os.path.basename(os.path.dirname(sp))
            cands.append((world, m_pass.group(1), m_port.group(1) if m_port else ""))
    if not cands:
        return None
    for w, pwd, port in cands:
        if port == str(GAME_PORT):
            return w, pwd
    return cands[-1][0], cands[-1][1]  # 最后一个修改的


def rcon_info(world_arg=None):
    if world_arg:
        sp = os.path.join(SAVES_DIR, world_arg, "server.properties")
        if not os.path.exists(sp):
            return None, "世界不存在:%s" % world_arg
        txt = open(sp).read()
        m_pass = re.search(r"^rcon\.password=(.+)$", txt, re.M)
        m_en = re.search(r"^enable-rcon=(true|false)$", txt, re.M)
        if not m_pass or not m_pass.group(1):
            return None, "世界 %s 未配置 rcon.password" % world_arg
        return (world_arg, m_pass.group(1)), None
    return find_world(), None


def packet(rid, typ, payload):
    data = struct.pack("<ii", rid, typ) + payload.encode("utf-8") + b"\x00\x00"
    return struct.pack("<i", len(data)) + data


def recv_packet(s):
    hdr = s.recv(12)
    if len(hdr) < 12:
        return None
    length, rid, typ = struct.unpack("<iii", hdr)
    if length < 8 or length > 65536:  # 坏包防护
        return None
    body = b""
    while len(body) < length - 8:
        chunk = s.recv(length - 8 - len(body))
        if not chunk:
            break
        body += chunk
    return rid, typ, body


def game_running():
    """游戏进程在跑且监听 GAME_PORT?"""
    try:
        out = subprocess.run(["lsof", "-nP", "-iTCP:%d" % GAME_PORT, "-sTCP:LISTEN"],
                             capture_output=True, text=True, timeout=5).stdout
        return bool(re.search(r"\bjava\b", out))
    except Exception:
        return False


def send(cmd, retries=1, timeout=15, world=None):
    info, err = rcon_info(world)
    if err:
        return "ERR|%s" % err
    if info is None:
        return "ERR|没找到开了 RCON 的世界(先改 server.properties 的 enable-rcon=true 并重启游戏)"
    world_name, password = info
    for attempt in range(max(1, retries)):
        try:
            s = socket.create_connection((HOST, PORT), timeout=timeout)
            s.settimeout(timeout)
            s.sendall(packet(1, 3, password))
            p = recv_packet(s)
            if p is None or p[1] != 2:
                return "ERR|认证失败:rcon.password 与 server.properties 不一致(世界:%s)" % world_name
            s.sendall(packet(2, 2, cmd))
            out = []
            while True:
                try:
                    p = recv_packet(s)
                except socket.timeout:
                    break
                if p is None:
                    break
                if p[1] == 0:
                    out.append(p[2].decode("utf-8", "replace"))
            s.close()
            return "OK|" + ("".join(out).strip() or "(执行成功,无回显)")
        except (ConnectionRefusedError, ConnectionResetError):
            if attempt < max(1, retries) - 1:
                time.sleep(3)
                continue
            return "ERR|连接失败:游戏没开,或 RCON 未生效(改完 server.properties 需重启游戏重进世界)"
        except socket.timeout:
            return "ERR|连接超时:游戏繁忙或无响应"
    return "ERR|未知错误"


def check():
    print("=== RCON 通道诊断 ===")
    info, err = rcon_info(None)
    if err:
        print("  ✗ 配置错误: %s" % err)
    elif info is None:
        print("  ✗ 没有世界开启 RCON(需在 saves/<世界>/server.properties 设 enable-rcon=true)")
    else:
        world, pwd = info
        print("  ✓ RCON 配置: 世界[%s] enable-rcon=true, 密码已就绪" % world)
    print("  %s 游戏监听 %s 端口" % ("✓" if game_running() else "✗", GAME_PORT))
    r = send("list", retries=1, timeout=5)
    if r.startswith("OK"):
        print("  ✓ 通道连通:", r.split("|", 1)[1])
        return 0
    print("  ✗ 通道不通: %s" % r)
    print("  提示: 配置已改的话, 重启游戏重进世界即可激活")
    return 1


def main():
    args = sys.argv[1:]
    world = None
    if "--world" in args:
        i = args.index("--world")
        world = args[i + 1]
        args = args[:i] + args[i + 2:]
    if not args:
        print(__doc__)
        return 2
    if args[0] == "--check":
        return check()
    if args[0] == "--retry":
        n = int(args[1])
        cmd = " ".join(args[2:])
        print(send(cmd, retries=n, world=world))
        return 0
    if args[0] == "-":
        for line in sys.stdin:
            line = line.strip()
            if line:
                print(send(line, world=world))
        return 0
    cmd = " ".join(args)
    print(send(cmd, world=world))
    return 0


if __name__ == "__main__":
    sys.exit(main())
