# mc-god-bot — Minecraft「Claude 之神」假玩家通道

让 Claude 在游戏里当神：玩家说话，Claude 听到；Claude 发指令，游戏执行。基于 mineflayer 的假玩家，**只做协议入口**——不渲染、不跑物理、不加载区块，纯消息/命令双向桥。

适用：Forge 1.20.1 局域网开房（集成服务器）联机，玩家端零改动。

> English: see [README_EN.md](README_EN.md)

---

## 一、架构思路（为什么长这样）

### 核心问题：通道从哪来？

局域网开房模式**没有 RCON**，且该整合包的 kubejs6 类过滤器把 Java IO 封死（读不了文件、写不了文件）。也就是说「游戏内命令」和「外部进程」之间没有现成通道。

**解法：用一个假玩家当通道。** bot（ludwiggod）以 OP 身份登录进世界，成为服务器里的一个「真实玩家」：
- 玩家聊天 → bot 收到 → 写 `inbox.jsonl`
- Claude 写 `outbox.jsonl` → bot 每秒轮询 → 以 OP 身份执行命令/广播

```
玩家/朋友聊天(带触发词) → ludwiggod(OP) → inbox.jsonl → Claude
Claude 写 outbox.jsonl → bot 每秒轮询 → 以 OP 执行指令 → 游戏内生效
```

### 为什么要 override mod 列表？

1.20.1 (FML3) 服务器的 mod 列表在协议里是**编码过的**，mineflayer 的 `autoVersionForge` 解不出来。解法：复用其 hook 机制（保证时机正确），只覆盖数据源为本地列表 `/tmp/forge-mods.json`（从 mods 目录生成，`modid@version` 224 个）。

### 为什么 bot 要隐身 + 创造模式？

- **隐身**：神的化身，对玩家不可见，不打扰游戏。
- **创造模式**：OP 执行 `give/setblock/fill` 等需要非生存权限。
- 上线自动设置，且带**看门狗**：只要还没进创造模式，每 3 秒重发（kubejs auto-op 可能滞后）。

### 为什么事件分级？

避免 inbox 被普通聊天刷爆。只把「触发词」（神/god/@claude）和重要事件（加入/死亡/命令回执）进 inbox，普通聊天只进本地日志。

---

## 二、目录结构

```
mc-god-bot.js              bot 主程序（本仓核心）
buildings/
  gen-shrine.js            和风神社+鸟居 程序化生成器
  pagoda-convert.js        Sponge v3 schematic → fill/setblock 命令
  schematic-v1-convert.js  老式 MCEdit .schematic → 现代块名命令
  castlevania/             恶魔城数据包（castle_p1~p3.mcfunction 示例）
README.md / README_EN.md   中英双文档
```

---

## 三、启动

```bash
# 1. 游戏开房（端口 51620，在线模式关）
# 2. 进世界后启动 bot
cd <本仓> && nohup node mc-god-bot.js > /tmp/mc-god-bot.log 2>&1 &
# 3. 确认上线
grep "上线" /tmp/mc-god-bot.log
# 4. kubejs 桥有改动时：游戏里 /kubejs reload server_scripts
```

依赖：`mineflayer` + `@tcortega/minecraft-protocol-forge@1.2.0`（FML3 握手）。

---

## 四、错误处理（踩过的坑，为何这样写）

这是本项目的核心价值——**mod 服协议与原版差异极大**，几乎所有逻辑都是为了对抗这些坑：

### 1. mod 实体 metadata 与原版格式不同 → 崩连接流

mod 实体（女仆等）的 metadata 格式不同，库内 handler 依赖原版结构（`entities.js fromEntries`、`chat.js` 的 `declare_commands` 切片索引）会炸。**一旦异常从包解析流抛出，会毁掉连接流 → 30s 超时断线循环。**

解法：在 `inject_allowed`（mineflayer 插件注册完成时机）后，把 `entity_metadata` / `declare_commands` / `block_action` 三个监听全部换成 no-op——bot 不需要实体数据/命令树/箱子开合。

> 关键坑：`chat.js` 在登录成功（`success` 包）后才注册 `declare_commands` handler，会**重新覆盖 no-op** → 必须在 `login` 事件后再补一次。

### 2. 压缩层丢包 → 收不到 spawn → 被踢循环

Forge 合并包原版压缩层只处理每 TCP 块第一个包，会丢包 → bot 收不到 spawn → 30s 踢人循环。

解法：**重写 `minecraft-protocol/src/transforms/compression.js`** 为循环消费 + 二分找压缩流边界。（运行时补丁，见仓库外协议文档）

### 3. 地面心跳——防「浮空太久」被踢

物理关停且出生点在半空时，服务器 `allow-flight=false` 会在 ~4s 把 bot 当「浮空太久」踢掉（断线循环的另一个根因）。

解法：每 2 秒手动上报 `onGround:true` 的 `position` 包，重置浮空计时，撑到拿到 OP 和正常位置。

### 4. 命令树（declare_commands）结构不同 → 静态解析会炸

mod 服命令树与 vanilla 结构不同，但 bot 根本不用 tab 补全——**直接 no-op，省掉整个解析路径**。

### 5. outbox 逐行容错

`JSON.parse` 失败（坏行）只打印跳过，不中断整批；单条命令执行失败也不影响后续。断线自动 5 秒重连（`end` → `setTimeout(start, 5000)`）。

### 6. 消息里带 `§` 颜色代码会被服务器当非法字符踢

广播（say）**不要带颜色代码**，用纯文本。

### 7. 传送反馈噪音

`/tp` 的反馈 `Teleported X to ...` 因玩家名可能含 "god" 误触发触发词——显式排除该正则，不进 inbox。

---

## 五、建筑生成（buildings/）

Claude 在游戏里建建筑有三种路径，按场景选：

### 1. 程序化生成（gen-shrine.js）

直接用 fill 命令**组合成型**，适合小而规整的结构（神社、鸟居、塔楼）。

```
fill(-3,0,4,-3,7,4,'crimson_stem')    // 鸟居左柱
fill(-4,7,4,4,7,4,'crimson_planks')   // kasagi(笠木)
```

特点：
- 锚点 = 玩家所在位置（写死在脚本头，`BX/BZ/GROUND` 常量）
- 先清空建造体积 + 铺实心地基，吸收地形起伏
- 相对坐标 → 绝对坐标一次换算，命令直接可执行
- 适合 10~30 格尺度，几条 fill 拼一个结构

### 2. schematic 转换（pagoda-convert.js / schematic-v1-convert.js）

把现成的 `.schematic` 建筑文件转成 fill/setblock 命令序列，适合**大而精**的结构（完整塔楼、城堡）。

核心思路：
- 解析 NBT → 3D 网格（`cells[y][z][x] = blockname`）
- **盒聚合**：对连续同款方块贪心扩展最大盒子，`fill` 一条搞定一片（`cnt>=4` 用 fill，孤立块用 setblock），命令数从「每格一条」降到「每盒一条」
- 非满格方块（水/草/梯子/火把等）必须逐格 setblock，不能 fill 聚合
- 状态方块（楼梯朝向/木板轴）带 `[...]` 状态串，保证 fill 内状态一致

```
node pagoda-convert.js castle.schem 100 64 200 --stats   # 先看统计
node pagoda-convert.js castle.schem 100 64 200           # 生成命令 → /tmp/pagoda-fills.jsonl
```

`--stats` 会输出：尺寸、方块统计、最低/最高非空层、**疑似 1.21 专属块**（1.20.1 不存在会 setblock 报错）——放建筑前先查这个。

### 3. 数据包 mcfunction（castlevania/）

超大建筑拆成多个 `.mcfunction` 分块函数（`castle_p1~p3`），通过 `castle_main` 依次 `function lzmx:castle_pN` 调用。

注意：单函数命令上限 65536 条，超了必须拆；fill 高度也受世界高度限制。

---

## 六、权限与安全

- 本仓**不含任何密钥/token**；bot 仅连本地局域网端口，无外网能力
- bot 是 OP，**只应在局域网信任环境使用**，勿暴露公网
- 死亡补血已停用（`HP_MAP` 为 null，仅发死亡通知），如需恢复按注释改回即可
