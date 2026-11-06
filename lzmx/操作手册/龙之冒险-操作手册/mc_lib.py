#!/usr/bin/env python3
"""Minecraft 存档(.mca region)与示意图(.schematic)解析层 —— 解析全部交给现成库。

依赖(本机实测版本,装一次):
    pip3 install --break-system-packages --user nbtlib==2.0.4 anvil-parser2==0.10.6
  nbtlib         —— NBT 二进制解析 + 自动识别 gzip/zlib 容器,用来读 .schematic(本质就是 gzip 过的 NBT)
  anvil-parser2  —— .mca region 表头读取、zlib 解压、1.13+/1.18+ 方块状态调色板解码

之前这一层是手写的(递归 NBT 解析器 + 自己解 region 表头 + 自己解打包 long),
一个位序写反就出「高度每 16 格在 79/63 之间跳」的棋盘格假象,同一个 bug 在 6 个脚本里各犯一次。
换库之后下面这些坑由库负责,但坑本身仍然要留档 —— 出问题时知道该往哪儿看。

============================ 格式坑(留档) ============================

  1) region 表头(坑的是「以为两种格式不一样」)
     表头 = 4096 个 4 字节偏移项 + 4096 个 4 字节时间戳 = 8192 字节。
     每项 4 字节 = **前 3 字节大端扇区偏移 + 第 4 字节扇区数**。
     这套表头布局 McRegion(.mcr)与 Anvil(.mca)**完全相同** —— Anvil 只改了区块载荷
     (.mcr 是单层 Blocks/Data,.mca 是 sections 数组 / 1.13+ 的 block_states 调色板)。
     实测本存档 r.-2.-1.mca 首项字节 `00 01 23 02` → 偏移 291 扇区、占 2 扇区,与上式吻合。
     我最早写错的地方是反了:**把「4 字节偏移」当成 Anvil 的布局**,照那样读偏移会大 256 倍
     并直接越界读到文件尾,表现是「每个区块都返回 None」而不是报错。

  2) 根复合的名字没有类型字节前缀
     NBT 根复合的结构是 [0x0a][名字长度 2 字节][名字][条目...],名字前面**没有**类型字节。
     拿通用的「先读类型字节」payload 解析器从第 0/1 字节开始啃,会把名字长度当成 tag 类型,
     一路错位到全零区,最后得到一个**空 dict 而不是异常** —— 普查出来全是 0,极难发现。
     nbtlib 里这就是标准 NBT 解析,不会踩。

  3) 方块索引的位序(**库与手写用的是同一口径,写反了照样错**)
     1.18+ 的 section 里 block_states.data 是打包 long 数组,索引
         i = (y*16 + z)*16 + x   ⇒  x 在最低 4 位、z 次之、y 在最高 4 位
     写成 1.12 那种 x 最高的老顺序,会把 x 和 y 对调 —— 症状是一片
     「高度每 16 格在 79/63 之间跳」的棋盘格,自然地形不可能长这样,**见到即知位序反了**。
     实测:anvil 的 stream_blocks 与手写实现在 r.-2.-2.mca 整区块 98,304 个方块上逐块一致。

======================== 库本身的坑(我实测过的) ========================

  A) **同名遮蔽:曾经踩过,在本目录已不复存在。** 当年这批脚本住在 /tmp,而 /tmp 里有个
     历史脚本也叫 anvil.py;脚本目录在 sys.path 最前,`import anvil` 拿到的是那个文件,
     后续 `anvil.Region` 直接 AttributeError。为此本文件曾有一段护栏:导入期间临时把
     脚本目录从 sys.path 摘出去、导完再放回。
     **搬迁到本手册目录后已删除该护栏** —— 这个目录里没有 anvil.py / nbtlib.py / nbt.py,
     遮蔽不可能再发生,而留着一个不再生效的 workaround 本身就是认知负担。
     只保留一条便宜的体检:_import_libs() 导完立刻确认 anvil 真是 anvil-parser2 包
     (有 Region 属性),撞上就当场说清楚,而不是等到调用时才炸。
     ⚠️ 反过来:如果哪天又把这批脚本拷回 /tmp 跑,那个同名历史文件**还会咬人** ——
     届时要么删掉/改名它,要么把这段 sys.path 护栏加回来。

  B) anvil 的 `get_chunk()` 会把坐标 `% 32` **静默折叠**:传一个不属于该 region 文件的
     坐标不会报错,而是安静地返回另一个区块。本文件的 Save.chunk() 一律按绝对坐标
     自己算 region 文件名,再传进去,不给它折叠的机会。

  C) anvil **不支持 gzip 压缩的区块**(comp==1 直接抛 GZipChunkData)。实测本存档
     185 个 region / 73,294 个区块的压缩类型**全是 comp=2(zlib)**,所以不受影响;
     但换个存档可能撞上。Save.chunk() 会把它转成一句可读的报错。

  D) anvil 把「**单元素调色板且没有 data 键**」的 section 一律当成全空气(源码
     _states_from_section 的 KeyError 分支)。按格式应该是 palette[0] 那一种方块。
     实测本工作区 0 例(单元素调色板的全是 air),所以现在不炸;但为了不依赖库的这条
     分支,iter_blocks() 遇到单元素调色板时按调色板自己判定。

  E) anvil 的 `_states_from_section` 有一处拼写错位:
       [state if state >= 0 else states + 2 ** 64 for state in states.value]
                                        ^^^^^^ 应为 state
     一旦某个打包 long 的**最高位为 1**(64 位被填满的位宽,即 bits ∈ {4,8,16,32},
     且最高那格索引大到把 bit63 顶起来),读取时该 long 是负数,就会走到这个分支抛
     TypeError。实测本工作区 0 次触发;写在这里是因为它**只在别的存档上炸**。
"""
import os


def _import_libs():
    """导入 nbtlib / anvil,并当场确认拿到的是真包。

    这里原来有一段「导入期间把脚本目录从 sys.path 摘出去」的护栏,用来绕开 /tmp/anvil.py
    的同名遮蔽;搬到本目录后已删除(目录里没有同名文件,遮蔽不会发生)。见文件头坑 A。
    留下的这条体检很便宜,但能挡住「有人拷回 /tmp 跑」或「PYTHONPATH 里混进同名文件」
    这类事故:那时 anvil 会是别的东西,这里直接报错,而不是等到调用 .Region 才炸。
    """
    import anvil
    import nbtlib
    if not hasattr(anvil, 'Region'):
        raise ImportError('import anvil 拿到的是 %s,不是 anvil-parser2 包(有同名文件顶掉了?)'
                          % getattr(anvil, '__file__', '?'))
    return anvil, nbtlib


anvil, nbtlib = _import_libs()

AIR = 'minecraft:air'


def _is_air(name):
    """是不是「空气」(含 minecraft:cave_air / void_air 这类变体)。

    原脚本一律用 endswith('air') 判定,这里保持同一口径 —— 换成 == 'minecraft:air'
    会把洞穴空气/虚空空气当成实心方块,列顶高度和普查计数都会变(实测差 177 块)。
    """
    return name.endswith('air')


# ===================== .schematic(MCEdit 经典格式) =====================
def load_schematic(path):
    """读 .schematic,返回根复合。

    格式 = **gzip 过的 NBT**,顶层键 Width/Height/Length/Blocks/Data[/AddBlocks]。
    nbtlib.load() 自己嗅探容器(gzip/zlib/裸),不用我们去看头两个字节是不是 gzip 魔数。
    Blocks 是 ByteArray(有符号 int8),所以取值一律 `& 0xFF` 还原成 0-255。
    """
    return nbtlib.load(path)


def schematic_cells(root, ys=None):
    """把 schematic 摊平成生成器,产出 ((示意 x, y, z), id, meta),顺序 = (y*L + z)*W + x。

    AddBlocks 是 id 的高 9-12 位(半字节打包,偶索引在低半字节),1.13 以前 id 超过 255
    才需要;chateau2.schematic 里没有这个键。

    ys 给一个层号集合时只产这些层。循环本来就是 y 在最外层,所以这是整层整层地跳过
    (省下每格一个元组 + 两次 int 的开销),不是产出来再筛 —— 846,600 格的 schematic
    上实测 0.33s → 0.01s。要「看过所有层才知道答案」的用法(dump 的直方图/floor 的逐列
    最低)不能传它,传了就只剩点名的那几层。
    """
    W, H, L = int(root['Width']), int(root['Height']), int(root['Length'])
    blocks = root['Blocks']
    data = root.get('Data')
    add = root.get('AddBlocks')
    for y in range(H):
        if ys is not None and y not in ys:
            continue
        for z in range(L):
            for x in range(W):
                k = (y * L + z) * W + x
                bid = blocks[k] & 0xFF
                if add:
                    nib = add[k >> 1]
                    bid |= ((nib & 0x0F) if (k & 1) == 0 else ((nib >> 4) & 0x0F)) << 8
                yield (x, y, z), bid, (data[k] if data is not None else 0)


# ===================== .mca(存档 region) =====================
class Save:
    """一个存档目录的区块读取器。region 文件按需读入并缓存。"""

    def __init__(self, world_dir):
        self.dir = world_dir
        self._regions = {}
        self._tops = {}

    def _region(self, rx, rz):
        key = (rx, rz)
        if key not in self._regions:
            path = os.path.join(self.dir, 'region', 'r.%d.%d.mca' % key)
            self._regions[key] = anvil.Region.from_file(path) if os.path.exists(path) else None
        return self._regions[key]

    def chunk(self, cx, cz):
        """绝对区块坐标 → anvil 的 Chunk;区块不存在(或 region 文件是空的)返回 None。"""
        reg = self._region(cx >> 5, cz >> 5)
        if reg is None:
            return None
        if reg.chunk_location(cx, cz) == (0, 0):       # (0,0) = 这个区块还没生成
            return None
        try:
            return reg.get_chunk(cx, cz)
        except anvil.errors.GZipChunkData as e:         # 见文件头坑 C
            raise RuntimeError(
                '区块 (%d,%d) 用 gzip 压缩(comp=1),anvil-parser2 不支持 —— '
                '本存档实测全是 zlib,遇到这个说明换存档了' % (cx, cz)) from e

    def topmap(self, cx, cz):
        """该区块每一列的「最高非空气方块 y」。按区块缓存 —— 逐列去问会重复扫整个区块。"""
        if (cx, cz) not in self._tops:
            top = {}
            ch = self.chunk(cx, cz)
            if ch is not None:
                for gx, gy, gz, _ in iter_blocks(ch):
                    k = (gx, gz)
                    if gy > top.get(k, -1):
                        top[k] = gy
            self._tops[(cx, cz)] = top
        return self._tops[(cx, cz)]

    def top(self, x, z):
        """该列最高非空气方块的世界 y;整列空气返回 -1。"""
        return self.topmap(x >> 4, z >> 4).get((x, z), -1)


def palette_names(section):
    """一个 section 的调色板方块名列表。1.18+ 在 block_states.palette,老版本直接是 Palette。"""
    if 'block_states' in section:
        pal = section['block_states']['palette']
    else:
        pal = section.get('Palette')
    return [str(p['Name'].value) for p in (pal or [])]


def _sections(chunk):
    """区块的 section 列表。库在这里做过版本归一:老版本在 Level.Sections(大写)。"""
    if 'sections' in chunk.data:
        return chunk.data['sections']
    return chunk.data.get('Sections', [])


def iter_blocks(chunk):
    """遍历一个区块的**非空气**方块,产出 (世界 x, 世界 y, 世界 z, 方块全名)。

    坐标用 chunk.x / chunk.z(取自 NBT 的 xPos/zPos,是权威值,不受调用方传参影响)。
    方块名口径 = "minecraft:xxx"(与调色板 Name 一致),不带 Properties 状态串。
    """
    cx, cz = int(chunk.x), int(chunk.z)
    for sec in _sections(chunk):
        sec_y = int(sec['Y'].value)
        names = palette_names(sec)
        if len(names) == 1:
            # 单元素调色板:整段就这一种方块。库在这里会一律当空气(见文件头坑 D),
            # 所以不走库:全空气就跳过,否则整段按同一种方块产出。
            if _is_air(names[0]):
                continue
            for i in range(4096):
                yield cx * 16 + (i & 15), sec_y * 16 + (i >> 8), cz * 16 + ((i >> 4) & 15), names[0]
            continue
        for i, blk in enumerate(chunk.stream_blocks(section=sec_y)):
            name = blk.name()
            if _is_air(name):
                continue
            # i = (y*16 + z)*16 + x —— x 在最低 4 位(见文件头坑 3)
            yield cx * 16 + (i & 15), sec_y * 16 + (i >> 8), cz * 16 + ((i >> 4) & 15), name


def tile_entities(chunk):
    """区块里的方块实体(箱子/告示牌/刷怪笼...),产出 (id, 世界 x, y, z)。

    库已经做过版本归一:1.18+ 在 block_entities,老版本在 Level.TileEntities。
    取标量一律 .value —— 底层 nbt 库的 TAG_Byte/TAG_Int 不是 int 子类,直接当 int 用会炸
    (实测 int(TAG_Byte) 直接 TypeError)。
    """
    for be in chunk.tile_entities:
        yield str(be['id'].value), int(be['x'].value), int(be['y'].value), int(be['z'].value)
