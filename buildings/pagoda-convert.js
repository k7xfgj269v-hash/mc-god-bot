// pagoda-convert.js — 把 Sponge v3 schematic 转成 fill/setblock 命令序列
// 用法: node pagoda-convert.js <schem> <baseX> <baseY> <baseZ> [--stats]
// 索引: index = x + z*W + y*W*L  (W=Width=x, L=Length=z, H=Height=y)
const nbt = require('/Users/ludwigxu/Documents/Projects/mc-lzmx/node_modules/prismarine-nbt');
const fs = require('fs'); const zlib = require('zlib');

const schemPath = process.argv[2];
const [baseX, baseY, baseZ] = process.argv.slice(3, 6).map(Number);
const onlyStats = process.argv.includes('--stats');

// 非满格、不能 fill 聚合的裸名方块(需逐格 setblock;无状态但非整方块)
const NON_FULL_BARE = new Set([
  'minecraft:air', 'minecraft:grass', 'minecraft:tall_grass', 'minecraft:fern',
  'minecraft:large_fern', 'minecraft:torch', 'minecraft:wall_torch',
  'minecraft:flower_pot', 'minecraft:oak_sapling', 'minecraft:spruce_sapling',
  'minecraft:lantern', 'minecraft:soul_lantern', 'minecraft:candle',
  'minecraft:water', 'minecraft:lava', 'minecraft:vine', 'minecraft:ladder',
]);

const raw = zlib.gunzipSync(fs.readFileSync(schemPath));
nbt.parse(raw, 'big').then(d => {
  const S = d.parsed.value.Schematic.value;
  const W = S.Width.value, H = S.Height.value, L = S.Length.value;
  const B = S.Blocks.value;
  const paletteNames = Object.keys(B.Palette.value);
  const paletteId = Object.fromEntries(paletteNames.map((n, i) => [n, i]));
  const data = B.Data.value; // byteArray

  // 3D 网格: cells[y][z][x] = palette 名称(去 waterlogged=false)
  const cells = Array.from({ length: H }, () => Array.from({ length: L }, () => new Array(W).fill('minecraft:air')));
  for (let y = 0; y < H; y++) {
    for (let z = 0; z < L; z++) {
      for (let x = 0; x < W; x++) {
        const idx = data[x + z * W + y * W * L];
        if (idx === undefined || idx < 0 || idx >= paletteNames.length) continue;
        cells[y][z][x] = paletteNames[idx].replace(',waterlogged=false', '');
      }
    }
  }

  // 统计
  const counts = {};
  for (let y = 0; y < H; y++) for (let z = 0; z < L; z++) for (let x = 0; x < W; x++) {
    const b = cells[y][z][x];
    counts[b] = (counts[b] || 0) + 1;
  }
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const nonAir = sorted.filter(([n]) => n !== 'minecraft:air');
  console.log(`尺寸 ${W}x${H}x${L} 总格 ${W*H*L} 非空气 ${nonAir.reduce((s, [,c])=>s+c,0)}`);
  console.log('top:', nonAir.slice(0, 10).map(([n, c]) => `${n.split(':').pop()}x${c}`).join(' '));

  if (onlyStats) {
    // 底部 3 层非空气(判断是否自带地基)
    for (let ly = 0; ly < Math.min(3, H); ly++) {
      const names = new Set();
      for (let z = 0; z < L; z++) for (let x = 0; x < W; x++) {
        const b = cells[ly][z][x];
        if (b !== 'minecraft:air') names.add(b.replace('minecraft:', ''));
      }
      console.log(`y=${ly} 层非空气: ${[...names].slice(0,8).join(', ')}`);
    }
    // 疑似 1.21+ 专属块(1.20.1 不存在会 setblock 报错)
    const suspicious = nonAir.filter(([n]) => /copper_bulb|copper_grate|tuff_brick|chiseled_tuff|pale_|resin|crafter|trial|heavy_core|oxidized_copper|weathered_copper|exposed_copper|red_nether/.test(n));
    console.log('疑似1.21专属:', suspicious.length ? suspicious.map(([n, c]) => n.replace('minecraft:', '') + 'x' + c).join(' ') : '无');
    process.exit(0);
  }

  // 分类: 非空气且非"必须逐格"的块都能盒 fill(含带状态,只要盒内状态一致)
  // fill 支持状态串(如 stripped_acacia_wood[axis=y]); 盒生长器保证盒内名字+状态完全相同
  const fillable = (name) => name !== 'minecraft:air' && !NON_FULL_BARE.has(name);

  const cmds = [];
  const placed = Array.from({ length: H }, () => Array.from({ length: L }, () => new Array(W).fill(false)));

  // 盒填充: 对每个可聚合块, 贪心扩展最大盒子(状态一致才聚合)
  for (let y = 0; y < H; y++) {
    for (let z = 0; z < L; z++) {
      for (let x = 0; x < W; x++) {
        const b = cells[y][z][x];
        if (placed[y][z][x] || !fillable(b)) continue;
        // 扩展 X 方向最长连续
        let x2 = x;
        while (x2 + 1 < W && cells[y][z][x2 + 1] === b && !placed[y][z][x2 + 1]) x2++;
        // 扩展 Z 方向: 整行一致
        let z2 = z;
        outerZ: while (z2 + 1 < L) {
          for (let xi = x; xi <= x2; xi++) if (cells[y][z2 + 1][xi] !== b || placed[y][z2 + 1][xi]) break outerZ;
          z2++;
        }
        // 扩展 Y 方向: 整面一致
        let y2 = y;
        outerY: while (y2 + 1 < H) {
          for (let zi = z; zi <= z2; zi++) for (let xi = x; xi <= x2; xi++) if (cells[y2 + 1][zi][xi] !== b || placed[y2 + 1][zi][xi]) break outerY;
          y2++;
        }
        const cnt = (x2 - x + 1) * (z2 - z + 1) * (y2 - y + 1);
        if (cnt >= 4) {
          const id = b.replace('minecraft:', '');
          cmds.push(`fill ${baseX+x} ${baseY+y} ${baseZ+z} ${baseX+x2} ${baseY+y2} ${baseZ+z2} ${id}`);
        } else {
          for (let yi = y; yi <= y2; yi++) for (let zi = z; zi <= z2; zi++) for (let xi = x; xi <= x2; xi++) {
            cmds.push(`setblock ${baseX+xi} ${baseY+yi} ${baseZ+zi} ${b.replace('minecraft:','')}`);
          }
        }
        for (let yi = y; yi <= y2; yi++) for (let zi = z; zi <= z2; zi++) for (let xi = x; xi <= x2; xi++) placed[yi][zi][xi] = true;
      }
    }
  }

  // 未被盒聚合的块(孤立带状态/非满格) → setblock
  for (let y = 0; y < H; y++) for (let z = 0; z < L; z++) for (let x = 0; x < W; x++) {
    const b = cells[y][z][x];
    if (b === 'minecraft:air' || placed[y][z][x]) continue;
    cmds.push(`setblock ${baseX+x} ${baseY+y} ${baseZ+z} ${b.replace('minecraft:','')}`);
  }

  fs.writeFileSync('/tmp/pagoda-fills.jsonl', cmds.map(c => JSON.stringify({ cmd: c })).join('\n'));
  console.log(`命令总数: ${cmds.length} (fill ${cmds.filter(c=>c.startsWith('fill')).length} / setblock ${cmds.filter(c=>c.startsWith('setblock')).length})`);
  console.log('写出 /tmp/pagoda-fills.jsonl');
}).catch(e => console.log('ERR', e.message));
