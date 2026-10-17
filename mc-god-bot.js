// mc-god-bot.js — Claude 之神假玩家通道
// 以 ludwiggod 登录局域网世界(51620),OP 身份双向桥:
//   玩家聊天/广播/加入 → inbox.jsonl(Claude 读)
//   Claude 写 outbox.jsonl → 每秒轮询 → 以 OP 执行命令/广播
const mineflayer = require('mineflayer');
const forgeHandshake3 = require('@tcortega/minecraft-protocol-forge/src/client/forgeHandshake3');
// 1.20.1(FML3)服务器的 mod 列表被编码,autoVersionForge 解不出来 → 用本地列表
// 做法:复用其 hook 机制(正确时机),仅覆盖 mods 数据源
const fs = require('fs');
const BRIDGE = process.env.HOME + '/Library/Application Support/minecraft/mc-bridge';
const INBOX = BRIDGE + '/inbox.jsonl';
const OUTBOX = BRIDGE + '/outbox.jsonl';
let currentBot = null;   // 当前连接实例, 供模块级 outbox 轮询取用(重连后自动切到新连接)
const HP_MAP = { 'ludwigxu': null };   // 玩家 -> 死亡后自动补的最大血量;null=不自动调(仅死亡通知,2026-08-16 停用)
// bot 声称的 mod 列表(FML3 格式: "modid@version";含 minecraft/forge 本体)
const FORGE_MODS = JSON.parse(fs.readFileSync(__dirname + '/forge-mods.json', 'utf8'))
  .map(m => m.modid + '@' + m.version)
  .concat(['minecraft@1.20.1', 'forge@47.3.22']);

// 死亡原因匹配:玩家死亡时服务器广播原文含这些词 → 进 inbox 通知 Claude
const DEATH_CAUSES = /died|was slain|was shot|was blown|burned to death|drowned|suffocated|starved to death|fell from|fell off|hit the ground|was impaled|was killed|was pricked|blew up/;

function log(type, player, msg, extra) {
  try {
    // inbox 只增不减 → 超 8MB 改名归档(保留数据, 不删), 下次写新文件
    const st = fs.statSync(INBOX, { throwIfNoEntry: false });
    if (st && st.size > 8 * 1024 * 1024) {
      const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\..+/, '');
      fs.renameSync(INBOX, INBOX.replace(/\.jsonl$/, '-' + ts + '.jsonl'));
    }
    const line = JSON.stringify({ t: type, p: String(player || ''), m: String(msg || ''), x: String(extra || ''), ts: Date.now() });
    fs.appendFileSync(INBOX, line + '\n');
  } catch (e) {}
}

// scanchests 特殊指令:扫描 ludwigxu 附近的存储方块(箱子/木桶/潜影盒),把位置发到 inbox
function handleScanChests(bot) {
  const t = bot.players['ludwigxu'];
  const p = t && t.entity ? t.entity.position : null;
  if (!p) { console.log('[scan] ludwigxu 不在线'); return; }
  // 打玩家当前位置 + 附近 3 格内所有非空气块的原始名,定位黑曜石箱子真实注册名
  const here = p.floored();
  console.log('[scan] ludwigxu @ ' + here.x + ',' + here.y + ',' + here.z + ' yaw=' + (t.entity.yaw).toFixed(1));
  const nearby = bot.findBlocks({ matching: b => b.name !== 'minecraft:air', maxDistance: 6, point: p, count: 128 });
  // mineflayer 不认识 mod 块 → name 全 undefined;改用 type id(数字)识别,mod 块 id 远大于原版
  const byType = {};
  nearby.forEach(b => { byType[b.type] = (byType[b.type] || 0) + 1; });
  console.log('[scan] nearby types:', Object.entries(byType).map(([t, c]) => '#' + t + 'x' + c).join(' '));
  const names = {};
  nearby.forEach(b => { names[b.name] = (names[b.name] || 0) + 1; });
  console.log('[scan] nearby blocks:', Object.entries(names).map(([n, c]) => n + 'x' + c).join(' '));
  const found = bot.findBlocks({
    // 原版 chest/barrel/shulker + 模组箱子(ironchest 黑曜石箱等, name 是 ironchest:obsidian_chest 这种完整注册名)
    matching: b => /(chest|barrel|shulker)/i.test(b.name),
    maxDistance: 10,
    point: p,
    count: 64,
  });
  const list = found.map(b => b.name + ' ' + b.position.x + ',' + b.position.y + ',' + b.position.z);
  log('exec', 'god', 'scanchests: ' + (list.length ? list.join(' | ') : '无'), '');
  console.log('[scan] chests:', list.length ? list.join(' | ') : '无');
}

process.on('uncaughtException', (e) => {
  console.error('[uncaught]', e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n') : e);
});
process.on('unhandledRejection', (e) => console.error('[unhandled]', e));

function start() {
  const bot = mineflayer.createBot({
    host: '127.0.0.1', port: 51620,
    username: 'ludwiggod', auth: 'offline', hideErrors: true,   // 原生压掉解析噪音(见 patches/README),真错误仍会报
    version: false,                 // 触发 minecraft-protocol 自动版本协商(hook 时机)
    physicsEnabled: false,          // 只做协议入口,不跑物理模拟
  });
  currentBot = bot;
  if (!bot._client.autoVersionHooks) bot._client.autoVersionHooks = [];
  bot._client.autoVersionHooks.push(function (response, client, options) {
    if (!response.forgeData || !response.forgeData.d) return;   // 仅 FML3
    forgeHandshake3(client, { forgeMods: FORGE_MODS });
  });
  // mod 实体(女仆等)metadata 格式与原版不同,协议层已改 restBuffer 吞掉;
  // mineflayer 插件在 inject_allowed 事件(loader.js setTimeout 0)才注册 handler,
  // createBot 返回时还没注册 → 等注入完成后再把 metadata 监听换成 no-op(bot 不需要实体数据)
  bot.on('inject_allowed', () => {
    // mod 实体 metadata / 命令树结构都与原版不同,协议层已改 restBuffer;
    // 对应库内 handler 依赖原版结构(entities.js fromEntries、chat.js 的 declare_commands 切片索引)会炸 → 全部换 no-op
    bot._client.removeAllListeners('entity_metadata');
    bot._client.on('entity_metadata', () => {});
    bot._client.removeAllListeners('declare_commands');
    bot._client.on('declare_commands', () => {});
    // mod 箱子(女仆/深渊等)的 block_action 里 metadata 解析不出 facing → Object.values(undefined) 崩,
    // 异常从包解析流抛出会毁掉连接流 → 30s 超时断线循环;bot 不需要箱子开合,no-op
    bot._client.removeAllListeners('block_action');
    bot._client.on('block_action', () => {});
    console.log('[diag] patched after inject: entity_metadata/declare_commands/block_action listeners:',
      bot._client.listenerCount('entity_metadata'), bot._client.listenerCount('declare_commands'), bot._client.listenerCount('block_action'));
  });
  // chat.js(签名聊天插件)在登录成功(success 包)后才注册 declare_commands handler,
  // 会重新覆盖 no-op → 登录后再替换一次
  bot.on('login', () => {
    bot._client.removeAllListeners('declare_commands');
    bot._client.on('declare_commands', () => {});
    console.log('[diag] declare_commands re-patched after login');
  });

  // 神的化身设置:旁观者模式(无敌不可见) + 隐身, bot 连接级复用
  const setGod = () => {
    try {
      bot.chat('/gamemode spectator ludwiggod');
      bot.chat('/effect give ludwiggod minecraft:invisibility 999999 0 true');
      console.log('[god] spectator + invisible (attempt)');
    } catch (e) {}
  };
  bot.on('spawn', () => {
    try { bot.setViewDistance(5); } catch (e) {}   // 视距5:约80格半径,足够大范围 /fill 所需区块(原为2,2026-09-03改)
    if (bot._godInit) {
      // 重生/二次 spawn: 只需重设状态(spectator+隐身), 看门狗已注册
      setGod();
      log('bot', 'ludwiggod', 're-spawned');
      console.log('[bot] 重生上线');
      return;
    }
    bot._godInit = true;
    // 上线自动设置:旁观者模式 + 隐身(旁观者天然无敌不可见, 不会被玩家杀死)
    setGod();
    // 看门狗:只要还没进旁观者模式,每 3 秒重发(kubejs auto-op 可能滞后)
    const wd = setInterval(() => {
      try {
        if (bot.game && bot.game.gameMode !== 'spectator') setGod();
      } catch (e) {}
    }, 3000);
    // 地面心跳:物理关停且出生点在半空时,服务器 allow-flight=false 会在 ~4s 把 bot
    // 当"浮空太久"踢掉(loop 根源)。周期性上报 onGround=true 重置浮空计时,撑到拿到 OP。
    const hb = setInterval(() => {
      try {
        const e = bot.entity;
        if (e && e.position) {
          bot._client.write('position', {
            x: e.position.x, y: e.position.y, z: e.position.z,
            yaw: e.yaw || 0, pitch: e.pitch || 0, onGround: true,
          });
        }
      } catch (e) {}
    }, 2000);
    bot.once('end', () => { clearInterval(wd); clearInterval(hb); bot._godInit = false; });
    log('bot', 'ludwiggod', 'spawned');
    console.log('[bot] 上线');
  });
  // 自动重生: 死亡后立即 respawn(保持连接, 不走断线重连)
  bot.on('death', () => {
    console.log('[bot] 死亡, 自动重生');
    log('bot', 'ludwiggod', 'death, auto-respawn');
    try { bot.respawn(); } catch (e) {}
  });
  bot.on('respawn', () => {
    console.log('[bot] 重生完成, 恢复状态');
    setGod();
  });

  bot.on('chat', (username, message) => {
    if (username === 'ludwiggod') return;
    // 发给神的信息全收:ludwigxu/PIGGOD 是仅有的两名玩家, 真人聊的每一句都进 inbox,
    // 让 Claude 连追问(「然后呢」「不够」这类不带触发词的话)也能收到;
    // 系统/命令回显噪音(切模式/commands.*/传送/进度/备份)继续不进 inbox, 避免刷屏
    const CHAT_NOISE = /^(set own game mode to |teleported |commands\.|backup |.* joined the game|.* has (made|completed|reached|achieved) )/i;
    const lower = message.toLowerCase();
    const isTrigger = lower.indexOf('神') !== -1 || lower.indexOf('god') !== -1 || lower.indexOf('@claude') !== -1;
    const isPlayer = username === 'ludwigxu' || username === 'PIGGOD';
    if (CHAT_NOISE.test(message)) {
      // 噪音优先于触发词:传送回显里含 PIGGOD 的 "god" 会误触发, 一律不进 inbox
      console.log('[chat-skip]', username + ':', message);
    } else if (isPlayer || isTrigger) {
      log('chat', username, message);
      console.log('[chat]', username + ':', message);
    } else {
      console.log('[chat-skip]', username + ':', message);
    }
  });

  bot.on('message', (json) => {
    try {
      let text = json.toString();
      text = text.replace(/§[0-9a-fk-or]/g, '');
      // 系统广播不写 inbox(噪音),仅本地日志;死亡补血逻辑独立处理
      if (text) { console.log('[msg]', text); }
      // 死亡事件进 inbox(Claude 诊断);自动补血已停(HP_MAP 值为 null 不调),只保留通知
      for (const name of Object.keys(HP_MAP)) {
        if (text.includes(name) && DEATH_CAUSES.test(text)) {
          log('death', name, text);   // 死亡原因原文进 inbox,方便 Claude 诊断
          const hp = HP_MAP[name];
          if (hp) {
            setTimeout(() => {
              bot.chat('/attribute ' + name + ' minecraft:generic.max_health base set ' + hp);
              log('revive', name, 'hp restored');
              console.log('[revive]', name, 'hp ->', hp);
            }, 3000);
          }
        }
      }
    } catch (e) {}
  });

  bot.on('playerJoined', (p) => {
    if (p.username !== 'ludwiggod') { log('join', p.username, 'joined'); console.log('[join]', p.username); }
  });

  bot.on('kicked', (r) => {
    console.log('[bot] 被踢:', r);
    log('bot', 'ludwiggod', 'kicked: ' + r);
  });
  bot.on('end', () => {
    console.log('[bot] 连接断开,5 秒后重连...');
    log('bot', 'ludwiggod', 'disconnected');
    if (currentBot === bot) currentBot = null;   // 重连窗口内挂起 outbox 消费, 命令留在文件里
    setTimeout(start, 5000);
  });
  bot.on('error', (e) => { console.error('[bot err]', e.message); });

}

// outbox 轮询:模块级只注册一次
// (原写在 start() 内 → 每次重连都新注册一个且从不清理, 堆叠后多个轮询抢读同一文件 → outbox bad line)
setInterval(() => {
  const bot = currentBot;
  if (!bot) return;   // 未连接/重连窗口内不消费, 命令留在 outbox 等新连接
  try {
    if (!fs.existsSync(OUTBOX)) return;
    const content = fs.readFileSync(OUTBOX, 'utf8');
    fs.rmSync(OUTBOX, { force: true });
    const lines = content.split('\n').filter(l => l.trim());
    for (const l of lines) {
      try {
        const cmd = JSON.parse(l.trim()).cmd;
        if (cmd) {
          if (cmd === 'scanchests') {
            handleScanChests(bot);
            continue;
          }
          // 以 ! 开头的 cmd = 发纯聊天消息(不拼 /), 用于触发 kubejs PlayerEvents.chat
          if (cmd.startsWith('!')) {
            bot.chat(cmd.slice(1));
          } else {
            bot.chat('/' + cmd);
          }
          log('exec', 'god', cmd, 'sent');
          console.log('[exec]', cmd);
        }
      } catch (e) { console.error('[outbox bad line]', l); }
    }
  } catch (e) { console.error('[outbox err]', e.message); }
}, 1000);

start();
