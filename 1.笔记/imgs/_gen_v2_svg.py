# -*- coding: utf-8 -*-
"""重构 10 篇 v2 配图：统一浅色扁平风格，显式 fill，步骤编号与条件标注齐全。"""
import os, io

OUT = os.path.dirname(os.path.abspath(__file__))
FONT = "Microsoft YaHei, sans-serif"
MONO = "Inter, Consolas, monospace"

C = {
    'blue': '#E6F1FB', 'blue_b': '#9CC3E5', 'blue_t': '#1F4E79',
    'green': '#EAF3DE', 'green_b': '#AFCFA0',
    'yellow': '#FAEDA8', 'yellow_b': '#E0C96A',
    'purple': '#EEEDFE', 'purple_b': '#C5C3EC',
    'red': '#FAECE7', 'red_b': '#E7B9AB',
    'orange': '#FDEBD0', 'orange_b': '#EBC48F',
    'ink': '#1F2937', 'sub': '#5A7A99', 'line': '#7A94AD', 'line2': '#4A7FB5',
    'border': '#C9D6E5', 'white': '#FFFFFF', 'warn': '#B45309',
}


def esc(t):
    return str(t).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def tx(x, y, t, size=12, fill=None, anchor='start', bold=False, mono=False):
    fill = fill or C['ink']
    fam = MONO if mono else FONT
    w = ' font-weight="700"' if bold else ''
    return ('<text x="%s" y="%s" font-family="%s" font-size="%s" fill="%s" '
            'text-anchor="%s"%s>%s</text>' % (x, y, fam, size, fill, anchor, w, esc(t)))


def box(x, y, w, h, bg, border=None, rx=8, sw=1, op=None):
    b = ' stroke="%s" stroke-width="%s"' % (border, sw) if border else ''
    o = ' fill-opacity="%s"' % op if op else ''
    return ('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"%s%s/>'
            % (x, y, w, h, rx, bg, o, b))


def whitebox(x, y, w, h, rx=6):
    return box(x, y, w, h, C['white'], None, rx, 0)


def ln(x1, y1, x2, y2, color=None, dash=None, sw=1.5):
    color = color or C['line']
    d = ' stroke-dasharray="%s"' % dash if dash else ''
    return ('<path d="M %s %s L %s %s" fill="none" stroke="%s" stroke-width="%s"%s/>'
            % (x1, y1, x2, y2, color, sw, d))


def poly(points, color=None):
    color = color or C['line']
    return '<polygon points="%s" fill="%s"/>' % (points, color)


def down(x, y1, y2, color=None):
    color = color or C['line']
    return ln(x, y1, x, y2 - 6, color) + poly('%s,%s %s,%s %s,%s' % (
        x, y2, x - 4, y2 - 7, x + 4, y2 - 7), color)


def right(x1, y, x2, color=None):
    color = color or C['line']
    return ln(x1, y, x2 - 6, y, color) + poly('%s,%s %s,%s %s,%s' % (
        x2, y, x2 - 7, y - 4, x2 - 7, y + 4), color)


def left(x1, y, x2, color=None):
    color = color or C['line']
    return ln(x1, y, x2 + 6, y, color) + poly('%s,%s %s,%s %s,%s' % (
        x2, y, x2 + 7, y - 4, x2 + 7, y + 4), color)


def circle(cx, cy, r, bg, border=None, sw=1):
    b = ' stroke="%s" stroke-width="%s"' % (border, sw) if border else ''
    return '<circle cx="%s" cy="%s" r="%s" fill="%s"%s/>' % (cx, cy, r, bg, b)


def num(cx, cy, n, bg=None, fg=None):
    bg = bg or C['blue_t']
    fg = fg or C['white']
    return circle(cx, cy, 12, bg) + tx(cx, cy + 4, str(n), 12, fg, 'middle', True, True)


def card(x, y, w, h, title, tech=None, bg=C['blue'], border=None, tsize=13,
         inner=True, num_n=None, num_bg=None):
    """带白内框的节点卡；num_n 时在左侧画编号圆。"""
    border = border or C['blue_b']
    s = box(x, y, w, h, bg, border, 8)
    if inner:
        s += whitebox(x + 8, y + 7, w - 16, h - 14)
    tx_x = x + 20
    if num_n is not None:
        s += num(x + 22, y + h / 2, num_n, num_bg)
        tx_x = x + 42
    if tech:
        s += tx(tx_x, y + h / 2 - 3, title, tsize, C['ink'], bold=True)
        s += tx(tx_x, y + h / 2 + 14, tech, 10, C['sub'])
    else:
        s += tx(tx_x, y + h / 2 + 5, title, tsize, C['ink'], bold=True)
    return s


def table(head_items, rows, col_x, col_w, row_h, head_y=48, start_y=84,
          head_bg=C['blue_t'], row_bgs=None):
    """手绘表格：head_items=[(label,x,w)]；rows=[[cell,...]]，cell=(text,size,fill,bold,mono)"""
    s = ''
    for label, x, w in head_items:
        s += box(x, head_y, w, 30, head_bg, None, 4)
        s += tx(x + 10, head_y + 20, label, 12, C['white'], bold=True)
    for i, row in enumerate(rows):
        y = start_y + i * row_h
        bg = (row_bgs[i] if row_bgs else (C['white'] if i % 2 == 0 else '#F8FAFD'))
        s += box(col_x, y, sum(col_w), row_h - 4, bg, C['border'], 4)
        cx = col_x
        for j, cell in enumerate(row):
            t = cell[0]
            size = cell[1] if len(cell) > 1 else 12
            fill = cell[2] if len(cell) > 2 else C['ink']
            bold = cell[3] if len(cell) > 3 else False
            mono = cell[4] if len(cell) > 4 else False
            s += tx(cx + 10, y + (row_h - 4) / 2 + 4, t, size, fill, 'start', bold, mono)
            cx += col_w[j]
    return s


def svg(w, h, body, title=None, subtitle=None):
    s = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s" width="%s" height="%s">\n' % (w, h, w, h)
    s += box(0, 0, w, h, C['white'], None, 0, 0) + '\n'
    if title:
        s += tx(24, 28, title, 15, C['blue_t'], bold=True) + '\n'
        s += box(24, 36, 632, 1, C['blue_b'], None, 0, 0) + '\n'
    if subtitle:
        s += tx(24, 54, subtitle, 11, C['sub']) + '\n'
    s += body + '\n</svg>\n'
    return s


def save(name, content):
    io.open(os.path.join(OUT, name), 'w', encoding='utf-8').write(content)
    print('生成', name, len(content), 'bytes')


# ============ 图 1-1 从单次调用到受控多 Agent ============
def fig_1_1():
    s = ''
    s += box(24, 54, 292, 30, '#8FA5B8', None, 5)
    s += tx(38, 74, '单次模型调用', 13, C['white'], bold=True)
    s += box(364, 54, 292, 30, C['blue_t'], None, 5)
    s += tx(378, 74, '受控多 Agent 协作', 13, C['white'], bold=True)

    s += card(24, 94, 292, 66, '输入资料', '人自己备好商品与竞品资料', '#F2F5F8', C['border'])
    s += down(170, 160, 178)
    s += card(24, 178, 292, 66, '一次调用，直接出结果', '中间发生了什么无人知晓', '#F2F5F8', C['border'])
    s += down(170, 244, 262)
    s += card(24, 262, 292, 66, '结构化结果', '好不好只能靠人自己看', '#F2F5F8', C['border'])

    steps = [
        ('运营目标进入', '一句话，不是一串接口顺序'),
        ('路由到已注册业务线', '建立任务与运行，记录版本'),
        ('Agent 依次执行', '每步结果写回共享状态'),
        ('工具受白名单与策略约束', '风险动作暂停等人拍板'),
        ('产出可审核草稿', '不是终稿，先审后定'),
    ]
    for i, (t, d) in enumerate(steps):
        y = 94 + i * 62
        bgs = [C['blue'], C['purple'], C['green'], C['yellow'], C['green']]
        s += card(364, y, 292, 54, t, d, bgs[i], C['border'], 12, num_n=i + 1)
        if i < 4:
            s += down(510, y + 54, y + 62)

    s += box(24, 348, 632, 42, C['red'], C['red_b'], 6)
    s += tx(340, 366, '六处不足：无共享状态 · 无权限边界 · 无质量门 · 无过程记录 · 目标要人拆 · 停不下来等人',
            11, C['ink'], 'middle')
    s += tx(340, 383, '右边每一步都对应一类约束，把左边做不到的补齐', 10, C['sub'], 'middle')
    s += right(316, 250, 362, C['warn'])
    s += tx(339, 240, '演进', 10, C['warn'], 'middle', True)
    save('10_v2_图1-1_从单次调用到受控多Agent.svg', svg(680, 404, s, '从单次调用到受控多 Agent 协作'))


# ============ 图 2-1 坚果案例数据流 ============
def fig_2_1():
    s = card(150, 44, 380, 42, '卖家一句话：分析坚果定位，给主图方向，先审核', None,
             C['blue'], C['blue_b'], 13, True)
    nodes = [
        ('商品上下文节点', '售价、成本、人群、竞品', C['blue']),
        ('诊断节点', '定位、价格带、风险 · 商品策略', C['purple']),
        ('创意策略节点', '几版主图方向与画面提示词', C['green']),
        ('质量合规节点', '数量、差异度、不当承诺', C['yellow']),
        ('人工审核节点', '暂停，等待卖家拍板', C['orange']),
        ('收尾落库节点', '通过则保存，驳回不落库', C['green']),
    ]
    y0 = 100
    for i, (t, d, bg) in enumerate(nodes):
        y = y0 + i * 56
        s += card(150, y, 380, 48, t, d, bg, C['border'], 12, num_n=i + 1)
        if i < 5:
            s += down(340, y + 48, y + 56)
    # 返修回路标注（挂在第4节点右侧）
    s += ln(530, 268, 556, 268, C['warn'], '4 3')
    s += ln(556, 268, 556, 156, C['warn'], '4 3')
    s += left(556, 156, 532, C['warn'])
    s += tx(562, 220, '未通过', 10, C['warn'], bold=True)
    s += tx(562, 234, '且未超上限', 10, C['warn'])
    s += tx(562, 248, '回诊断重跑', 10, C['warn'])

    s += box(24, 442, 632, 46, '#F8FAFD', C['border'], 6)
    s += tx(36, 462, '共享状态逐步填充：', 11, C['blue_t'], bold=True)
    s += tx(36, 479, '上下文 → 诊断草稿 → 创意方案列表 → 质量报告 → 审核决定 → 采用内容',
            11, C['sub'])
    s += tx(656, 462, '返修次数与用量同步累加；快照先脱敏再写事件', 10, C['sub'], 'end')
    s += box(24, 498, 632, 40, C['orange'], C['orange_b'], 6)
    s += tx(36, 515, '两条纪律', 11, C['warn'], bold=True)
    s += tx(100, 515, '「低糖」不能扩写成「无糖」「保证减肥」，自动检查只是辅助', 11, C['ink'])
    s += tx(36, 531, '批准采用的主图方向仍是文字方案，真出图继续走后台生成任务', 11, C['sub'])
    save('10_v2_图2-1_坚果案例数据流.svg', svg(680, 546, s, '坚果案例的一次完整执行'))


# ============ 图 2-2 多 Agent 全景分层 ============
def fig_2_2():
    s = ''
    layers = [
        ('运行与接口层', '接口收目标返结果，运行层管认领、事件、状态、恢复与回收',
         '卖家看到「待审核」，是运行层把状态推过去的', C['blue']),
        ('编排层', '决定节点顺序、分支条件与暂停点，不直接碰数据或模型',
         '基础图把诊断排在创意前面', C['purple']),
        ('执行层', 'Harness 模块、工具网关、专业节点，脱敏预算与规则兜底',
         '诊断节点调模型出草稿，网关做租约与幂等校验', C['green']),
        ('注册与策略层', '注册表与策略：九个 Agent、十六项工具、七条业务线与风险判定',
         '声明谁可用什么，不决定执行先后', C['yellow']),
        ('合同层', '上下文、草稿、质量报告、事件、共享状态',
         '节点之间能交换什么数据在这里定死', C['orange']),
    ]
    for i, (name, duty, note, bg) in enumerate(layers):
        y = 66 + i * 82
        s += box(24, y, 632, 74, bg, C['border'], 6)
        s += box(24, y, 148, 74, bg, None, 6)
        s += box(148, y, 2, 74, C['border'], None, 0, 0)
        s += tx(40, y + 32, name, 13, C['blue_t'], bold=True)
        s += tx(40, y + 52, '第 %d 层' % (5 - i), 10, C['sub'], mono=True)
        s += whitebox(160, y + 8, 484, 58)
        s += tx(174, y + 30, duty, 12, C['ink'])
        s += tx(174, y + 50, note, 10, C['sub'])
        s += num(636, y + 18, 5 - i, bg=C['blue_t'])
    s += box(24, 484, 632, 34, '#F8FAFD', C['border'], 6)
    s += tx(36, 505, '硬规矩：节点只通过结构化状态和受控工具交换数据，不许绕过策略边界直接写结果',
            11, C['ink'])
    s += tx(644, 505, '约束由上到下逐渐变硬', 10, C['sub'], 'end')
    save('10_v2_图2-2_多Agent全景分层.svg', svg(680, 528, s, '多 Agent 全景分层（一次请求的纵向剖面）'))


# ============ 图 2-3 注册表三件套关系 ============
def fig_2_3():
    s = ''
    s += card(24, 52, 200, 82, 'Agent 注册表', '九个 Agent + 工具白名单', C['blue'], C['blue_b'], 12)
    s += card(240, 52, 200, 82, '工具注册表', '十六项工具 + R0 至 R3', C['green'], C['green_b'], 12)
    s += card(456, 52, 200, 82, '工作流注册表', '七条业务线 + Agent 顺序', C['purple'], C['purple_b'], 12)
    # 连线标注
    s += right(224, 78, 238, C['blue_t'])
    s += tx(231, 70, '白名单', 9, C['blue_t'], 'middle')
    s += ln(224, 110, 238, 110, C['blue_t'])
    s += tx(231, 102, '被引用', 9, C['blue_t'], 'middle')
    s += ln(456, 78, 442, 78, C['blue_t'])
    s += tx(449, 70, '顺序', 9, C['blue_t'], 'middle')
    s += tx(556, 146, '执行顺序由此推导，节点按声明顺序串联', 10, C['sub'], 'middle')
    s += tx(340, 146, '风险级别写在工具上，不由 Agent 单独决定', 10, C['sub'], 'middle')

    s += tx(24, 174, '一次判定的完整链条（从左到右）', 12, C['blue_t'], bold=True)
    chain = ['Agent\n是否注册', '工具\n是否注册', '在白\n名单内', '工作区\n身份', '所有者\n专用?', '风险\n要审批?']
    cx = 24
    for i, t in enumerate(chain):
        s += box(cx, 186, 96, 48, C['blue'] if i < 5 else C['orange'], C['border'], 6)
        lines = t.split('\n')
        s += tx(cx + 48, 205, lines[0], 10, C['ink'], 'middle', True)
        s += tx(cx + 48, 220, lines[1], 10, C['ink'], 'middle', True)
        if i < 5:
            s += right(cx + 96, 210, cx + 106)
        cx += 108
    s += tx(24, 254, '坚果的诊断草稿工具：前五步都通过 → R1 不需审批 → 放行', 11, C['blue_t'])

    s += tx(24, 282, '三条容易记错的规则', 12, C['blue_t'], bold=True)
    rules = [
        ('注册 ≠ 可执行', '网关没适配器照样拒绝'),
        ('只读成员', '只能执行 R0 级工具'),
        ('所有者专用', '只有工作区所有者可用'),
    ]
    for i, (t, d) in enumerate(rules):
        x = 24 + i * 214
        s += card(x, 294, 204, 66, t, d, C['yellow'], C['yellow_b'], 12)
    s += tx(24, 380, '业务线名称只表达方向，不等同于已经接通外部系统', 10, C['sub'])
    save('10_v2_图2-3_注册表三件套关系.svg', svg(680, 400, s, '注册表三件套的关系'))


# ============ 图 2-4 运行时拓扑 ============
def fig_2_4():
    s = ''
    tops = [
        ('接口层', '创建任务与运行', C['blue']),
        ('消息中间件', '三类队列', C['purple']),
        ('后台 Worker', '认领租约并执行', C['green']),
        ('工具网关', '租约·幂等·复核', C['yellow']),
        ('业务服务', '已有能力原样调用', C['orange']),
    ]
    x = 24
    for i, (t, d, bg) in enumerate(tops):
        s += card(x, 60, 118, 64, t, d, bg, C['border'], 12)
        if i < 4:
            s += right(x + 118, 92, x + 130)
        x += 130
    s += tx(24, 140, '运行 / 工作流 / 维护三类队列耗时特征不同，混一条会互相阻塞', 10, C['sub'])

    s += card(300, 156, 300, 46, '维护与周期任务：投递待发消息 · 回收到期与超时运行',
              None, '#F2F5F8', C['border'], 11, False)
    s += ln(420, 156, 420, 126, C['line'], '4 3')
    s += ln(600, 156, 600, 190, C['line'], '4 3')

    s += card(24, 224, 300, 118, '业务数据库', '任务 · 运行 · 事件 · 操作 · 审批 · 产物', C['blue'], C['blue_b'], 13)
    s += tx(40, 300, '使用者可见的业务事实', 11, C['blue_t'], bold=True)
    s += tx(40, 320, '用于审计，不能只存在于内存', 10, C['sub'])
    s += card(356, 224, 300, 118, '检查点数据库', '图的中间状态，按线程标识保存', C['purple'], C['purple_b'], 13)
    s += tx(372, 300, '只用于技术恢复', 11, '#6D5FB5', bold=True)
    s += tx(372, 320, '不能替代业务库做审计', 10, C['sub'])
    s += ln(174, 202, 174, 222)
    s += ln(506, 202, 506, 222)

    s += box(24, 356, 632, 42, C['red'], C['red_b'], 6)
    s += tx(340, 374, '两条写入线彼此独立，缺一不可', 11, C['ink'], 'middle', True)
    s += tx(340, 391, '只写业务库：中断后无法从断点续跑　|　只写检查点：事后无法审计', 10, C['sub'], 'middle')
    save('10_v2_图2-4_运行时拓扑.svg', svg(680, 408, s, '运行时拓扑'))


# ============ 图 3-1 Harness 边界环绕 ============
def fig_3_1():
    s = ''
    rings = [
        (24, 44, 632, 452, C['red'], C['red_b'], '边界之外：模型供应商与外部系统', None),
        (56, 76, 568, 388, C['orange'], C['orange_b'], '第五层：副作用边界', '写入正式业务对象必须经人工审批，同一运行只接受一次最终决定'),
        (88, 108, 504, 324, C['green'], C['green_b'], '第四层：时间边界', '租约五分钟、心跳六十秒、软硬超时 1700 / 1800 秒，到期回收'),
        (120, 140, 440, 260, C['yellow'], C['yellow_b'], '第三层：预算边界', '总预算一万二千 Token，调用前截断，耗尽即熔断'),
        (152, 172, 376, 196, C['purple'], C['purple_b'], '第二层：权限边界', '白名单、工作区身份、所有者专用、风险级别'),
        (184, 204, 312, 132, C['blue'], C['blue_b'], '第一层：结构边界', '只交换定义过的结构，多余字段直接拒绝'),
    ]
    for x, y, w, h, bg, bd, title, note in rings:
        s += box(x, y, w, h, bg, bd, 10, 1)
        s += box(x + 44, y - 1, 180, 1, C['white'], None, 0, 0)
        s += tx(x + 16, y + 22, title, 12, C['ink'], bold=True)
        if note:
            s += tx(x + 16, y + 39, note, 10, C['sub'])
    s += box(248, 252, 184, 62, C['white'], C['blue_b'], 8)
    s += tx(340, 277, 'Agent 节点', 13, C['blue_t'], 'middle', True)
    s += tx(340, 295, '负责做什么', 11, C['sub'], 'middle')
    s += tx(340, 309, '不负责能做什么', 10, C['sub'], 'middle')
    s += tx(340, 392, 'Harness 负责「在什么范围内做」', 12, C['blue_t'], 'middle', True)
    s += tx(340, 418, '任何一次对外访问都必须穿过全部五层', 11, C['ink'], 'middle')
    s += tx(340, 438, '穿不过去，不是被拒绝，而是根本不会发生', 10, C['sub'], 'middle')
    save('10_v2_图3-1_Harness边界环绕.svg', svg(680, 506, s, 'Harness 的边界环绕结构'))


# ============ 图 3-2 四类失控与防线 ============
def fig_3_2():
    s = ''
    heads = [('四类失控（坚果场景）', 24, 200), ('对应防线', 232, 200), ('承担模块', 440, 216)]
    s += ''
    for label, x, w in heads:
        s += box(x, 52, w, 30, C['blue_t'], None, 4)
        s += tx(x + 10, 72, label, 12, C['white'], bold=True)
    rows = [
        ('越界读取', '读到别家竞品数据', '按工作区过滤并校验归属，越界直接拒绝，不返回部分结果', '上下文加载 + 工具网关', C['red']),
        ('无限循环', '质量不过一直返修', '返修次数上限，超限交人工；默认一次，可配零到三次', '基础图 + 共享状态', C['orange']),
        ('重复副作用', '重投存了两遍', '独占租约加幂等操作键，已完成的操作直接返回旧结果', '租约模块 + 工具网关', C['yellow']),
        ('成本与不可追溯', '消耗无人统计、过程不落库', '预算熔断、脱敏事件；开始/完成/失败三步留痕，含链路标识', 'Harness + 运行服务', C['green']),
    ]
    y = 90
    for i, (risk, scene, defense, mod, bg) in enumerate(rows):
        s += box(24, y, 200, 72, bg, C['border'], 5)
        s += tx(36, y + 30, risk, 12, C['ink'], bold=True)
        s += tx(36, y + 50, scene, 10, C['sub'])
        s += box(232, y, 200, 72, C['white'], C['border'], 5)
        lines = [defense[j:j + 16] for j in range(0, len(defense), 16)]
        for k, line in enumerate(lines[:3]):
            s += tx(242, y + 24 + k * 16, line, 10, C['ink'])
        s += box(440, y, 216, 72, C['white'], C['border'], 5)
        s += tx(452, y + 34, mod, 11, C['blue_t'], bold=True)
        y += 80
    s += tx(24, y + 6, '四类风险都不是模型能力问题，而是工程缺失问题；防线全部落在工程约束上',
            11, C['blue_t'])
    save('10_v2_图3-2_失控与防线对照.svg', svg(680, y + 26, s, '四类失控与对应的防线'))


# ============ 图 4-1 边界与目标矩阵 ============
def fig_4_1():
    s = ''
    s += box(24, 52, 396, 30, C['blue_t'], None, 5)
    s += tx(36, 72, '五类边界：守什么 / 具体阈值', 12, C['white'], bold=True)
    borders = [
        ('数据边界', '看得见什么', '按工作区过滤，商品与店铺越界即拒', C['blue']),
        ('权限边界', '能用哪个', '白名单不匹配拒，只读成员仅 R0，所有者专用独占', C['purple']),
        ('预算边界', '能消耗多少', '默认 12000 Token，调用前截断，为零即熔断', C['yellow']),
        ('时间边界', '能执行多久', '租约 5 分钟 / 心跳 60 秒 / 软硬超时 1700、1800 秒', C['green']),
        ('副作用边界', '能不能写', 'R2 与 R3 必须审批，通过才落库，只接受一次决定', C['orange']),
    ]
    y = 90
    for name, what, rule, bg in borders:
        s += box(24, y, 396, 66, bg, C['border'], 5)
        s += tx(36, y + 26, name, 12, C['blue_t'], bold=True)
        s += tx(110, y + 26, what, 11, C['ink'])
        s += tx(36, y + 47, rule, 10, C['sub'])
        y += 74

    s += box(436, 52, 220, 30, C['blue_t'], None, 5)
    s += tx(448, 72, '五个可靠性目标（一条链）', 12, C['white'], bold=True)
    goals = ['幂等 · 重试安全', '可恢复 · 不丢工作', '可观测 · 过程留痕', '可审计 · 决定可追溯', '可解释 · 知道怎么改']
    gy = 90
    for i, g in enumerate(goals):
        s += card(436, gy, 220, 48, g, None, C['blue'] if i < 2 else C['green'], C['border'], 11, True, num_n=i + 1)
        if i < 4:
            s += down(546, gy + 48, gy + 58)
        gy += 58
    s += tx(24, 452, '预算边界是调用前截断，不是事后统计；坚果诊断申请 2200、创意 3000，都在剩余额度内核定',
            11, C['ink'])
    save('10_v2_图4-1_边界与目标矩阵.svg', svg(680, 468, s, '五类边界与五个可靠性目标'))


# ============ 图 4-2 七步应用流程 ============
def fig_4_2():
    s = ''
    steps = [
        ('定合同', '声明可交换的数据结构，禁止多余字段', '合同模块', '校验不过，节点进不来'),
        ('做注册', '声明 Agent、工具、业务线与版本', '注册表模块', '未注册的直接报错'),
        ('判授权', '按白名单、身份与风险给允许/拒绝/需审批', '策略模块', '越权被拒，高风险转审批'),
        ('走网关', '执行前复核租约、执行中幂等防重、执行后记录', '工具网关模块', '租约失效拒绝执行'),
        ('记事件', '开始、完成、失败都写事件，先脱敏', '运行服务', '不阻塞执行，但丢了查不到'),
        ('过质量门', '结构、依据、风险检查，给分数与问题清单', '专业节点与质量规则', '未通过且有次数则返修'),
        ('审批落库', '高风险动作等人决定，通过才写正式对象', '任务服务与审批记录', '驳回进已驳回终态'),
    ]
    y = 54
    for i, (name, do, who, fail) in enumerate(steps):
        s += box(24, y, 632, 50, C['white'] if i % 2 == 0 else '#F8FAFD', C['border'], 5)
        s += num(46, y + 25, i + 1)
        s += tx(68, y + 22, name, 12, C['blue_t'], bold=True)
        s += tx(68, y + 39, do, 10, C['ink'])
        s += tx(392, y + 22, who, 10, C['sub'], bold=True)
        s += tx(392, y + 39, fail, 10, C['warn'])
        if i < 6:
            s += down(340, y + 50, y + 56)
        y += 56
    s += box(24, y + 4, 310, 74, C['orange'], C['orange_b'], 6)
    s += tx(38, y + 26, '两处「停下来」', 11, C['warn'], bold=True)
    s += tx(38, y + 45, '第三步：高风险停等审批，未拿到不执行', 10, C['ink'])
    s += tx(38, y + 62, '第七步：人审停等拍板，暂停前零副作用', 10, C['ink'])
    s += box(346, y + 4, 310, 74, C['blue'], C['blue_b'], 6)
    s += tx(360, y + 26, '顺序不能颠倒的理由', 11, C['blue_t'], bold=True)
    s += tx(360, y + 45, '先注册再授权：没声明过无从判断', 10, C['ink'])
    s += tx(360, y + 62, '先执行再记录：记的是结果，事后可回放', 10, C['ink'])
    save('10_v2_图4-2_七步应用流程.svg', svg(680, y + 92, s, 'Harness 应用步骤七步法'))


# ============ 图 5-1 基础工作流图 ============
def fig_5_1():
    s = ''
    s += card(268, 48, 148, 40, '开始', '目标与范围已确定', C['blue'], C['blue_b'], 12, True)
    nodes = [
        ('商品上下文节点', '读资料，不调模型', C['blue']),
        ('诊断节点', '商品策略 · 调模型', C['purple']),
        ('创意策略节点', '调模型，有兜底', C['green']),
        ('质量合规节点', '纯规则，不调模型', C['yellow']),
    ]
    y = 104
    for i, (t, d, bg) in enumerate(nodes):
        s += card(268, y, 148, 46, t, d, bg, C['border'], 11, num_n=i + 1)
        if i < 3:
            s += down(342, y + 46, y + 54)
        y += 54
    # 分叉点 y ~= 320
    fy = 320
    s += tx(342, fy - 6, '质量判定', 10, C['sub'], 'middle')
    s += ln(342, fy, 342, fy + 20, C['line'])
    s += ln(120, fy + 20, 566, fy + 20, C['line'])
    s += down(120, fy + 20, fy + 46, C['warn'])
    s += down(566, fy + 20, fy + 46)
    s += tx(230, fy + 14, '通过或已达上限', 10, C['sub'], 'end')
    s += tx(452, fy + 14, '未通过且未超上限 → 返修', 10, C['warn'])
    # 返修节点（左）
    s += card(46, fy + 46, 148, 52, '准备返修节点', '次数加一并整理反馈', C['red'], C['red_b'], 11, num_n=5)
    s += ln(120, fy + 98, 120, 156, C['warn'], '4 3')
    s += right(120, 156, 266, C['warn'])
    s += tx(160, 176, '回到诊断重跑', 10, C['warn'])
    # 人审（右）
    s += card(492, fy + 46, 148, 52, '人工审核节点', '暂停等待拍板', C['orange'], C['orange_b'], 11, num_n=6)
    s += down(566, fy + 98, fy + 118)
    s += card(492, fy + 118, 148, 52, '收尾落库节点', '通过保存，驳回不存', C['green'], C['green_b'], 11, num_n=7)
    s += left(492, fy + 144, 420, C['line'])
    s += card(268, fy + 118, 148, 52, '结束', '已完成或已驳回', '#F2F5F8', C['border'], 12, True)
    # 底部说明
    by = fy + 190
    s += box(24, by, 632, 44, '#F8FAFD', C['border'], 6)
    s += tx(36, by + 20, '四个业务 Agent（上下文 / 诊断 / 创意 / 质量）＋ 三个控制节点（返修 / 人审 / 收尾）＝ 七个节点',
            11, C['ink'])
    s += tx(36, by + 37, '控制节点不是新 Agent：返修只整理反馈、人审只暂停、收尾只按决定写库', 10, C['sub'])
    save('10_v2_图5-1_基础工作流图.svg', svg(680, by + 56, s, '基础工作流图（商品诊断与优化）'))


# ============ 图 5-2 平台工作流图 ============
def fig_5_2():
    s = ''
    chain = [
        ('加载上下文', '按范围加载', C['blue']),
        ('领域节点一', '首个 Agent', C['purple']),
        ('… 领域节点', '数量不固定', C['purple']),
        ('质量合规', '末尾查全部', C['yellow']),
        ('审批门', 'R2/R3 才有', C['orange']),
        ('收尾节点', '写正式对象', C['green']),
    ]
    x = 24
    for i, (t, d, bg) in enumerate(chain):
        s += card(x, 60, 100, 68, t, d, bg, C['border'], 11, True)
        if i < 5:
            s += right(x + 100, 94, x + 110)
        x += 110
    s += down(384, 128, 158, C['warn'])
    s += card(316, 158, 136, 46, '质量失败终态', '未通过且不再返修', C['red'], C['red_b'], 11)
    s += tx(520, 150, 'R0 / R1 直接由质量连收尾', 10, C['sub'])
    s += tx(520, 168, '不插入审批门', 10, C['sub'])

    s += tx(24, 226, '四条装配规则', 12, C['blue_t'], bold=True)
    rules = [
        ('一、固定加载上下文', '按商品或店铺范围加载'),
        ('二、按声明顺序串联', '质量合规跳过，固定末尾'),
        ('三、质量节点放末尾', '检查全部领域输出'),
        ('四、按风险插审批门', 'R2 与 R3 才有'),
    ]
    for i, (t, d) in enumerate(rules):
        x = 24 + (i % 2) * 322
        y = 238 + (i // 2) * 62
        s += card(x, y, 312, 54, t, d, C['blue'] if i % 2 == 0 else C['green'], C['border'], 11, num_n=i + 1)
    s += box(24, 370, 632, 44, C['orange'], C['orange_b'], 6)
    s += tx(340, 388, '加一条业务线不用再写一张图', 12, C['warn'], 'middle', True)
    s += tx(340, 405, '节点数量、顺序、插不插审批门，全部由注册表声明推导', 10, C['ink'], 'middle')
    save('10_v2_图5-2_平台工作流图.svg', svg(680, 424, s, '平台工作流图（注册表动态装配）'))


# ============ 图 5-3 六道闸门时序 ============
def fig_5_3():
    s = ''
    s += ln(40, 214, 644, 214, C['blue_t'], None, 2)
    s += poly('644,214 637,210 637,218', C['blue_t'])
    s += tx(24, 56, '一次运行的时间轴　→', 11, C['blue_t'], bold=True)
    gates = [
        ('一', '租约认领', '租约模块', '运行前', '两个 Worker 同时执行', C['blue']),
        ('二', '幂等操作键', '工具网关', '每次调用前', '重投造成重复副作用', C['purple']),
        ('三', '预算扣减', 'Harness', '调模型前', '多轮调用超出预算', C['yellow']),
        ('四', '超时与维护', '维护模块', '运行期间', '崩溃或超时长期占资源', C['green']),
        ('五', '审批门', '任务服务', '落库之前', '未确认就写入正式对象', C['orange']),
        ('六', '检查点恢复', '持久化+运行', '暂停之后', '中断后从头重跑', C['blue']),
    ]
    x = 24
    for i, (n, name, who, when, guard, bg) in enumerate(gates):
        s += box(x, 70, 100, 138, bg, C['border'], 6)
        s += num(x + 50, 90, i + 1, C['blue_t'])
        s += tx(x + 50, 116, name, 11, C['ink'], 'middle', True)
        s += tx(x + 50, 136, who, 9, C['sub'], 'middle')
        s += box(x + 8, 146, 84, 1, C['border'], None, 0, 0)
        s += tx(x + 50, 162, when, 9, C['blue_t'], 'middle')
        s += tx(x + 50, 180, '防住：', 9, C['warn'], 'middle', True)
        lines = [guard[j:j + 8] for j in range(0, len(guard), 8)]
        for k, l in enumerate(lines[:3]):
            s += tx(x + 50, 194 + k * 11, l, 9, C['sub'], 'middle')
        s += ln(x + 50, 208, x + 50, 214, C['line'])
        x += 110
    s += tx(24, 244, '六道里有三道都在防重复，但不是冗余，因为重复来源不同', 11, C['blue_t'], bold=True)
    dup = [
        ('租约', '防并发重复', '两个 Worker 同时认领'),
        ('幂等键', '防重放重复', '队列把同一条消息又投一次'),
        ('检查点恢复', '防重跑重复', '中断后节点从头执行'),
    ]
    for i, (t, d, src) in enumerate(dup):
        x = 24 + i * 214
        s += card(x, 256, 204, 72, t, d, C['blue'] if i != 1 else C['purple'], C['border'], 11)
        s += tx(x + 20, 312, '来源：' + src, 9, C['sub'])
    save('10_v2_图5-3_六道闸门时序.svg', svg(680, 344, s, '一次运行的六道闸门时序'))


# ============ 图 5-4 任务与运行关系 ============
def fig_5_4():
    s = ''
    s += card(24, 54, 280, 118, '任务：卖家的业务目标', '业务线 · 标题 · 意图 · 范围 · 风险', C['blue'], C['blue_b'], 13)
    s += tx(40, 116, '结果摘要 · 版本清单 · 取消时间', 10, C['sub'])
    s += tx(40, 142, '坚果「给这商品做诊断优化」是一个任务', 10, C['blue_t'])
    s += card(376, 54, 280, 118, '运行：某次技术执行实例', '线程标识 · 尝试次数 · 状态 · 预算用量', C['purple'], C['purple_b'], 13)
    s += tx(392, 116, '草稿 · 质量报告 · 租约与超时', 10, C['sub'])
    s += tx(392, 142, '同一个任务可以有多次运行', 10, '#6D5FB5')
    s += right(304, 96, 374, C['blue_t'])
    s += tx(340, 88, '一对多', 10, C['blue_t'], 'middle', True)
    s += right(304, 132, 374, C['blue_t'])

    runs = [
        ('运行一 · 首次执行', '尝试次数为一，可能停在待审核', C['blue']),
        ('运行二 · 恢复执行', '同一线程标识，收到决定后继续', C['green']),
        ('运行三 · 重试执行', '次数累加，用量账本继续累计', C['yellow']),
    ]
    for i, (t, d, bg) in enumerate(runs):
        x = 24 + i * 214
        s += card(x, 190, 204, 66, t, d, bg, C['border'], 11, num_n=i + 1)
    s += box(24, 272, 632, 50, '#F8FAFD', C['border'], 6)
    s += tx(36, 292, '为什么分两层：目标不会因一次技术失败而消失，重试与恢复只换运行、不重建任务', 11, C['ink'])
    s += tx(36, 310, '界面展示任务进度，排查看运行事件', 10, C['sub'])
    s += box(24, 332, 632, 50, C['orange'], C['orange_b'], 6)
    s += tx(36, 352, '两张表状态同步：运行推进时任务跟随更新', 11, C['ink'], bold=True)
    s += tx(36, 370, '检查点只管技术恢复，替代不了业务库里的运行事实', 10, C['sub'])
    s += tx(340, 402, '任务回答「要什么」，运行回答「这次跑得怎么样」', 11, C['blue_t'], 'middle', True)
    save('10_v2_图5-4_任务与运行关系.svg', svg(680, 416, s, '任务与运行的关系'))


# ============ 图 5-5 运行状态机 ============
def fig_5_5():
    s = ''
    states = {
        'q': (40, 60, '已入队', C['blue']),
        'run': (266, 60, '执行中', C['purple']),
        'rev': (492, 60, '待审核', C['orange']),
        'resume': (492, 190, '恢复入队', C['yellow']),
        'done': (266, 320, '已完成', C['green']),
        'reject': (40, 320, '已驳回', C['red']),
        'fail': (492, 320, '失败', C['red']),
        'cancel': (266, 410, '已取消', '#F2F5F8'),
    }
    for k, (x, y, t, bg) in states.items():
        s += card(x, y, 148, 50, t, None, bg, C['border'], 12, True)
    # 转移箭头
    s += right(188, 85, 264) ; s += tx(226, 78, '认领', 9, C['sub'], 'middle')
    s += right(414, 85, 490) ; s += tx(452, 78, '暂停', 9, C['sub'], 'middle')
    s += down(566, 110, 188, C['orange']) ; s += tx(578, 150, '收到决定', 9, C['sub'])
    s += left(490, 215, 416, C['orange']) ; s += tx(452, 208, '再次认领', 9, C['sub'], 'middle')
    s += ln(340, 110, 340, 318, C['line'])
    s += down(340, 300, 318, C['line'])
    s += tx(350, 170, '执行完成且审核通过', 9, C['sub'])
    s += ln(266, 340, 190, 340, C['warn']) ; s += poly('190,340 197,336 197,344', C['warn'])
    s += tx(228, 333, '驳回', 9, C['warn'], 'middle')
    s += right(414, 340, 490, C['warn']) ; s += tx(452, 333, '出错 / 超时', 9, C['warn'], 'middle')
    s += ln(566, 370, 566, 410, C['line']) ; s += ln(566, 410, 414, 410, C['line'])
    s += poly('414,410 421,406 421,414', C['line'])
    s += tx(470, 402, '主动取消', 9, C['sub'], 'middle')

    s += box(24, 476, 632, 56, '#F8FAFD', C['border'], 6)
    s += tx(36, 496, '八个状态，四个终态，含义不同不能混用', 11, C['blue_t'], bold=True)
    s += tx(36, 515, '已完成＝通过并落库　|　已驳回＝人工不采用、未落库　|　失败＝出错或超时，可按策略重试　|　已取消＝卖家主动动作',
            10, C['ink'])
    save('10_v2_图5-5_运行状态机.svg', svg(680, 542, s, '一次运行的状态机'))


if __name__ == '__main__':
    fig_1_1()
    fig_2_1()
    fig_2_2()
    fig_2_3()
    fig_2_4()
    fig_3_1()
    fig_3_2()
    fig_4_1()
    fig_4_2()
    fig_5_1()
    fig_5_2()
    fig_5_3()
    fig_5_4()
    fig_5_5()
    print('全部 14 张图生成完成')
