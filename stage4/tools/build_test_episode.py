"""Stage 4: data/episode.js for the 10 s SILENT visual test (Canada -> USA -> Mexico) + technical checks.

Everything shown comes from ../countries.csv (stage 2 registry). Times here are hand-set for the test only;
stage 5 replaces this file with tools/build_episode.py driven by the real WAV word timestamps.
Technical checks are picked automatically from the data + data/world.js geometry (no hand-picked countries).
Run: python3 tools/build_test_episode.py   (env MIG_ROOT = project root, default /mnt/project-files/migration-desire-map)
"""
import csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.dirname(HERE)
ROOT = os.environ.get('MIG_ROOT', '/mnt/project-files/migration-desire-map')
sys.path.insert(0, HERE)
from build_episode import ISO as ISO_OLD  # alpha3 -> (numeric, flag) for the old 156 countries

ISO = dict(ISO_OLD); ISO.update({'USA': ('840', 'us'), 'GMB': ('270', 'gm'), 'SWZ': ('748', 'sz')})

# 6 statuses (project_brief.txt). Diverging scale: green = people want in, red = people want out, purple = cannot leave.
STATUSES = {
    'MAGNET': {'label': 'MAGNET',        'color': '#1FA64F', 'dark': '#0d6a2e', 'icon': 'magnet',   'rule': 'PNMI +50% or more / 3%+ dream share'},
    'PULL':   {'label': 'MORE WANT IN',  'color': '#86C94A', 'dark': '#4c8a1f', 'icon': 'arrowIn',  'rule': 'PNMI +10 to +49% / UN +2 per 1,000 or more'},
    'STAY':   {'label': 'MOST STAY',     'color': '#8FA2B4', 'dark': '#566778', 'icon': 'house',    'rule': 'under 20% want out / PNMI or UN near zero'},
    'LEAVE':  {'label': 'MANY WANT OUT', 'color': '#F39A1E', 'dark': '#a85f00', 'icon': 'arrowOut', 'rule': '20-39% want out / PNMI -10% / UN -2 or less'},
    'EXIT':   {'label': 'MOST WANT OUT', 'color': '#E0283B', 'dark': '#9c1424', 'icon': 'plane',    'rule': '40% or more want to leave'},
    'LOCKED': {'label': "CAN'T LEAVE",   'color': '#6A4BC4', 'dark': '#3e2a85', 'icon': 'lock',     'rule': 'exit ban: leaving is a crime'},
}
# default face per status = a game illustration of the band, not a claim about how people feel
FACE = {'MAGNET': 'happy', 'PULL': 'calm', 'STAY': 'chill', 'LEAVE': 'nervous', 'EXIT': 'shocked', 'LOCKED': 'disappointed'}


def tags(r):
    """(card tag, short tag for the recent list) from the registry row: the number + its year, never a repeat of the status"""
    q = r['quality']
    if r['status'] == 'LOCKED': return 'EXIT BAN', 'EXIT BAN'
    if r['pnmi']:
        v = int(r['pnmi']); return '%+d%% NET (2023-25)' % v, '%+d%%' % v
    if r['leave_pct']:
        per = r['leave_period'] if re.fullmatch(r'\d{4}(-\d{2,4})?', r['leave_period']) else re.findall(r'\d{4}', r['leave_period'])[-1]
        return '%s%% (%s)' % (r['leave_pct'], per), '%s%% OUT' % r['leave_pct']
    if q == 'E':
        v = float(r['un_netmig_per1000_avg19_23']); return 'UN %+.1f PER 1,000' % v, '%+.1f/1k' % v
    return r['basis'][:24].upper(), ''


def stop_of(r, **kw):
    num, flag = ISO[r['code']]
    tag, rtag = tags(r)
    d = {'code': r['code'], 'id': num, 'flag': flag, 'name': r['name'], 'status': r['status'], 'quality': r['quality'],
         'tag': tag, 'rtag': rtag, 'reaction': FACE[r['status']], 'events': []}
    if r['short_name'] and r['short_name'] != r['name']: d['short'] = r['short_name']
    d.update(kw); return d


def world():
    W = json.loads(open(os.path.join(PROJ, 'data', 'world.js')).read().split('=', 1)[1].rstrip().rstrip(';'))
    return {c['id']: c for c in W['countries'] if c.get('id')}


def near_box(c):  # same grouping as index.html init(): polygons near the main one share the camera box
    m = c['polys'][c['main']]['b']; mw, mh = m[2] - m[0], m[3] - m[1]
    ex = [m[0] - mw * .25, m[1] - mh * .25, m[2] + mw * .25, m[3] + mh * .25]; core = list(m)
    for i, p in enumerate(c['polys']):
        b = p['b']; cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        if i == c['main'] or (ex[0] < cx < ex[2] and ex[1] < cy < ex[3]):
            core = [min(core[0], b[0]), min(core[1], b[1]), max(core[2], b[2]), max(core[3], b[3])]
    return core


def face_r(c):  # face radius at the country's own camera (countryCam: 50% width, 590 px height, zmax 9)
    b = near_box(c); z = min(960 / (b[2] - b[0]), 590 / (b[3] - b[1]), 9)
    return min(c['label'][2] * z * 0.95, 80)


def main():
    reg = [r for r in csv.DictReader(open(os.path.join(ROOT, 'countries.csv')))]
    by = {r['code']: r for r in reg}
    W = world()
    missing = [r['code'] for r in reg if r['code'] not in ISO or ISO[r['code']][0] not in W]
    flags_missing = [r['code'] for r in reg if r['code'] in ISO and not os.path.exists(os.path.join(PROJ, 'assets', 'flags', ISO[r['code']][1] + '.svg'))]
    assert not missing, ('no geometry/ISO', missing)
    assert not flags_missing, ('no flag', flags_missing)

    # ---- the 10 s test: first three countries of the route (scenes.csv order) ----
    can = stop_of(by['CAN'], activate=3.75, events=[{'kind': 'num', 't': 4.25, 'head': 'GALLUP 2023-25', 'big': '+225%', 'arrow': 'in', 'sub': 'WANT IN vs WANT OUT', 'dx': 160}])
    usa = stop_of(by['USA'], activate=6.25, tag='#1 DREAM · 15% PICK IT', rtag='#1 DREAM',
                  events=[{'kind': 'num', 't': 6.7, 'head': "WORLD'S #1 DREAM", 'big': '15%', 'sub': 'OF WOULD-BE MIGRANTS PICK IT'}])
    mex = stop_of(by['MEX'], activate=8.45, events=[{'kind': 'num', 't': 8.85, 'head': 'GALLUP 2023', 'big': '20%', 'arrow': 'out', 'sub': 'WANT TO LEAVE', 'side': 1}])
    shots = [{'ids': ['124'], 'codes': ['CAN'], 'region': 'TEST', 'flyStart': 2.6, 'arrive': 4.2},
             {'ids': ['840'], 'codes': ['USA'], 'region': 'TEST', 'flyStart': 5.55, 'arrive': 6.55},
             {'ids': ['484'], 'codes': ['MEX'], 'region': 'TEST', 'flyStart': 7.75, 'arrive': 8.75}]

    # ---- technical checks, picked from the data ----
    route = [r for r in reg]
    fr = {r['code']: face_r(W[ISO[r['code']][0]]) for r in route}
    longest = max(route, key=lambda r: len(r['name']))
    with_face = [r for r in route if fr[r['code']] >= 22]
    smallest_face = min(with_face, key=lambda r: fr[r['code']])
    micro = sorted([r for r in route if fr[r['code']] < 22], key=lambda r: fr[r['code']])
    holes = [r for r in route if any(len(p['r']) > 1 for p in W[ISO[r['code']][0]]['polys'])]
    enclave = next((r for r in holes if r['code'] == 'ZAF'), holes[0] if holes else None)
    flag_kb = lambda r: os.path.getsize(os.path.join(PROJ, 'assets', 'flags', ISO[r['code']][1] + '.svg'))
    complexflag = max(route, key=flag_kb)
    bw = lambda r: (lambda b: (b[2] - b[0], b[3] - b[1]))(near_box(W[ISO[r['code']][0]]))
    widest = max(route, key=lambda r: bw(r)[0])
    tallest = max(route, key=lambda r: bw(r)[1] / bw(r)[0])
    est = next(r for r in route if r['quality'] == 'E')
    srv = next(r for r in route if r['quality'] == 'S')
    T = lambda kind, r, **kw: {**stop_of(r), 'kind': kind, **kw}
    tech = [
        T('longname', longest, note='LONGEST NAME: card + list'),
        T('smallface', smallest_face, note='SMALLEST COUNTRY WITH A FACE ON THE MAP (R %.0f px)' % fr[smallest_face['code']]),
        T('micro1', micro[0], micro=True, note='TOO SMALL FOR A FACE: CALLOUT (R %.1f px)' % fr[micro[0]['code']]),
        T('micro2', micro[1], micro=True, note='TOO SMALL FOR A FACE: CALLOUT (R %.1f px)' % fr[micro[1]['code']]),
        T('enclave', enclave, note='ENCLAVE INSIDE (hole in the polygon)'),
        T('complexflag', complexflag, note='MOST COMPLEX FLAG (%d KB SVG)' % (flag_kb(complexflag) // 1024)),
        T('wide_strict', widest, flagFit='strict', note='WIDEST: FLAG IN STRICT PROPORTIONS'),
        T('wide_stretch', widest, flagFit='stretch', note='WIDEST: FLAG STRETCHED TO THE WIDTH'),
        T('tall', tallest, note='MOST ELONGATED: WHOLE COUNTRY IN FRAME (face R %.0f px)' % fr[tallest['code']]),
        T('tall_span', tallest, span=[150, 95], note='MOST ELONGATED: CAMERA ON PART OF IT (span rule)'),
        T('estimate', est, tint=1, note='UN ESTIMATE: HATCHED', events=[{'kind': 'num', 'head': 'UN ESTIMATE 2019-23', 'big': '%+.1f' % float(est['un_netmig_per1000_avg19_23']), 'sub': 'NET MIGRANTS PER 1,000', 'est': True}]),
        T('survey', srv, tint=1, note='OTHER SURVEY: DOTTED OUTLINE', events=[{'kind': 'num', 'head': 'INDEPENDENT POLL 2023', 'big': srv['leave_pct'] + '%', 'arrow': 'out', 'sub': 'WANT TO LEAVE'}]),
    ]
    ep = {
        'title': 'Countries People Want to LEAVE vs MOVE TO', 'size': [1920, 1080], 'fps': 30, 'seed': 20261104,
        'totalCountries': 3, 'testScope': 3, 'duration': 10.0, 'colorAfter': True, 'emblem': 'assets/theme_suitcase.png',
        'audio': None, 'subject': None, 'statuses': STATUSES, 'shots': shots, 'stops': [can, usa, mex], 'regions': [],
        'techChecks': tech,
    }
    js = ('// GENERATED by tools/build_test_episode.py (stage 4 visual test, silent, hand-set times). Stage 5 replaces it.\n'
          'window.EPISODE = ' + json.dumps(ep, ensure_ascii=False, indent=1) + ';\n')
    open(os.path.join(PROJ, 'data', 'episode.js'), 'w').write(js)
    print('tech:', [(x['kind'], x['code']) for x in tech])
    print('micro list:', [(r['code'], round(fr[r['code']], 1)) for r in micro])


if __name__ == '__main__':
    main()
