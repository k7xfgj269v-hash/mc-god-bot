# mc-god-bot — Minecraft "Claude the God" bot channel

Let Claude be a god in-game: players speak, Claude hears; Claude issues commands, the game executes. A mineflayer bot acting as a **protocol-only entry point** — no rendering, no physics, no chunk loading. Pure message/command two-way bridge.

Target: Forge 1.20.1 LAN world (integrated server), zero changes on the player side.

> 中文版: 见 [README.md](README.md)

---

## 1. Architecture Rationale (why it looks like this)

### Core problem: where does the channel come from?

LAN worlds have **no RCON**, and this modpack's kubejs6 class filter **blocks Java IO** entirely (no file reads/writes). So there is no ready-made channel between "in-game commands" and an external process.

**Solution: use a fake player as the channel.** The bot (ludwiggod) logs in with OP and becomes a "real player" in the world:
- Player chat → bot receives → writes `inbox.jsonl`
- Claude writes `outbox.jsonl` → bot polls every second → executes commands/broadcasts as OP

```
Player chat (with trigger word) → ludwiggod(OP) → inbox.jsonl → Claude
Claude writes outbox.jsonl → bot polls each second → executes as OP → in-game effect
```

### Why override the mod list?

On 1.20.1 (FML3), the server's mod list is **encoded** in the protocol; mineflayer's `autoVersionForge` can't decode it. Fix: reuse its hook mechanism (to keep the timing correct) but override the data source with a local list `/tmp/forge-mods.json` (generated from the mods dir, 224 `modid@version` entries).

### Why invisible + creative mode?

- **Invisible**: the god's avatar — invisible to players, doesn't disturb gameplay.
- **Creative**: executing `give/setblock/fill` as OP requires non-survival permissions.
- Set on spawn with a **watchdog**: while not yet in creative, re-apply every 3s (kubejs auto-op may lag).

### Why event filtering?

To keep inbox from being flooded by casual chat. Only trigger words (神/god/@claude) and important events (join/death/command receipt) go to inbox; ordinary chat stays in local logs.

---

## 2. Layout

```
mc-god-bot.js              bot main program (core of this repo)
buildings/
  gen-shrine.js            procedural Japanese shrine + torii generator
  pagoda-convert.js        Sponge v3 schematic → fill/setblock commands
  schematic-v1-convert.js  legacy MCEdit .schematic → modern block-name commands
  castlevania/             Castlevania datapack (castle_p1~p3.mcfunction example)
README.md / README_EN.md   bilingual docs
```

---

## 3. Startup

```bash
# 1. Open LAN world (port 51620, online-mode off)
# 2. Start the bot after entering the world
cd <repo> && nohup node mc-god-bot.js > /tmp/mc-god-bot.log 2>&1 &
# 3. Confirm online
grep "上线" /tmp/mc-god-bot.log
# 4. After changing the kubejs bridge: in-game /kubejs reload server_scripts
```

Deps: `mineflayer` + `@tcortega/minecraft-protocol-forge@1.2.0` (FML3 handshake).

---

## 4. Error Handling (traps hit, why written this way)

This is the real value of the project — **the modded-server protocol diverges hugely from vanilla**, and almost every piece of logic exists to fight one of these traps:

### 1. Mod entity metadata differs → kills the connection stream

Mod entities (maids etc.) use a different metadata format; the library handlers rely on vanilla structure (`entities.js fromEntries`, `chat.js`'s `declare_commands` slice indexing) and crash. **An exception thrown from the packet-parse stream destroys the connection → 30s timeout disconnect loop.**

Fix: after `inject_allowed` (when mineflayer plugins have registered), replace the `entity_metadata` / `declare_commands` / `block_action` listeners with no-ops — the bot needs no entity data / command tree / chest open-close.

> Key trap: `chat.js` registers its `declare_commands` handler only after login success (the `success` packet), **re-overwriting the no-op** → must re-patch after the `login` event.

### 2. Compression layer drops packets → no spawn → kick loop

The vanilla compression transform only handles the first packet of each TCP chunk; Forge merges packets, so packets get lost → bot never receives spawn → 30s kick loop.

Fix: **rewrite `minecraft-protocol/src/transforms/compression.js`** to consume in a loop and find compressed-stream boundaries via binary search (runtime patch, see protocol doc outside this repo).

### 3. Ground heartbeat — avoiding "flying too long" kicks

With physics off and spawn in mid-air, `allow-flight=false` kicks the bot for "flying too long" in ~4s (another root cause of the disconnect loop).

Fix: every 2s, manually write a `position` packet with `onGround:true`, resetting the flight timer until OP and a normal position are secured.

### 4. Command tree (declare_commands) differs → static parsing crashes

The modded command tree differs from vanilla, but the bot never needs tab-completion — **no-op the whole parse path**.

### 5. Per-line outbox tolerance

A failing `JSON.parse` (bad line) is logged and skipped without breaking the batch; a single command failing doesn't affect the rest. Auto-reconnect after 5s on disconnect (`end` → `setTimeout(start, 5000)`).

### 6. `§` color codes in messages get kicked as illegal characters

Broadcasts (`say`) **must not contain color codes** — use plain text.

### 7. Teleport feedback noise

`/tp` feedback `Teleported X to ...` can falsely trigger the trigger word when a player name contains "god" — explicitly exclude that regex from inbox.

---

## 5. Building Generation (buildings/)

Three paths, chosen by scenario:

### 1. Procedural generation (gen-shrine.js)

Directly **compose shapes with fill commands** — fits small, regular structures (shrines, torii, pagodas).

```
fill(-3,0,4,-3,7,4,'crimson_stem')    // torii left pillar
fill(-4,7,4,4,7,4,'crimson_planks')   // kasagi (top rail)
```

Features:
- Anchor = player's position (hardcoded at script head via `BX/BZ/GROUND` constants)
- Clear the build volume + lay a solid foundation first, absorbing terrain variation
- Relative → absolute coordinates converted once; commands runnable as-is
- Fits the 10–30 block scale; a few fills assemble one structure

### 2. Schematic conversion (pagoda-convert.js / schematic-v1-convert.js)

Turn existing `.schematic` building files into fill/setblock command sequences — fits **large, detailed** structures (full pagodas, castles).

Core idea:
- Parse NBT → 3D grid (`cells[y][z][x] = blockname`)
- **Box aggregation**: greedily grow the largest box of identical blocks; one `fill` covers a region (`cnt>=4` → fill, isolated blocks → setblock), cutting commands from "one per block" to "one per box"
- Non-full blocks (water/grass/ladder/torch etc.) must be setblock individually — cannot fill-aggregate
- Stateful blocks (stair facing/log axis) carry `[...]` state strings, ensuring consistent state inside a fill

```
node pagoda-convert.js castle.schem 100 64 200 --stats   # stats first
node pagoda-convert.js castle.schem 100 64 200           # generate commands → /tmp/pagoda-fills.jsonl
```

`--stats` outputs: dimensions, block stats, lowest/highest non-empty layer, and **suspected 1.21-only blocks** (don't exist on 1.20.1 → setblock error) — check this before placing a build.

### 3. Datapack mcfunction (castlevania/)

Very large builds are split into multiple `.mcfunction` chunk functions (`castle_p1~p3`), invoked in sequence via `castle_main` → `function lzmx:castle_pN`.

Note: single-function command limit is 65536 — must split beyond that; fill height is also bounded by world height.

---

## 6. Permissions & Safety

- This repo **contains no keys/tokens**; the bot only connects to a local LAN port, no external network capability
- The bot is OP — **only use in a trusted LAN environment**, never expose to public networks
- Auto health-restore is disabled (`HP_MAP` is null, death notification only); follow the code comment to re-enable if needed
