"""강아지 달리기 SVG 만들기 (크롬 오프라인 게임 모양, README 는 스크립트를 못 돌리니 자동 재생)

python tools/make_dog_svg.py  →  assets/dog-run-light.svg · assets/dog-run-dark.svg
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PX = 3            # 한 칸 = 3px
W, H = 960, 220
GROUND = 186      # 땅 선 y
DOG_X = 70
P = 6.0           # 한 바퀴(초)
TRAVEL = 2.6      # 장애물이 화면 오른쪽 끝에서 왼쪽 끝까지 가는 시간
JUMP = 0.72       # 점프 시간
JUMP_H = 78       # 점프 높이(px)

# 강아지(오른쪽을 봄). X = 몸, o = 눈(빈칸)
DOG = [
    "..................XX....",
    ".................XXX....",
    "................XXXXXXX.",
    "................XXoXXXXX",
    "................XXXXXXXX",
    ".X..............XXXXXXX.",
    ".XX.............XXXXX...",
    "..XX...........XXXXX....",
    "...XXXXXXXXXXXXXXXXXX...",
    "...XXXXXXXXXXXXXXXXXX...",
    "...XXXXXXXXXXXXXXXXXX...",
    "....XXXXXXXXXXXXXXXX....",
]
# 다리 두 동작(몸 아래 4줄)
LEGS_A = [
    "....XX..XX.....XX..XX...",
    "....XX...XX....XX...XX..",
    "...XX.....XX..XX.....X..",
    "...XX.....XX..XX........",
]
LEGS_B = [
    ".....XX.XX......XX.XX...",
    "......XXX.......XXXX....",
    "......XX........XX......",
    ".....XX........XX.......",
]
# 소화전
HYDRANT = [
    "...XXXX...",
    "..XXXXXX..",
    ".XXXXXXXX.",
    "..XXXXXX..",
    "XXXXXXXXXX",
    "XXXXXXXXXX",
    "..XXXXXX..",
    "..XXXXXX..",
    "..XXXXXX..",
    "..XXXXXX..",
    ".XXXXXXXX.",
    "XXXXXXXXXX",
]
# 뼈다귀 더미(낮은 장애물)
BONES = [
    "XX......XX......",
    "XXXXXXXXXX..XX..",
    "XX......XXXXXXXX",
    "..XX....XX..XX..",
    ".XXXXXXXXXXXXX..",
    "..XX........XX..",
]


def rects(grid, ox=0, oy=0, ch='X'):
    """같은 줄에서 이어진 칸을 한 사각형으로 묶는다(파일 크기를 줄인다)"""
    out = []
    for y, row in enumerate(grid):
        x = 0
        while x < len(row):
            if row[x] == ch:
                s = x
                while x < len(row) and row[x] == ch:
                    x += 1
                out.append(f'<rect x="{ox + s * PX}" y="{oy + y * PX}" width="{(x - s) * PX}" height="{PX}"/>')
            else:
                x += 1
    return ''.join(out)


def pct(t):
    return f'{(t % P) / P * 100:.3f}%'


def obstacle(name, grid, delay):
    """오른쪽 끝(x=W)에서 왼쪽 끝 밖(-60)까지 TRAVEL 초 동안 가고, 나머지는 화면 밖에서 기다린다"""
    w = len(grid[0]) * PX
    h = len(grid) * PX
    dist = W + 60 + w
    end = TRAVEL / P * 100
    kf = (f'@keyframes {name}{{0%{{transform:translateX(0)}}{end:.3f}%{{transform:translateX(-{dist}px)}}'
          f'{end + 0.01:.3f}%,100%{{transform:translateX(-{dist}px)}}}}')
    # 강아지 앞발 끝(x = DOG_X + 강아지 폭)과 장애물 가운데가 만나는 시각
    meet_x = W - (DOG_X + len(DOG[0]) * PX * 0.55) + w / 2
    meet = delay + meet_x / dist * TRAVEL
    body = f'<g class="{name}" style="animation-delay:{delay}s"><g transform="translate({W},{GROUND - h + 2})">{rects(grid)}</g></g>'
    return kf, body, meet


def jump_keyframes(meets):
    """장애물을 만나는 시각을 가운데로 둔 포물선 점프. 점 9개로 곡선을 흉내 낸다"""
    pts = {0.0: 0.0}
    for m in meets:
        for i in range(9):
            f = i / 8
            t = (m - JUMP / 2 + f * JUMP) % P
            pts[round(t, 3)] = -JUMP_H * 4 * f * (1 - f)
        # 점프 앞뒤로 땅에 붙어 있게
        pts[round((m - JUMP / 2 - 0.01) % P, 3)] = 0.0
        pts[round((m + JUMP / 2 + 0.01) % P, 3)] = 0.0
    pts[P - 0.001] = pts.get(0.0, 0.0)
    frames = ''.join(f'{t / P * 100:.3f}%{{transform:translateY({y:.1f}px)}}' for t, y in sorted(pts.items()))
    return '@keyframes jump{' + frames + '}'


def digit_strip(x, y, cls, dur):
    """한 자리 숫자. 0~9 를 세로로 세워 두고 한 칸씩 끊어 올린다"""
    nums = ''.join(f'<tspan x="{x}" dy="{0 if i == 0 else 16}">{i}</tspan>' for i in list(range(10)) + [0])
    return f'<g clip-path="url(#dg)" transform="translate(0,0)"><text class="sc {cls}" style="animation-duration:{dur}s" x="{x}" y="{y}">{nums}</text></g>'


def build(theme):
    ink, bg = ('#535353', '#FFFFFF') if theme == 'light' else ('#C9D1D9', '#0D1117')
    faint = '#B5B5B5' if theme == 'light' else '#3D444D'
    kfs, bodies, meets = [], [], []
    for name, grid, d in (('o1', HYDRANT, 0.0), ('o2', BONES, 2.1), ('o3', HYDRANT, 4.05)):
        kf, body, meet = obstacle(name, grid, d)
        kfs.append(kf); bodies.append(body); meets.append(meet)
    jump = jump_keyframes(meets)

    dog_h = (len(DOG) + len(LEGS_A)) * PX
    dog_y = GROUND - dog_h + 2
    legs_y = dog_y + len(DOG) * PX

    # 점수: 다섯 자리. 끝자리는 0.08초마다 1 씩
    sx, sy = W - 92, 34
    digits = ''.join(digit_strip(sx + i * 10, sy, f'd{i}', 0.8 * 10 ** (4 - i)) for i in range(5))

    css = f"""
    .ink {{ fill: {ink}; }}
    .faint {{ fill: {faint}; }}
    .eye {{ fill: {bg}; }}
    text {{ font-family: 'Press Start 2P', Consolas, 'Courier New', monospace; font-size: 13px; fill: {ink}; }}
    .sc {{ animation-name: roll; animation-timing-function: steps(10); animation-iteration-count: infinite; }}
    @keyframes roll {{ from {{ transform: translateY(0); }} to {{ transform: translateY(-160px); }} }}
    .dog {{ animation: jump {P}s linear infinite; }}
    .la {{ animation: legA .24s steps(1) infinite; }}
    .lb {{ animation: legB .24s steps(1) infinite; }}
    @keyframes legA {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0; }} }}
    @keyframes legB {{ 0% {{ opacity: 0; }} 50% {{ opacity: 1; }} }}
    .o1, .o2, .o3 {{ animation-duration: {P}s; animation-timing-function: linear; animation-iteration-count: infinite; }}
    .o1 {{ animation-name: o1; }} .o2 {{ animation-name: o2; }} .o3 {{ animation-name: o3; }}
    {''.join(kfs)}
    {jump}
    .ground {{ animation: ground 1.2s linear infinite; }}
    @keyframes ground {{ to {{ transform: translateX(-200px); }} }}
    .cloud {{ animation: cloud 26s linear infinite; }}
    .cloud2 {{ animation-duration: 38s; animation-delay: -14s; }}
    @keyframes cloud {{ from {{ transform: translateX(0); }} to {{ transform: translateX(-1100px); }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} .o2, .o3 {{ display: none; }} }}
    """

    pebbles = ''.join(f'<rect x="{x}" y="{GROUND + 8 + (x * 7) % 9}" width="{3 if x % 3 else 6}" height="2"/>'
                      for x in range(0, W + 240, 37))
    cloud = ('<path d="M0 12 h8 v-4 h6 v-4 h14 v4 h6 v4 h10 v4 z" fill="none" stroke-width="2"/>')
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t" shape-rendering="crispEdges">
<title id="t">강아지가 소화전과 뼈다귀를 뛰어넘으며 달리는 미니 게임</title>
<defs><clipPath id="dg"><rect x="0" y="{sy - 13}" width="{W}" height="16"/></clipPath></defs>
<style>{css}</style>
<g class="faint"><text x="{sx - 96}" y="{sy}" style="fill:{faint}">HI 01024</text></g>
{digits}
<g stroke="{faint}"><g class="cloud" transform="translate({W + 40},48)">{cloud}</g><g class="cloud cloud2" transform="translate({W + 300},78)">{cloud}</g></g>
<rect class="ink" x="0" y="{GROUND}" width="{W}" height="2"/>
<g class="faint"><g class="ground">{pebbles}</g></g>
<g class="ink">{''.join(bodies)}</g>
<g class="dog">
  <g class="ink">{rects(DOG, DOG_X, dog_y)}</g>
  <g class="eye">{rects(DOG, DOG_X, dog_y, 'o')}</g>
  <g class="ink la">{rects(LEGS_A, DOG_X, legs_y)}</g>
  <g class="ink lb">{rects(LEGS_B, DOG_X, legs_y)}</g>
</g>
</svg>
"""
    path = os.path.join(ROOT, 'assets', f'dog-run-{theme}.svg')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(path, len(svg), 'meets', [round(m, 2) for m in meets])


for th in ('light', 'dark'):
    build(th)
