// schematic-v1-convert.js — 老式 .schematic(MCEdit v1, Alpha) → 1.20.1 fill/setblock 命令
// 用法: node schematic-v1-convert.js <file> <baseX> <baseY> <baseZ> [--stats]
// 索引: index = x + z*W + y*W*L ; Blocks=byteArray(带符号,需 &0xFF), Data=metadata
const nbt = require('/Users/ludwigxu/Documents/Projects/mc-lzmx/node_modules/prismarine-nbt');
const fs = require('fs'); const zlib = require('zlib');
const md = require('/Users/ludwigxu/Documents/Projects/mc-lzmx/node_modules/minecraft-data')('1.12.2');

const schemPath = process.argv[2];
const [baseX, baseY, baseZ] = process.argv.slice(3, 6).map(Number);
const onlyStats = process.argv.includes('--stats');

// 非满格、必须逐格 setblock(含所有带状态方块)
const NON_FULL = new Set(['water', 'lily_pad', 'sugar_cane', 'flower_pot', 'ladder', 'fern', 'dead_bush']);

// (id,meta) → 现代块名+状态
const COLORS = ['white','orange','magenta','light_blue','yellow','lime','pink','gray','light_gray','cyan','purple','blue','brown','green','red','black'];
const STAIR_FACING = ['east','west','south','north'];
const TRAP_FACING = ['east','west','south','north'];
const SHULKER_FACING = ['down','up','north','south','west','east'];
const GLAZED_FACING = ['south','west','north','east'];
const LADDER_FACING = ['north','south','west','east'];  // meta2=north,3=south,4=west,5=east
const LOG_TYPE = ['oak','spruce','birch','jungle'];
const LEAF_TYPE = ['oak','spruce','birch','jungle'];
const AXIS = ['y','x','z'];

function mapBlock(id, meta) {
  switch (id) {
    case 0: return null;
    case 2: return 'grass_block';
    case 3: return meta === 2 ? 'podzol' : 'dirt';
    case 5: return 'oak_planks';
    case 9: return 'water';
    case 12: return 'sand';
    case 13: return 'gravel';
    case 17: return LOG_TYPE[meta & 3] + '_log[axis=' + AXIS[(meta >> 2) & 3] + ']';
    case 18: return LEAF_TYPE[meta & 3] + '_leaves';
    case 24: return 'sandstone';
    case 31: return meta === 1 ? 'fern' : 'dead_bush';
    case 35: return COLORS[meta] + '_wool';
    case 43: return 'stone_slab[type=double]';
    case 44: return 'stone_slab[type=' + (meta & 8 ? 'top' : 'bottom') + ']';
    case 53: return 'oak_stairs[facing=' + STAIR_FACING[meta & 3] + ',half=' + (meta & 4 ? 'top' : 'bottom') + ']';
    case 65: return 'ladder[facing=' + LADDER_FACING[meta] + ']';
    case 83: return 'sugar_cane';
    case 85: return 'oak_fence';
    case 89: return 'glowstone';
    case 96: return 'oak_trapdoor[facing=' + TRAP_FACING[meta & 3] + ',half=' + (meta & 4 ? 'top' : 'bottom') + ',open=' + ((meta >> 3) & 1 ? 'true' : 'false') + ']';
    case 111: return 'lily_pad';
    case 125: return 'oak_slab[type=double]';
    case 126: return 'oak_slab[type=' + (meta & 8 ? 'top' : 'bottom') + ']';
    case 140: return 'flower_pot';
    case 159: return COLORS[meta & 15] + '_terracotta';
    case 228: return 'cyan_shulker_box[facing=' + SHULKER_FACING[meta & 7] + ']';
    case 229: return 'purple_shulker_box[facing=' + SHULKER_FACING[meta & 7] + ']';
    case 236: return 'orange_glazed_terracotta[facing=' + GLAZED_FACING[meta & 3] + ']';
    case 254: return 'water';   // 底部水塘/护城河(mcbuild 导出工具的非标 ID,按水处理)
    default:
      return md.blocks[id] ? md.blocks[id].name : null;
  }
}

const raw = zlib.gunzipSync(fs.readFileSync(schemPath));
nbt.parse(raw, 'big').then(d => {
  const v = d.parsed.value;
  const W = v.Width.value, H = v.Height.value, L = v.Length.value;
  const Blocks = v.Blocks.value, Data = v.Data.value;
  // 3D 网格(现代块名)
  const cells = Array.from({ length: H }, () => Array.from({ length: L }, () => new Array(W).fill('air')));
  for (let y = 0; y < H; y++) for (let z = 0; z < L; z++) for (let x = 0; x < W; x++) {
    const idx = x + z * W + y * W * L;
    const id = Blocks[idx] & 0xFF;
    const name = mapBlock(id, Data[idx]);
    if (name) cells[y][z][x] = name;
  }
  // 统计
  const counts = {};
  for (let y = 0; y < H; y++) for (let z = 0; z < L; z++) for (let x = 0; x < W; x++) {
    const b = cells[y][z][x];
    counts[b] = (counts[b] || 0) + 1;
  }
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const nonAir = sorted.filter(([n]) => n !== 'air');
  console.log(`尺寸 ${W}x${H}x${L} 总格 ${W*H*L} 非空气 ${nonAir.reduce((s,[,c])=>s+c,0)}`);
  console.log('top:', nonAir.slice(0, 12).map(([n, c]) => `${n}x${c}`).join(' '));
  // 最低/最高非空层
  for (let y = 0; y < H; y++) { let non = 0; for (let z = 0; z < L; z++) for (let x = 0; x < W; x++) if (cells[y][z][x] !== 'air') non++; if (non) { console.log('最低非空 y=' + y, '非空=' + non); break; } }
  for (let y = H - 1; y >= 0; y--) { let non = 0; for (let z = 0; z < L; z++) for (let x = 0; x < W; x++) if (cells[y][z][x] !== 'air') non++; if (non) { console.log('最高非空 y=' + y, '非空=' + non); break; } }
  if (onlyStats) process.exit(0);

  const fillable = (n) => n !== 'air' && !NON_FULL.has(n);
  const cmds = [];
  const placed = Array.from({ length: H }, () => Array.from({ length: L }, () => new Array(W).fill(false)));
  // 盒聚合
  for (let y = 0; y < H; y++) for (let z = 0; z < L; z++) for (let x = 0; x < W; x++) {
    const b = cells[y][z][x];
    if (placed[y][z][x] || !fillable(b)) continue;
    let x2 = x;
    while (x2 + 1 < W && cells[y][z][x2 + 1] === b && !placed[y][z][x2 + 1]) x2++;
    let z2 = z;
    outerZ: while (z2 + 1 < L) { for (let xi = x; xi <= x2; xi++) if (cells[y][z2 + 1][xi] !== b || placed[y][z2 + 1][xi]) break outerZ; z2++; }
    let y2 = y;
    outerY: while (y2 + 1 < H) { for (let zi = z; zi <= z2; zi++) for (let xi = x; xi <= x2; xi++) if (cells[y2 + 1][zi][xi] !== b || placed[y2 + 1][zi][xi]) break outerY; y2++; }
    const cnt = (x2 - x + 1) * (z2 - z + 1) * (y2 - y + 1);
    if (cnt >= 4) cmds.push(`fill ${baseX+x} ${baseY+y} ${baseZ+z} ${baseX+x2} ${baseY+y2} ${baseZ+z2} ${b}`);
    else for (let yi = y; yi <= y2; yi++) for (let zi = z; zi <= z2; zi++) for (let xi = x; xi <= x2; xi++) cmds.push(`setblock ${baseX+xi} ${baseY+yi} ${baseZ+zi} ${b}`);
    for (let yi = y; yi <= y2; yi++) for (let zi = z; zi <= z2; zi++) for (let xi = x; xi <= x2; xi++) placed[yi][zi][xi] = true;
  }
  // 非满格 setblock
  for (let y = 0; y < H; y++) for (let z = 0; z < L; z++) for (let x = 0; x < W; x++) {
    const b = cells[y][z][x];
    if (b === 'air' || placed[y][z][x]) continue;
    cmds.push(`setblock ${baseX+x} ${baseY+y} ${baseZ+z} ${b}`);
  }
  fs.writeFileSync('/tmp/jp-big-fills.jsonl', cmds.map(c => JSON.stringify({ cmd: c })).join('\n'));
  console.log(`命令总数: ${cmds.length} (fill ${cmds.filter(c=>c.startsWith('fill')).length} / setblock ${cmds.filter(c=>c.startsWith('setblock')).length})`);
  console.log('写出 /tmp/jp-big-fills.jsonl');
}).catch(e => console.log('ERR', e.message));
