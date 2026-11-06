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
const HP_MAP = { 'ludwigxu': 1000000 };   // 玩家 -> 死亡后自动补的最大血量
// bot 声称的 mod 列表(FML3 格式: "modid@version";含 minecraft/forge 本体)
const FORGE_MODS = JSON.parse(fs.readFileSync('/tmp/forge-mods.json', 'utf8'))
  .map(m => m.modid + '@' + m.version)
  .concat(['minecraft@1.20.1', 'forge@47.3.22']);

function log(type, player, msg, extra) {
  try {
    const line = JSON.stringify({ t: type, p: String(player || ''), m: String(msg || ''), x: String(extra || ''), ts: Date.now() });
    fs.appendFileSync(INBOX, line + '\n');
  } catch (e) {}
}

process.on('uncaughtException', (e) => {
  console.error('[uncaught]', e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n') : e);
});
process.on('unhandledRejection', (e) => console.error('[unhandled]', e));

function start() {
  const bot = mineflayer.createBot({
    host: '127.0.0.1', port: 51620,
    username: 'ludwiggod', auth: 'offline', hideErrors: false,
    version: false,                 // 触发 minecraft-protocol 自动版本协商(hook 时机)
    physicsEnabled: false,          // 只做协议入口,不跑物理模拟
  });
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

  bot.on('spawn', () => {
    try { bot.setViewDistance(2); } catch (e) {}   // 最小视距,不拉区块
    // 上线自动设置:创造模式 + 隐身(神的化身,对玩家不可见)
    // spawn 后 3 秒执行,等 kubejs auto-op 生效;spawn 可能因 tp 重复触发,重复设置无害
    setTimeout(() => {
      try {
        bot.chat('/gamemode creative ludwiggod');
        bot.chat('/effect give ludwiggod minecraft:invisibility 999999 0 true');
        console.log('[god] creative + invisible');
      } catch (e) {}
    }, 3000);
    log('bot', 'ludwiggod', 'spawned');
    console.log('[bot] 上线');
  });

  bot.on('chat', (username, message) => {
    if (username === 'ludwiggod') return;
    // 事件分级:仅触发词(神/god/@claude)进 inbox,普通聊天只进本地日志
    const lower = message.toLowerCase();
    const isTrigger = lower.indexOf('神') !== -1 || lower.indexOf('god') !== -1 || lower.indexOf('@claude') !== -1;
    if (isTrigger) {
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
      if (text && text.indexOf(']') !== -1) { console.log('[msg]', text); }
      // 死亡自动补血:死亡广播 3 秒后重设最大血量(防重生回退)
      for (const name of Object.keys(HP_MAP)) {
        if (text.includes(name) && /died|was slain|was shot|was blown|burned to death|drowned|suffocated|starved to death|fell from|fell off|hit the ground|was impaled|was killed|was pricked|blew up/.test(text)) {
          log('death', name, text);   // 死亡原因原文进 inbox,方便 Claude 诊断
          setTimeout(() => {
            bot.chat('/attribute ' + name + ' minecraft:generic.max_health base set ' + HP_MAP[name]);
            log('revive', name, 'hp restored');
            console.log('[revive]', name, 'hp ->', HP_MAP[name]);
          }, 3000);
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
    setTimeout(start, 5000);
  });
  bot.on('error', (e) => { console.error('[bot err]', e.message); });

  // outbox 轮询
  setInterval(() => {
    try {
      if (!fs.existsSync(OUTBOX)) return;
      const content = fs.readFileSync(OUTBOX, 'utf8');
      fs.rmSync(OUTBOX, { force: true });
      const lines = content.split('\n').filter(l => l.trim());
      for (const l of lines) {
        try {
          const cmd = JSON.parse(l.trim()).cmd;
          if (cmd) {
            bot.chat('/' + cmd);
            log('exec', 'god', cmd, 'sent');
            console.log('[exec]', cmd);
          }
        } catch (e) { console.error('[outbox bad line]', l); }
      }
    } catch (e) { console.error('[outbox err]', e.message); }
  }, 1000);
}

start();
