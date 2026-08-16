// gen-shrine.js — 和风神社+鸟居 fill 命令生成器
// 锚点: ludwigxu 所在 (-671, 72, -142);GROUND=72 为可走平面,地表方块在 71
// 布局(沿 +Z): 鸟居(Z4) → 参道(Z5..14) → 石灯笼(Z10 两侧) → 台阶(Z15..16) → 社殿平台(Z17..29) → 社殿+屋顶
const BX = -671, BZ = -142, GROUND = 72;
const cmds = [];
function fill(x1, y1, z1, x2, y2, z2, block) {
  cmds.push(`fill ${BX + x1} ${GROUND + y1} ${BZ + z1} ${BX + x2} ${GROUND + y2} ${BZ + z2} ${block}`);
}

// 0. 清空建造体积(去掉树木/杂物),再铺实心地基吸收地形起伏
fill(-8, 0, 0, 8, 12, 29, 'air');
fill(-8, -4, 0, 8, -1, 29, 'stone_bricks');

// 1. 鸟居(朱红) 门面在 Z=4
fill(-3, 0, 4, -3, 7, 4, 'crimson_stem');       // 左柱
fill(3, 0, 4, 3, 7, 4, 'crimson_stem');         // 右柱
fill(-3, 0, 4, -3, 0, 4, 'smooth_quartz');      // 左柱基
fill(3, 0, 4, 3, 0, 4, 'smooth_quartz');        // 右柱基
fill(-4, 4, 4, 4, 4, 4, 'crimson_planks');      // nuki(贯)
fill(-4, 7, 4, 4, 7, 4, 'crimson_planks');      // kasagi(笠木)
fill(-4, 8, 4, 4, 8, 4, 'smooth_quartz_slab');  // 笠木顶饰

// 2. 参道(Z5..14) 石板+卵石镶边
fill(-1, 0, 5, 1, 0, 14, 'stone_bricks');
fill(-2, 0, 5, -2, 0, 14, 'cobblestone');
fill(2, 0, 5, 2, 0, 14, 'cobblestone');

// 3. 石灯笼(参道两侧 X±4, Z=10)
fill(-4, 0, 10, -4, 1, 10, 'smooth_quartz');
fill(4, 0, 10, 4, 1, 10, 'smooth_quartz');
fill(-4, 2, 10, -4, 2, 10, 'smooth_quartz_slab');
fill(4, 2, 10, 4, 2, 10, 'smooth_quartz_slab');

// 4. 台阶(Z15..16) 一级一级抬升到平台顶(relY2)
fill(-2, 1, 15, 2, 1, 15, 'stone_bricks');
fill(-2, 2, 16, 2, 2, 16, 'stone_bricks');

// 5. 社殿平台(Z17..29) + 石英贴边
fill(-7, 1, 17, 7, 2, 29, 'stone_bricks');
fill(-7, 2, 17, 7, 2, 17, 'smooth_quartz');     // 前缘
fill(-7, 2, 29, 7, 2, 29, 'smooth_quartz');     // 后缘
fill(-7, 2, 18, -7, 2, 28, 'smooth_quartz');    // 左缘
fill(7, 2, 18, 7, 2, 28, 'smooth_quartz');      // 右缘

// 6. 社殿白墙(Y3..6) 前墙开一门洞
fill(-6, 3, 19, 6, 6, 19, 'smooth_quartz');     // 前墙
fill(-1, 3, 19, 1, 5, 19, 'air');               // 门洞
fill(-1, 6, 19, 1, 6, 19, 'crimson_planks');    // 门楣
fill(-6, 3, 28, 6, 6, 28, 'smooth_quartz');     // 后墙
fill(-6, 3, 20, -6, 6, 28, 'smooth_quartz');    // 左墙
fill(6, 3, 20, 6, 6, 28, 'smooth_quartz');      // 右墙

// 7. 四角朱红立柱(Y3..7 撑起屋角)
fill(-6, 3, 19, -6, 7, 19, 'crimson_stem');
fill(6, 3, 19, 6, 7, 19, 'crimson_stem');
fill(-6, 3, 28, -6, 7, 28, 'crimson_stem');
fill(6, 3, 28, 6, 7, 28, 'crimson_stem');

// 8. 分层深板岩瓦屋顶(层层收窄出屋檐)
fill(-8, 7, 18, 8, 7, 29, 'deepslate_tile_slab');
fill(-6, 8, 20, 6, 8, 27, 'deepslate_tile_slab');
fill(-4, 9, 21, 4, 9, 26, 'deepslate_tile_slab');
fill(-2, 10, 22, 2, 10, 25, 'deepslate_tile_slab');
fill(-1, 11, 23, 1, 11, 24, 'deepslate_tiles');  // 屋脊

console.log(cmds.length + ' fills');
console.log(cmds.map(c => JSON.stringify({ cmd: c })).join('\n'));
