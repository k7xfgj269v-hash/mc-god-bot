# mc-god-bot — Minecraft「Claude 之神」假玩家通道

让 Claude 在游戏里当神:玩家说话,Claude 听到;Claude 发指令,游戏执行。基于 mineflayer 的假玩家,只做协议入口,不渲染不跑物理。

适用:Forge 1.20.1 局域网开房(集成服务器)联机,玩家端零改动。

## 架构

```
玩家/朋友聊天(带触发词) → ludwiggod(OP) → inbox.jsonl → Claude Monitor
Claude 写 outbox.jsonl → bot 每秒轮询 → 以 OP 执行指令/广播 → 游戏内生效
```

| 组件 | 说明 |
|---|---|
| bot | 本仓 `mc-god-bot.js`,mineflayer 连局域网端口,OP 身份收发消息、执行指令 |
| kubejs 桥 | 游戏目录 `kubejs/server_scripts/god-bridge.js`:ludwiggod 上线自动 OP + 触发词回执(不在本仓) |
| 消息文件 | 游戏目录 `mc-bridge/inbox.jsonl`(事件)/ `outbox.jsonl`(指令),双向通道 |
| 监视器 | Claude 会话内 Monitor 盯 inbox.jsonl |

## 启动

```bash
# 1. 游戏开房(端口 51620,在线模式关)
# 2. 进世界后启动 bot
cd <本仓> && nohup node mc-god-bot.js > /tmp/mc-god-bot.log 2>&1 &
# 3. 确认上线
grep "上线" /tmp/mc-god-bot.log
# 4. kubejs 桥有改动时:游戏里 /kubejs reload server_scripts
```

依赖:`mineflayer` + `@tcortega/minecraft-protocol-forge@1.2.0`(FML3 握手)。

## 事件分级(噪音控制)

| 级别 | 内容 | 去向 |
|---|---|---|
| 触发 | 聊天含「神」/god/@claude | inbox(Claude 收到) |
| 重要 | 玩家加入/死亡(自动补血)/指令回执/死亡原因 | inbox |
| 忽略 | 普通聊天、系统广播 | 仅 bot 本地日志 |

## 可执行指令(OP 权限示例)

```text
give <玩家> <物品> <数量>         发物品
attribute <玩家> minecraft:generic.max_health base set <n>   最大血量
effect give <玩家> <效果> <秒> <等级> true   上 buff
gamerule keepInventory true      死亡不掉落
execute at <玩家> run setblock ~ ~-1 ~ <方块>   放置方块
execute as <玩家> at @s run kill @e[type=#minecraft:monsters,distance=..40]   清怪
say <消息>                        全服广播(Claude 说话)
```

## 必读:运行时环境要求(本仓不包含)

Forge 服务器协议非原版,需对 node_modules 打三个补丁才能稳定连接,详见代码注释与 `05-Claude之神操作手册.md`(龙之冒险整合包文档):

1. `minecraft-data/.../pc/1.20/protocol.json`:declare_recipes / unlock_recipes / entity_metadata 三处**字段级** `restBuffer`(declare_commands 绝不能动)
2. `minecraft-protocol/src/transforms/compression.js`:重写为循环消费 + 二分找压缩流边界(原版只处理每 TCP 块第一个包,Forge 合并包会丢)
3. `mineflayer` 插件 handler:entity_metadata / declare_commands / block_action 换 no-op(mod 数据格式非原版会崩)

运行时依赖文件 `/tmp/forge-mods.json`:本地 mod 列表(`modid@version`,224 个),从 mods 目录生成,供 FML3 握手声明。

## 已踩的坑(为何长这样)

- 开房模式没有 RCON;kubejs6 类过滤器封死 Java IO → 通道移到外部 Node 进程
- FML3 握手需手动注入 mod 列表;ServerRegistry 快照解析越界 → restBuffer
- declare_commands 一旦 restBuffer 会破坏 set_compression 协商 → 永不 spawn
- chat.js 登录成功后才注册 declare_commands handler,覆盖 no-op → login 时再补一次
- 压缩层丢包 → bot 收不到 spawn → 30s 踢人循环(根因,已重写)
- mod 箱子 block_action 解析 facing 崩溃 → no-op
- 聊天消息带引号会被服务器踢 → say 广播别带引号

## 安全说明

- 本仓**不含任何密钥/token**;bot 仅连本地局域网端口,无外网能力
- `HP_MAP` 为玩家最大血量配置,按需修改
- 仅适用于局域网信任环境,OP 权限请勿暴露给公网
