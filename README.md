# mc-god-bot — Minecraft "Claude the God" bot channel

Let Claude be a god in-game: players speak, Claude hears; Claude issues commands, the game executes. A mineflayer bot acting as a **protocol-only entry point** — no rendering, no physics, no chunk loading. Pure message/command two-way bridge.

Target: Forge 1.20.1 LAN world (integrated server), zero changes on the player side.

> [中文版 README](README.zh-CN.md)

## Features

- **Fake-player channel**: `ludwiggod` logs in as an OP player and becomes a real player in the world, bridging in-game chat/commands to an external process — no RCON needed.
- **Two-way JSONL bridge**: player chat (with trigger word) → `inbox.jsonl` → Claude; Claude writes `outbox.jsonl` → bot polls every second → executes commands/broadcasts as OP.
- **FML3 (1.20.1 Forge) handshake**: overrides the mod list via the `autoVersionHooks` hook so the encoded server mod list can't break version negotiation.
- **Invisible + creative on spawn** with a watchdog that re-applies until creative is secured.
- **No-op patching** of `entity_metadata` / `declare_commands` / `block_action`, so modded-entity metadata and the divergent command tree can't crash the connection.
- **Robustness built for modded servers**: 2s ground heartbeat against flight-timeout kicks, per-line outbox tolerance, 5s auto-reconnect, and inbox event filtering to avoid chat flood.
- **In-game building**: procedural `fill` generators plus `.schematic` → command converters and a datapack mcfunction example.

## Quick Start

```bash
# 1. Open a LAN world (port 51620, online-mode off)
# 2. Start the bot after entering the world
cd <repo> && nohup node mc-god-bot.js > /tmp/mc-god-bot.log 2>&1 &
# 3. Confirm online
grep "上线" /tmp/mc-god-bot.log
# 4. After changing the kubejs bridge: in-game /kubejs reload server_scripts
```

Dependencies: `mineflayer` + `@tcortega/minecraft-protocol-forge@1.2.0` (FML3 handshake).

### forge-mods.json (required for the FML3 handshake)

The bot reads `/tmp/forge-mods.json` at startup to declare the local mod list during the FML3 handshake. Format: `[{"modid":"...","version":"..."}]`, generated from the mods dir:

```bash
python3 -c "import json,os;print(json.dumps([{'modid':f.split('-')[0] if '-' in f else f.split('.')[0],'version':'1'} for f in os.listdir('mods') if f.endswith('.jar')]))" > /tmp/forge-mods.json
```

(Real environments generate it from mod metadata for accuracy; this quick command rebuilds a placeholder.)

## How it works

### Architecture

LAN worlds have **no RCON**, and this modpack's kubejs6 class filter **blocks Java IO** entirely (no file reads/writes). So there is no ready-made channel between "in-game commands" and an external process — a fake player is the channel:

```
Player chat (with trigger word) → ludwiggod(OP) → inbox.jsonl → Claude
Claude writes outbox.jsonl → bot polls each second → executes as OP → in-game effect
```

The kubejs6 class filter blocks Java IO, so all file I/O lives in the bot process (external Node, no such limit).

| Component | Location | Role |
|---|---|---|
| bot | `mc-god-bot.js` (this repo) | mineflayer connecting to the LAN port, sending/receiving messages and running commands as OP |
| kubejs bridge | game dir `kubejs/server_scripts/god-bridge.js` (not in this repo) | auto-OP ludwiggod on login + trigger-word ack (in-game toast when a player calls "god") |
| message files | game dir `mc-bridge/inbox.jsonl` / `outbox.jsonl` | two-way channel |
| monitor | Claude session Monitor | watches inbox.jsonl, responds on events |

### Inbox event filtering

To keep inbox from being flooded by casual chat:

| Level | Content | Destination |
|---|---|---|
| trigger | chat containing 神/god/@claude | inbox (Claude receives) |
| important | player join / death / command receipt | inbox |
| ignored | ordinary chat, system broadcasts, `Teleported` feedback | bot local log only |

### Why override the mod list?

On 1.20.1 (FML3), the server's mod list is **encoded** in the protocol; mineflayer's `autoVersionForge` can't decode it. Fix: reuse its hook mechanism (to keep the timing correct) but override the data source with a local list `/tmp/forge-mods.json` (generated from the mods dir).

### Why invisible + creative mode?

- **Invisible**: the god's avatar — invisible to players, doesn't disturb gameplay.
- **Creative**: executing `give/setblock/fill` as OP requires non-survival permissions.
- Set on spawn with a **watchdog**: while not yet in creative, re-apply every 3s (kubejs auto-op may lag).

## Usage / Configuration

### Common commands (run as OP)

Claude writes `/`-prefixed commands via outbox to execute in-game:

```text
give <player> <item> <count>                                  give items
effect give <player> <effect> <seconds> <level> true          apply buff
gamerule keepInventory true                                   keep inventory on death
execute at <player> run setblock ~ ~-1 ~ <block>              place a block at feet
execute as <player> at @s run kill @e[type=<entity>,distance=..40]   clear mobs
say <message>                                                 broadcast (Claude speaks)
scanchests                                                    special: scan nearby chests → inbox
```

> `scanchests` is a built-in special command (not a game command) for locating mod storage blocks like obsidian chests.

### Key configuration points in `mc-god-bot.js`

- `BRIDGE` — path to the `mc-bridge` directory holding `inbox.jsonl` / `outbox.jsonl` (defaults to the Minecraft application-support `mc-bridge` folder).
- `HP_MAP` — optional auto-health-restore; `null` disables it (death notification only; currently disabled).

## Error handling notes (traps hit)

The modded-server protocol diverges hugely from vanilla, and almost every piece of logic exists to fight one of these traps:

1. **Mod entity metadata differs → connection-stream crash.** `entity_metadata` / `declare_commands` / `block_action` handlers rely on vanilla structure and crash (destroying the connection stream → 30s timeout disconnect loop). Fix: replace those three listeners with no-ops after `inject_allowed`. Key trap: `chat.js` re-registers its `declare_commands` handler after login success and overwrites the no-op, so it must be re-patched after the `login` event.
2. **Compression layer drops packets → no spawn → kick loop.** The vanilla compression transform only handles the first packet of each TCP chunk; Forge merges packets, so packets get lost. Fix: rewrite `minecraft-protocol/src/transforms/compression.js` to consume in a loop and find compressed-stream boundaries via binary search (runtime patch).
3. **Ground heartbeat — avoiding "flying too long" kicks.** With physics off and spawn in mid-air, `allow-flight=false` kicks the bot in ~4s. Fix: every 2s, manually write a `position` packet with `onGround:true`, resetting the flight timer.
4. **Command tree (`declare_commands`) differs → static parsing crashes.** The bot never needs tab-completion, so the parse path is no-oped.
5. **Per-line outbox tolerance.** A failing `JSON.parse` is logged and skipped without breaking the batch; reconnect after 5s on disconnect (`end` → `setTimeout(start, 5000)`).
6. **`§` color codes get kicked as illegal characters.** Broadcasts (`say`) must not contain color codes — use plain text.
7. **Teleport feedback noise.** `/tp` feedback `Teleported X to ...` can falsely trigger the trigger word when a player name contains "god" — explicitly excluded from inbox.

## Building generation (`buildings/`)

### 1. Procedural generation (`gen-shrine.js`)

Directly **compose shapes with fill commands** — fits small, regular structures (shrines, torii, pagodas).

```
fill(-3,0,4,-3,7,4,'crimson_stem')    // torii left pillar
fill(-4,7,4,4,7,4,'crimson_planks')   // kasagi (top rail)
```

- Anchor = player's position (hardcoded at script head via `BX/BZ/GROUND` constants)
- Clear the build volume + lay a solid foundation first, absorbing terrain variation
- Relative → absolute coordinates converted once; commands runnable as-is
- Fits the 10–30 block scale; a few fills assemble one structure

### 2. Schematic conversion (`pagoda-convert.js` / `schematic-v1-convert.js`)

Turn existing `.schematic` building files into fill/setblock command sequences — fits **large, detailed** structures (full pagodas, castles).

Core idea:
- Parse NBT → 3D grid (`cells[y][z][x] = blockname`)
- **Box aggregation**: greedily grow the largest box of identical blocks; one `fill` covers a region (`cnt>=4` → fill, isolated blocks → setblock), cutting commands from "one per block" to "one per box"
- Non-full blocks (water/grass/ladder/torch etc.) must be setblock individually — cannot fill-aggregate
- Stateful blocks (stair facing/log axis) carry `[...]` state strings, ensuring consistent state inside a fill

```bash
node pagoda-convert.js castle.schem 100 64 200 --stats   # stats first
node pagoda-convert.js castle.schem 100 64 200           # generate commands → /tmp/pagoda-fills.jsonl
```

`--stats` outputs: dimensions, block stats, lowest/highest non-empty layer, and **suspected 1.21-only blocks** (don't exist on 1.20.1 → setblock error) — check this before placing a build.

### 3. Datapack mcfunction (`castlevania/`)

Very large builds are split into multiple `.mcfunction` chunk functions (`castle_p1~p3`), invoked in sequence via `castle_main` → `function lzmx:castle_pN`.

> Note: single-function command limit is 65536 — must split beyond that; fill height is also bounded by world height.

## Project Structure

```
mc-god-bot.js              bot main program (core of this repo)
buildings/
  gen-shrine.js            procedural Japanese shrine + torii generator
  pagoda-convert.js        Sponge v3 schematic → fill/setblock commands
  schematic-v1-convert.js  legacy MCEdit .schematic → modern block-name commands
  castlevania/             Castlevania datapack (castle_main / castle_p1~p3.mcfunction)
README.md / README.zh-CN.md   bilingual docs (EN / 简体中文)
```

## Permissions & Safety

- This repo **contains no keys/tokens**; the bot only connects to a local LAN port, no external network capability.
- The bot is OP — **only use in a trusted LAN environment**, never expose to public networks.
- Auto health-restore is disabled (`HP_MAP` is null, death notification only); follow the code comment to re-enable if needed.

## License

MIT License — see [LICENSE](LICENSE)
