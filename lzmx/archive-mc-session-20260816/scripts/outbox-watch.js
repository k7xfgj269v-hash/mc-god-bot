const fs = require('fs');
const p = process.env.HOME + '/Library/Application Support/minecraft/mc-bridge/outbox.jsonl';
// 先确保文件不存在，让 bot 处于"等文件"状态
try { fs.rmSync(p); } catch(e) {}
setTimeout(() => {
  fs.writeFileSync(p, '{"cmd":"list"}\n');
  console.log('[W] 已写入 at', Date.now());
}, 200);
// 高频采样文件内容
const seen = {};
const timer = setInterval(() => {
  try {
    const b = fs.readFileSync(p);
    const hex = [...b].map(x=>x.toString(16)).join('');
    if (!seen[hex]) { seen[hex] = 1; console.log('[S]', new Date().toISOString().slice(17,23), 'len='+b.length, 'hex='+hex, JSON.stringify(b.toString())); }
  } catch(e) { /* 文件不存在 */ }
}, 10);
setTimeout(() => { clearInterval(timer); process.exit(0); }, 3000);
