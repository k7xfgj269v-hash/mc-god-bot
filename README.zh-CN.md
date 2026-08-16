# mc-god-bot — Minecraft「Claude 之神」假玩家通道

让 Claude 在游戏里当神：玩家说话，Claude 听到；Claude 发指令，游戏执行。基于 mineflayer 的假玩家，**只做协议入口**——不渲染、不跑物理、不加载区块，纯消息/命令双向桥。

适用：Forge 1.20.1 局域网开房（集成服务器）联机，玩家端零改动。

> [English README](README.md)

## Features

- **假玩家通道**：`ludwiggod` 以 OP 身份登录进世界，成为服务器里的一个「真实玩家」，把游戏内聊天/命令与外部进程桥接起来——不需要 RCON。
- **双向 JSONL 桥**：玩家聊天（带触发词）→ `inbox.jsonl` → Claude；Claude 写 `outbox.jsonl` → bot 每秒轮询 → 以 OP 执行命令/广播。
- **FML3（1.20.1 Forge）握手**：通过 `autoVersionHooks` hook 覆盖 mod 列表，避免编码过的服务器 mod 列表破坏版本协商。
- **上线自动隐身 + 创造模式**，带看门狗：只要还没进创造模式就每 3 秒重发。
- **no-op 补丁**：把 `entity_metadata` / `declare_commands` / `block_action` 三个监听换掉，mod 实体 metadata 和分叉的命令树就不会崩掉连接流。
- **为 mod 服打造的健壮性**：2 秒地面心跳防「浮空太久」被踢、outbox 逐行容错、断线 5 秒自动重连、inbox 事件分级避免被普通聊天刷爆。
- **游戏内建建筑**：程序化 fill 生成器 + `.schematic` → 命令转换器 + 数据包 mcfunction 示例。

## Quick Start

```bash
# 1. 游戏开房（端口 51620，在线模式关）
# 2. 进世界后启动 bot
cd <本仓> && nohup node mc-god-bot.js > /tmp/mc-god-bot.log 2>&1 &
# 3. 确认上线
grep "上线" /tmp/mc-god-bot.log
# 4. kubejs 桥有改动时：游戏里 /kubejs reload server_scripts
```

依赖：`mineflayer` + `@tcortega/minecraft-protocol-forge@1.2.0`（FML3 握手）。

### forge-mods.json（FML3 握手必需）

bot 启动时读取 `/tmp/forge-mods.json`，用于 FML3 握手声明本地 mod 列表。格式：`[{"modid":"...","version":"..."}]`，从 mods 目录生成：

```bash
python3 -c "import json,os;print(json.dumps([{'modid':f.split('-')[0] if '-' in f else f.split('.')[0],'version':'1'} for f in os.listdir('mods') if f.endswith('.jar')]))" > /tmp/forge-mods.json
```

（实际环境从 mod 列表元数据生成更准，此命令用于快速重建占位。）

## 工作原理

### 架构

局域网开房模式**没有 RCON**，且该整合包的 kubejs6 类过滤器把 Java IO 封死（读不了文件、写不了文件）。游戏内命令和外部进程之间没有现成通道——所以用一个假玩家当通道：

```
玩家/朋友聊天(带触发词) → ludwiggod(OP) → inbox.jsonl → Claude
Claude 写 outbox.jsonl → bot 每秒轮询 → 以 OP 执行指令 → 游戏内生效
```

kubejs6 类过滤器封了 Java IO，文件读写全部移到 bot 进程（外部 Node 无此限制）。

| 组件 | 位置 | 职责 |
|---|---|---|
| bot | 本仓 `mc-god-bot.js` | mineflayer 连局域网端口，OP 身份收发消息、执行指令 |
| kubejs 桥 | 游戏目录 `kubejs/server_scripts/god-bridge.js`（不在本仓） | ludwiggod 上线自动 OP + 触发词回执（玩家喊「神」时游戏内提示） |
| 消息文件 | 游戏目录 `mc-bridge/inbox.jsonl` / `outbox.jsonl` | 双向通道 |
| 监视器 | Claude 会话内 Monitor | 盯 inbox.jsonl，收到事件即响应 |

### inbox 事件分级

避免 inbox 被普通聊天刷爆：

| 级别 | 内容 | 去向 |
|---|---|---|
| 触发 | 聊天含「神」/god/@claude | inbox（Claude 收到） |
| 重要 | 玩家加入 / 死亡 / 命令回执 | inbox |
| 忽略 | 普通聊天、系统广播、`Teleported` 反馈 | 仅 bot 本地日志 |

### 为什么要 override mod 列表？

1.20.1 (FML3) 服务器的 mod 列表在协议里是**编码过的**，mineflayer 的 `autoVersionForge` 解不出来。解法：复用其 hook 机制（保证时机正确），只覆盖数据源为本地列表 `/tmp/forge-mods.json`（从 mods 目录生成）。

### 为什么 bot 要隐身 + 创造模式？

- **隐身**：神的化身，对玩家不可见，不打扰游戏。
- **创造模式**：OP 执行 `give/setblock/fill` 等需要非生存权限。
- 上线自动设置，且带**看门狗**：只要还没进创造模式，每 3 秒重发（kubejs auto-op 可能滞后）。

## 使用 / 配置

### 常用指令（OP 执行）

Claude 通过 outbox 写 `/` 开头命令即可在游戏内执行：

```text
give <玩家> <物品> <数量>                                 发物品
effect give <玩家> <效果> <秒> <等级> true                 上 buff
gamerule keepInventory true                              死亡不掉落
execute at <玩家> run setblock ~ ~-1 ~ <方块>             在脚下放方块
execute as <玩家> at @s run kill @e[type=<实体>,distance=..40]  清怪
say <消息>                                                全服广播(Claude 说话)
scanchests                                                特殊命令:扫描玩家附近箱子→inbox
```

> `scanchests` 是 bot 内置的特殊命令（非游戏指令），用于定位黑曜石箱等模组存储方块。

### `mc-god-bot.js` 关键配置点

- `BRIDGE` —— `mc-bridge` 目录路径，存放 `inbox.jsonl` / `outbox.jsonl`（默认指向 Minecraft 应用支持中的 `mc-bridge` 文件夹）。
- `HP_MAP` —— 可选的自动补血；`null` 表示停用（仅发死亡通知，当前为停用状态）。

## 错误处理笔记（踩过的坑）

mod 服协议与原版差异极大，几乎所有逻辑都是为了对抗这些坑：

1. **mod 实体 metadata 不同 → 崩连接流。** `entity_metadata` / `declare_commands` / `block_action` 的 handler 依赖原版结构会炸（异常从包解析流抛出 → 30s 超时断线循环）。解法：在 `inject_allowed` 后把这三个监听全部换成 no-op。关键坑：`chat.js` 在登录成功后重新注册 `declare_commands` handler 会覆盖 no-op，所以 `login` 事件后还需再补一次。
2. **压缩层丢包 → 收不到 spawn → 踢循环。** 原版压缩层只处理每 TCP 块第一个包，Forge 合并包会丢包。解法：重写 `minecraft-protocol/src/transforms/compression.js` 为循环消费 + 二分找压缩流边界（运行时补丁）。
3. **地面心跳——防「浮空太久」被踢。** 物理关停且出生点在半空时，`allow-flight=false` 会在 ~4s 踢掉 bot。解法：每 2 秒手动上报 `onGround:true` 的 `position` 包，重置浮空计时。
4. **命令树（declare_commands）结构不同 → 静态解析会炸。** bot 不用 tab 补全，直接 no-op 掉整个解析路径。
5. **outbox 逐行容错。** `JSON.parse` 失败（坏行）只打印跳过，不中断整批；断线自动 5 秒重连（`end` → `setTimeout(start, 5000)`）。
6. **消息里带 `§` 颜色代码会被服务器当非法字符踢。** 广播（say）不要带颜色代码，用纯文本。
7. **传送反馈噪音。** `/tp` 反馈 `Teleported X to ...` 因玩家名可能含 "god" 误触发触发词——显式排除该正则，不进 inbox。

## 建筑生成（`buildings/`）

### 1. 程序化生成（`gen-shrine.js`）

直接用 fill 命令**组合成型**，适合小而规整的结构（神社、鸟居、塔楼）。

```
fill(-3,0,4,-3,7,4,'crimson_stem')    // 鸟居左柱
fill(-4,7,4,4,7,4,'crimson_planks')   // kasagi(笠木)
```

- 锚点 = 玩家所在位置（写死在脚本头，`BX/BZ/GROUND` 常量）
- 先清空建造体积 + 铺实心地基，吸收地形起伏
- 相对坐标 → 绝对坐标一次换算，命令直接可执行
- 适合 10~30 格尺度，几条 fill 拼一个结构

### 2. schematic 转换（`pagoda-convert.js` / `schematic-v1-convert.js`）

把现成的 `.schematic` 建筑文件转成 fill/setblock 命令序列，适合**大而精**的结构（完整塔楼、城堡）。

核心思路：
- 解析 NBT → 3D 网格（`cells[y][z][x] = blockname`）
- **盒聚合**：对连续同款方块贪心扩展最大盒子，`fill` 一条搞定一片（`cnt>=4` 用 fill，孤立块用 setblock），命令数从「每格一条」降到「每盒一条」
- 非满格方块（水/草/梯子/火把等）必须逐格 setblock，不能 fill 聚合
- 状态方块（楼梯朝向/木板轴）带 `[...]` 状态串，保证 fill 内状态一致

```bash
node pagoda-convert.js castle.schem 100 64 200 --stats   # 先看统计
node pagoda-convert.js castle.schem 100 64 200           # 生成命令 → /tmp/pagoda-fills.jsonl
```

`--stats` 会输出：尺寸、方块统计、最低/最高非空层、**疑似 1.21 专属块**（1.20.1 不存在会 setblock 报错）——放建筑前先查这个。

### 3. 数据包 mcfunction（`castlevania/`）

超大建筑拆成多个 `.mcfunction` 分块函数（`castle_p1~p3`），通过 `castle_main` 依次 `function lzmx:castle_pN` 调用。

> 注意：单函数命令上限 65536 条，超了必须拆；fill 高度也受世界高度限制。

## 目录结构

```
mc-god-bot.js              bot 主程序（本仓核心）
buildings/
  gen-shrine.js            和风神社+鸟居 程序化生成器
  pagoda-convert.js        Sponge v3 schematic → fill/setblock 命令
  schematic-v1-convert.js  老式 MCEdit .schematic → 现代块名命令
  castlevania/             恶魔城数据包（castle_main / castle_p1~p3.mcfunction）
README.md / README.zh-CN.md   中英双文档（英文 / 简体中文）
```

## 权限与安全

- 本仓**不含任何密钥/token**；bot 仅连本地局域网端口，无外网能力。
- bot 是 OP，**只应在局域网信任环境使用**，勿暴露公网。
- 死亡补血已停用（`HP_MAP` 为 null，仅发死亡通知），如需恢复按注释改回即可。

## License

MIT License — 见 [LICENSE](LICENSE)
