"""은하 전투기 자동 재생 SVG (README 용 · 스크립트 없이 CSS 만으로 움직인다)

python tools/make_space_svg.py  →  assets/space-fighter.svg

장면: 전투기가 세 줄(가운데 · 위 · 아래)을 오가며, 오른쪽에서 오는 적기를 레이저로 맞혀 터뜨린다.
적기 · 레이저 · 폭발은 모두 같은 주기(P)를 돌고, 시작 시각은 음수 지연으로 맞춘다
(양수 지연이면 시작 전에 기본 자리에 그림이 보인다).
"""
import os, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PX = 4
W, H = 960, 240
P = 6.0
LANES = [124, 68, 180]         # 구간마다 전투기가 가는 줄(가운데 · 위 · 아래)
SEG = P / len(LANES)
PLAYER_X = 120
FOE_V = 260                     # 적기 속도 px/s
BOLT_V = 900                    # 레이저 속도 px/s

PAL = {
    'W': '#D8DEE6', 'w': '#9AA5B1', 'R': '#E5484D', 'C': '#7D8794', 'E': '#FFB347', 'B': '#6EC1FF',
    'D': '#4A5361', 'd': '#2B313B', 'G': '#5CF08B', 'K': '#14181F',
}
# 게임 페이지(game/space)와 같은 도트. 위(적기는 아래)를 보는 그림을 돌려 쓴다
PLAYER = [
    '.......W.......', '.......W.......', '......WBW......', '......WBW......',
    '.C....WWW....C.', '.C....WRW....C.', '.C....WRW....C.', '.C...wWWWw...C.',
    '.WWWWWWWWWWWWW.', '.WRRWWWWWWWRRW.', '..wWWWWWWWWWw..', '......WWW......',
    '.....wWWWw.....', '.....E...E.....',
]
FIGHTER = [
    'dd.......dd', 'dDd.....dDd', 'dDDd...dDDd', 'dDDdDDDdDDd', 'dDDDGGGDDDd',
    'dDDdGKGdDDd', 'dDDd.G.dDDd', 'dDd.....dDd', 'dd.......dd',
]


def rot_cw(grid):
    """시계 방향 90도: 위를 보던 그림이 오른쪽을, 아래를 보던 그림이 왼쪽을 본다"""
    h = len(grid)
    return [''.join(grid[h - 1 - j][i] for j in range(h)) for i in range(len(grid[0]))]


def sprite(grid, cx, cy):
    w, h = len(grid[0]) * PX, len(grid) * PX
    ox, oy = cx - w / 2, cy - h / 2
    out = []
    for y, row in enumerate(grid):
        x = 0
        while x < len(row):
            ch = row[x]
            if ch in PAL:
                s = x
                while x < len(row) and row[x] == ch:
                    x += 1
                out.append(f'<rect x="{ox + s * PX:.0f}" y="{oy + y * PX:.0f}" width="{(x - s) * PX}" height="{PX}" fill="{PAL[ch]}"/>')
            else:
                x += 1
    return ''.join(out)


def neg_delay(t):
    """주기 안의 시작 시각 t → 음수 지연(-P < d <= 0)"""
    t %= P
    return -(P - t) if t > 0 else 0.0


def pct(t):
    return f'{t / P * 100:.3f}%'


def build():
    ply = rot_cw(PLAYER)
    foe = rot_cw(rot_cw(rot_cw(FIGHTER)))  # 아래를 보던 적기를 왼쪽으로
    css, body = [], []

    # 전투기: 구간 시작마다 다음 줄로 0.3초 동안 옮긴다
    kf = []
    for k, y in enumerate(LANES):
        t0 = k * SEG
        prev = LANES[k - 1]
        kf.append(f'{pct(t0)}{{transform:translateY({prev - LANES[0]}px)}}')
        kf.append(f'{pct(t0 + 0.3)}{{transform:translateY({y - LANES[0]}px)}}')
    kf.append(f'100%{{transform:translateY({LANES[-1] - LANES[0]}px)}}')
    css.append('@keyframes ply{' + ''.join(kf) + '}')
    css.append(f'.ply{{animation:ply {P}s cubic-bezier(.5,0,.2,1) infinite}}')

    # 줄마다 적기 두 대: 하나는 줄에 자리 잡자마자, 하나는 조금 뒤에 맞힌다
    shots = []
    for lane, y in enumerate(LANES):
        shots.append((y, lane * SEG + 0.42))
        shots.append((y, lane * SEG + 1.25))
    wing = (len(PLAYER[0]) // 2 - 1) * PX      # 날개 끝 포의 위아래 거리
    for k, (y, f) in enumerate(shots):
        s = f - 1.05                  # 적기가 화면 오른쪽 끝에 나타나는 시각
        x0, b0 = W + 40, PLAYER_X + len(PLAYER) * PX // 2
        meet = (x0 + FOE_V * s - b0 + BOLT_V * f) / (FOE_V + BOLT_V)
        mx = x0 - FOE_V * (meet - s)
        # 적기: 나타나 → 맞는 자리까지 → 사라짐
        live = meet - s
        css.append(
            f'@keyframes f{k}{{0%{{transform:translateX(0);opacity:1}}{pct(live)}{{transform:translateX({mx - x0:.0f}px);opacity:1}}'
            f'{pct(live + 0.01)},100%{{transform:translateX({mx - x0:.0f}px);opacity:0}}}}'
            f'.f{k}{{animation:f{k} {P}s linear infinite;animation-delay:{neg_delay(s):.3f}s}}')
        body.append(f'<g class="f{k}">{sprite(foe, x0, y)}</g>')
        # 레이저 두 줄기(날개 끝)
        fly = meet - f
        css.append(
            f'@keyframes b{k}{{0%{{transform:translateX(0);opacity:1}}{pct(fly)}{{transform:translateX({mx - b0:.0f}px);opacity:1}}'
            f'{pct(fly + 0.01)},100%{{transform:translateX({mx - b0:.0f}px);opacity:0}}}}'
            f'.b{k}{{animation:b{k} {P}s linear infinite;animation-delay:{neg_delay(f):.3f}s}}')
        body.append(
            f'<g class="b{k}">'
            f'<rect x="{b0}" y="{y - wing - 3}" width="26" height="7" fill="#E5484D" opacity=".35"/><rect x="{b0 + 1}" y="{y - wing - 1}" width="24" height="3" fill="#FF8A8D"/>'
            f'<rect x="{b0}" y="{y + wing - 3}" width="26" height="7" fill="#E5484D" opacity=".35"/><rect x="{b0 + 1}" y="{y + wing - 1}" width="24" height="3" fill="#FF8A8D"/></g>')
        # 적의 반격: 초록 탄이 전투기 위나 아래로 빗나간다
        e0 = s + 0.35
        ex = x0 - FOE_V * 0.35
        ey = y + (34 if k % 2 else -34)
        efly = (ex + 40) / 520
        css.append(
            f'@keyframes e{k}{{0%{{transform:translateX(0);opacity:1}}{pct(efly)}{{transform:translateX({-ex - 40:.0f}px);opacity:1}}'
            f'{pct(efly + 0.01)},100%{{transform:translateX({-ex - 40:.0f}px);opacity:0}}}}'
            f'.e{k}{{animation:e{k} {P}s linear infinite;animation-delay:{neg_delay(e0):.3f}s}}')
        body.append(f'<g class="e{k}"><rect x="{ex - 5:.0f}" y="{ey - 5}" width="11" height="11" fill="#5CF08B" opacity=".3"/>'
                    f'<rect x="{ex - 2:.0f}" y="{ey - 2}" width="5" height="5" fill="#B9FFD0"/></g>')
        # 폭발: 맞는 자리에서 조각이 퍼진다
        css.append(
            f'@keyframes x{k}{{0%{{transform:scale(.2);opacity:1}}{pct(0.5)}{{transform:scale(1.7);opacity:0}}100%{{transform:scale(1.7);opacity:0}}}}'
            f'.x{k}{{transform-box:fill-box;transform-origin:center;animation:x{k} {P}s ease-out infinite;animation-delay:{neg_delay(meet):.3f}s}}')
        rnd = random.Random(k)
        bits = ''.join(
            f'<rect x="{mx + dx:.0f}" y="{y + dy:.0f}" width="{sz}" height="{sz}" fill="{c}"/>'
            for dx, dy, sz, c in [(rnd.uniform(-30, 30), rnd.uniform(-30, 30), rnd.choice([4, 4, 6, 8]),
                                   rnd.choice(['#FFE07A', '#FF8A3D', '#E5484D', '#FFFFFF'])) for _ in range(22)])
        body.append(f'<g class="x{k}">{bits}</g>')

    # 별: 세 겹, 멀수록 느리게
    rnd = random.Random(7)
    stars = []
    for layer, (n, dur, col, sz) in enumerate([(70, 24, '#2A3344', 1), (40, 12, '#56637A', 2), (16, 6, '#C9D6EA', 2)]):
        dots = ''.join(f'<rect x="{x}" y="{rnd.randint(4, H - 4)}" width="{sz + (1 if layer == 2 else 0)}" height="{sz}"/>'
                       for x in [rnd.randint(0, W) for _ in range(n)])
        stars.append(f'<g fill="{col}" class="s{layer}"><g>{dots}</g><g transform="translate({W},0)">{dots}</g></g>')
        css.append(f'.s{layer}{{animation:sx {dur}s linear infinite}}')
    css.append(f'@keyframes sx{{to{{transform:translateX(-{W}px)}}}}')

    # 엔진 불꽃 깜빡임
    css.append('.fl{animation:fl .12s steps(1) infinite}@keyframes fl{50%{opacity:.35}}')
    # 점수(다섯 자리, 끝자리부터 굴린다)
    sx, sy = W - 100, 30
    digits = ''.join(
        f'<g clip-path="url(#dg)"><text class="sc" style="animation-duration:{0.6 * 10 ** (4 - i):.1f}s" x="{sx + i * 11}" y="{sy}">'
        + ''.join(f'<tspan x="{sx + i * 11}" dy="{0 if j == 0 else 16}">{j % 10}</tspan>' for j in range(11)) + '</text></g>'
        for i in range(5))
    css.append('.sc{fill:#C9D1D9;animation-name:roll;animation-timing-function:steps(10);animation-iteration-count:infinite}'
               '@keyframes roll{to{transform:translateY(-160px)}}')
    css.append('text{font-family:Consolas,"Courier New",monospace;font-size:14px}')
    css.append('@media (prefers-reduced-motion:reduce){*{animation:none!important}}')

    pw = len(ply[0]) * PX
    player = (f'<g class="ply">{sprite(ply, PLAYER_X, LANES[0])}'
              f'<g class="fl"><rect x="{PLAYER_X - pw / 2 - 12:.0f}" y="{LANES[0] - 2 * PX}" width="12" height="{PX}" fill="#FFB347"/>'
              f'<rect x="{PLAYER_X - pw / 2 - 12:.0f}" y="{LANES[0] + 2 * PX}" width="12" height="{PX}" fill="#FFB347"/></g></g>')

    # 멀리 떠 있는 고리 행성(천천히 왼쪽으로 흐른다)
    pr, pcx, pcy, cells = 11, 690, 150, []
    for yy in range(-pr - 1, pr + 2):
        for xx in range(-pr - 6, pr + 7):
            d = (xx * xx + yy * yy) ** 0.5
            ring = abs((xx * 0.5) ** 2 + (yy * 2.2) ** 2 - (pr * 0.95) ** 2) < 14 and not (d < pr and yy < 0)
            if d <= pr:
                col = '#121926' if xx + yy > 4 else ('#182132' if xx + yy > -6 else '#212C42')
            elif ring:
                col = '#26314A'
            else:
                continue
            cells.append(f'<rect x="{pcx + xx * PX}" y="{pcy + yy * PX}" width="{PX}" height="{PX}" fill="{col}"/>')
    planet = f'<g class="pl">{"".join(cells)}</g>'
    css.append('.pl{animation:pl 60s linear infinite alternate}@keyframes pl{to{transform:translateX(-160px)}}')

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t" shape-rendering="crispEdges">
<title id="t">은하 전투기: 전투기가 오른쪽에서 오는 적기를 레이저로 맞히는 미니 게임</title>
<defs><clipPath id="card"><rect width="{W}" height="{H}" rx="14"/></clipPath><clipPath id="dg"><rect x="0" y="{sy - 14}" width="{W}" height="17"/></clipPath></defs>
<style>{''.join(css)}</style>
<g clip-path="url(#card)">
<rect width="{W}" height="{H}" fill="#070A12"/>
{''.join(stars)}
{planet}
{''.join(body)}
{player}
<text x="24" y="{sy}" fill="#5B6672">GALAXY FIGHTER</text>
<text x="{sx - 12}" y="{sy}" fill="#5B6672" text-anchor="end">HI 0099200</text>
{digits}
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="#1B2230"/>
</svg>
"""
    path = os.path.join(ROOT, 'assets', 'space-fighter.svg')
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(svg)
    print(path, len(svg))


build()
