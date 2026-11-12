"""Build data/episode.js for "Countries People Want to LEAVE vs MOVE TO" from the registry, the region plans
(tools/plans.py) and the REAL word timestamps of the voice (sync/script_words.json from tools/align.py).

usage: python3 tools/build_mig.py      env MIG_ROOT = project root with countries.csv (default /mnt/project-files/migration-desire-map)
Outputs data/episode.js, sync/sync_table.csv, sync/region_Rxx.json.
Rules: every map time comes from a word time. Base reveal fires as the camera reaches the country, never later than
its spoken name. A number chip pops on its spoken number; countries whose number is not spoken still show the chip
(scenes.csv silent_chip rule) right after the reveal. One chip at a time inside a shot.
"""
import csv, json, os, re, sys, wave

HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.dirname(HERE)
ROOT = os.environ.get('MIG_ROOT', '/mnt/project-files/migration-desire-map')
FPS = 30
sys.path.insert(0, HERE)
from build_test_episode import ISO, STATUSES, FACE, tags   # one source for statuses/tags (accepted at stage 4)
from plans import PLANS, OUTRO_PLAN

SRC_HEAD = {'S01': 'GALLUP', 'S02': 'GALLUP', 'S03': 'GALLUP', 'S04': 'ARAB BAROMETER', 'S05': 'ARAB BAROMETER', 'S07': 'LEVADA',
            'S08': 'RAZUMKOV / DIF', 'S09': 'METROPOLL', 'S10': 'SWS POLL', 'S11': 'KEYOU POLL', 'S12': 'CAUCASUS BAROMETER',
            'S13': 'BALKAN BAROMETER', 'S14': 'GALLUP', 'S15': 'GALLUP INTL', 'S16': 'GALLUP', 'S18': 'GALLUP', 'S24': 'INDEPENDENT POLL'}

norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())


def short_period(p):
    if re.fullmatch(r'\d{4}-\d{4}', p): return p[:4] + '-' + p[7:]
    if re.fullmatch(r'\d{4}(-\d{2})?', p): return p
    return re.findall(r'\d{4}', p)[-1]


def auto_chip(r):
    """default number chip for a country, straight from the registry row"""
    if r['status'] == 'LOCKED':
        return {'kind': 'num', 'head': 'EXIT BAN', 'big': 'LOCKED', 'sub': "PEOPLE CAN'T LEAVE FREELY", 'arrow': True}
    if r['pnmi']:
        v = int(r['pnmi']); return {'kind': 'num', 'head': 'GALLUP ' + ('2015-17' if '2015-2017' in r['basis'] else '2023-25'), 'big': '%+d%%' % v, 'sub': 'WANT IN vs WANT OUT', 'arrow': True}
    if r['leave_pct']:
        return {'kind': 'num', 'head': '%s %s' % (SRC_HEAD.get(r['leave_source'], 'POLL'), short_period(r['leave_period'])),
                'big': r['leave_pct'] + '%', 'sub': 'CONSIDERED EMIGRATING' if r['leave_source'] in ('S04', 'S05') else 'WANT TO LEAVE', 'arrow': True}
    if r['dream_pct']:
        return {'kind': 'num', 'head': 'GALLUP 2025 · TOP DREAM', 'big': r['dream_pct'] + '%', 'sub': 'OF WOULD-BE MIGRANTS PICK IT', 'arrow': True}
    v = float(r['un_netmig_per1000_avg19_23'])
    return {'kind': 'num', 'head': 'UN ESTIMATE 2019-23', 'big': '%+.1f' % v, 'sub': 'NET MIGRANTS PER 1,000 / YEAR', 'est': True, 'arrow': True}


def load_words():
    from audio_edit import src2edit
    W = json.load(open(os.path.join(PROJ, 'sync', 'script_words.json')))
    for w in W:
        w['src_start'], w['src_end'] = w['start'], w['end']
        w['start'], w['end'] = round(src2edit(w['start']), 3), round(src2edit(w['end']), 3)
    return W


def finder(words):
    toks = [norm(x['w']) for x in words]; cursor = [0]

    def find(phrase, from_cursor=True):
        q = [norm(x) for x in re.split(r'[\s\-]+', phrase) if norm(x)]
        for i in range(cursor[0] if from_cursor else 0, len(toks) - len(q) + 1):
            if toks[i:i + len(q)] == q: return i
        raise KeyError(phrase)
    return find, cursor


def main():
    words = load_words(); find, cursor = finder(words)
    reg = {r['code']: r for r in csv.DictReader(open(os.path.join(ROOT, 'countries.csv')))}
    rows = []
    i_s1_end = find('leave yours?') + 2
    i_s2_end = find('the planet, Canada.') + 3
    intro = {'s1': [words[0]['start'], words[i_s1_end - 1]['end']], 's2': [words[i_s1_end]['start'], words[i_s2_end - 1]['end']]}
    rows.append(['R01', 'SC01', '', 'If .. yours?', intro['s1'][0], intro['s1'][1], 'title + suitcase emblem', 0.0])
    rows.append(['R01', 'SC01', 'CAN', "Let's .. Canada.", intro['s2'][0], intro['s2'][1], 'fly-in, arrive Canada', None])
    stops, shots, regions, outro = [], [], [], None
    n0 = 0
    for plan in PLANS:
        rid, t_reg0 = plan['id'], n0 / FPS
        r_stops, r_shots = [], []
        cursor[0] = next(i for i, w in enumerate(words) if w['start'] >= t_reg0 - 0.01)
        for st in plan['stops']:
            i = find(st['at']); cursor[0] = i
            num, flag = ISO[st['code']]; r = reg[st['code']]
            tag, rtag = tags(r)
            stop = {'code': st['code'], 'id': num, 'flag': flag, 'name': r['name'], 'status': r['status'], 'quality': r['quality'],
                    'tag': st.get('tag', tag), 'rtag': st.get('rtag', rtag), 'reaction': st.get('reaction', FACE[r['status']]),
                    'scene': st['scene'], 'region': rid, 'wordT': round(words[i]['start'], 3), 'events': []}
            if r['short_name'] and r['short_name'] != r['name']: stop['short'] = r['short_name']
            for k in ('flagFit', 'forceMode', 'hold', 'calloutAt'):
                if k in st: stop[k] = st[k]
            evs = [] if st.get('nochip') else [dict(auto_chip(r), **st.get('chip', {}))]
            if evs and 'num_at' in st: evs[0]['at'] = st['num_at']
            evs += [dict(e) for e in st.get('events', [])]
            for ev in evs:
                e = {k: v for k, v in ev.items() if k not in ('at', 'steps', 'end_at')}
                if 'at' in ev:
                    j = find(ev['at']); e['t'] = round(words[j]['start'], 3)
                    rows.append([rid, st['scene'], st['code'], ev['at'], words[j]['start'], words[j]['end'], ev['kind'] + ' ' + str(ev.get('big', ev.get('text', ''))), e['t']])
                else:
                    e['silent'] = True
                if 'end_at' in ev: e['end'] = round(words[find(ev['end_at'], from_cursor=False)]['start'] - 0.1, 3)
                if 'steps' in ev:
                    e['steps'] = []
                    for sp in ev['steps']:
                        j = find(sp['at']); d = {k: v for k, v in sp.items() if k != 'at'}; d['t'] = round(words[j]['start'], 3); e['steps'].append(d)
                        rows.append([rid, st['scene'], st['code'], sp['at'], words[j]['start'], words[j]['end'], 'timeline ' + sp['year'], d['t']])
                    e['t'] = e['steps'][0]['t']
                stop['events'].append(e)
            r_stops.append(stop)
        # shots: arrive just as the line about them starts; take off when the previous line has ended
        cursor[0] = next(i for i, w in enumerate(words) if w['start'] >= t_reg0 - 0.01)
        for sh in plan['shots']:
            j = find(sh['arrive_at']); cursor[0] = j; line_t = words[j]['start']
            if sh.get('first'):
                arrive = line_t - 0.05; fly = max(intro['s2'][0] + 0.35, arrive - 3.2)   # title stays up while sentence 2 starts
            else:
                fly = max(words[j - 1]['end'] - 0.02, line_t - 1.6, t_reg0)
                if 'fly_at' in sh: fly = max(words[find(sh['fly_at'], from_cursor=False)]['start'], t_reg0)
                if 'fly_after' in sh: q = sh['fly_after'].split(); fly = words[find(sh['fly_after'], from_cursor=False) + len(q) - 1]['end'] + 0.05
                if sh.get('fly_region_start'): fly = t_reg0 + 0.05
                arrive = max(line_t + 0.05, fly + sh.get('minfly', 0.9))
            r_shots.append({'ids': [ISO[c][0] for c in sh['ids']], 'codes': sh['ids'], 'region': rid, 'flyStart': round(fly, 3), 'arrive': round(arrive, 3),
                            **{k: sh[k] for k in ('zmax', 'span', 'wFrac', 'pad', 'dip', 'box') if k in sh}})
        # base activation
        for stop in r_stops:
            sh = next(s for s in r_shots if stop['id'] in s['ids'])
            if stop['id'] == sh['ids'][0]: stop['activate'] = round(min(stop['wordT'], max(sh['flyStart'] + 0.3, sh['arrive'] - 0.3)), 3)
            else: stop['activate'] = round(stop['wordT'] - 0.08, 3)
            rows.append([rid, stop['scene'], stop['code'], stop['name'], stop['wordT'], None, 'fill+glow+face+status', stop['activate']])
        # silent chips right after the reveal; one chip at a time inside a shot
        for k, stop in enumerate(r_stops):
            sh = next(s for s in r_shots if stop['id'] in s['ids'])
            for e in stop['events']:
                if e.pop('silent', False): e['t'] = round(stop['activate'] + 0.45, 3); rows.append([rid, stop['scene'], stop['code'], '(silent chip)', None, None, 'num ' + e.get('big', ''), e['t']])
            nx = r_stops[k + 1] if k + 1 < len(r_stops) else None
            if nx and stop['id'] in sh['ids'] and nx['id'] in sh['ids']:
                for e in stop['events']:
                    if e['kind'] == 'num' and 'end' not in e: e['end'] = round(max(e['t'] + 1.0, nx['activate'] - 0.05), 3)
            nums = [e for e in stop['events'] if e['kind'] == 'num']
            for a, b in zip(nums, nums[1:]):   # a later chip of the same country replaces the earlier one
                a['end'] = round(min(a.get('end', 1e9), b['t'] - 0.1), 3)
        # inside one shot chips queue up: each stays at least 1.1 s, the next one waits (fast lists of names)
        for sh in r_shots:
            ch = sorted([e for s2 in r_stops if s2['id'] in sh['ids'] for e in s2['events'] if e['kind'] == 'num'], key=lambda e: e['t'])
            for a, b in zip(ch, ch[1:]):
                if b['t'] < a['t'] + 1.1: b['t'] = round(a['t'] + 1.1, 3)
                a['end'] = round(min(a.get('end', 1e9), b['t'] - 0.05), 3) if a.get('end', 1e9) > b['t'] - 0.05 else a['end']
            nxs = r_shots[r_shots.index(sh) + 1] if r_shots.index(sh) + 1 < len(r_shots) else None
            if ch and nxs and ch[-1]['t'] > nxs['flyStart'] - 0.4: print('  WARN chip after shot end', sh['codes'], ch[-1].get('big'))
        # dwell rule (stage 5 QA): the last chip of a shot stays at least DWELL s before the camera leaves.
        # The narration lists countries ~1 s apart, so the camera may arrive up to ~0.6 s after the next name is spoken.
        DWELL, FLYMIN = 1.25, 0.75
        for i in range(len(r_shots)):
            pv = r_shots[i - 1] if i else (shots[-1] if shots else None); sh = r_shots[i]
            if pv is None or not sh['ids'] or sh.get('first'): continue
            pool = r_stops if i else stops   # first shot of a region: the previous region's last shot (chips may run past the boundary)
            ch = sorted([e for s2 in pool if s2['id'] in pv['ids'] and (i or s2.get('region') != rid) for e in s2['events'] if e['kind'] == 'num'], key=lambda e: e['t'])
            if not ch or sh['flyStart'] >= ch[-1]['t'] + DWELL: continue
            fly = round(ch[-1]['t'] + DWELL, 3); sh['flyStart'] = fly; sh['arrive'] = round(max(sh['arrive'], fly + FLYMIN), 3)
            for e in ch:
                if e.get('end', 0) > fly - 0.05 or 'end' not in e: e['end'] = round(fly + 0.2, 3)
            first = next(s2 for s2 in r_stops if s2['id'] == sh['ids'][0])
            first['activate'] = round(min(max(first['wordT'], fly + 0.3), max(fly + 0.3, sh['arrive'] - 0.3)), 3)
            ch2 = sorted([e for s2 in r_stops if s2['id'] in sh['ids'] for e in s2['events'] if e['kind'] == 'num'], key=lambda e: e['t'])
            prev_t = None
            for s2 in r_stops:
                if s2['id'] in sh['ids'] and s2 is not first and s2['activate'] < first['activate'] + 0.6: s2['activate'] = round(first['activate'] + 0.6, 3)
            for e in ch2:
                if e['t'] < sh['arrive'] - 0.1: e['t'] = round(sh['arrive'] - 0.1, 3)
                if prev_t is not None and e['t'] < prev_t['t'] + 1.1: e['t'] = round(prev_t['t'] + 1.1, 3)
                if prev_t is not None:
                    pe = prev_t.get('end', 1e9)
                    prev_t['end'] = round(e['t'] - 0.05 if pe < prev_t['t'] + 0.9 else min(pe, e['t'] - 0.05), 3)   # a stale end from before the shift is reset
                prev_t = e
        if 'outro' in plan:
            O = plan['outro']; at = lambda ph: round(words[find(ph)]['start'], 3)
            cursor[0] = find(O['start']); outro = {'t0': at(O['start'])}
            outro['rows'] = [{'status': k, 't': at(ph)} for k, ph in O['rows']]
            for k in ('pattern', 'question'): outro[k] = at(O[k])
            r_shots.append({'ids': [], 'codes': [], 'region': rid, 'overview': True, 'flyStart': outro['t0'], 'arrive': round(outro['t0'] + 2.2, 3)})
            rows.append([rid, 'SC25', '', O['start'], outro['t0'], None, 'camera pulls out: final map', outro['t0']])
        # region boundary: after the closing sentence and its natural tail, before the next line
        q = plan['end_after'].split(); k = find(plan['end_after']); last = k + len(q) - 1
        cursor[0] = last + 1; end_word = words[last]; nxt = words[last + 1] if last + 1 < len(words) else None
        tail = end_word['src_end'] + 0.35
        if nxt: tail = min(tail, (end_word['src_end'] + nxt['src_start']) / 2)
        else:
            wv = wave.open(os.path.join(PROJ, 'audio', 'voice_en_source.wav')); tail = min(tail + 1.5, wv.getnframes() / wv.getframerate())
        from audio_edit import src2edit_before
        n_end = int(round(src2edit_before(round(tail * FPS) / FPS) * FPS))
        region = {'id': rid, 'name': plan['name'], 'scenes': plan['scenes'], 'n0': n0, 'n1': n_end, 't0': n0 / FPS, 't1': n_end / FPS,
                  'countries': len(r_stops), 'lastWord': end_word, 'nextWord': nxt}
        regions.append(region); stops += r_stops; shots += r_shots
        json.dump({'region': region, 'shots': r_shots}, open(os.path.join(PROJ, 'sync', 'region_%s.json' % rid), 'w'), indent=1)
        print(rid, 'stops', len(r_stops), 'shots', len(r_shots), 'frames [%d, %d)' % (n0, n_end), 'len %.3f s' % ((n_end - n0) / FPS))
        n0 = n_end
    ep = {'title': 'Countries People Want to LEAVE vs MOVE TO', 'size': [1920, 1080], 'fps': FPS, 'seed': 20261104,
          'totalCountries': len(reg), 'duration': n0 / FPS, 'colorAfter': True, 'emblem': 'assets/theme_suitcase.png',
          'audio': {'file': 'audio/voice_en_edited.wav', 'preview': 'audio/voice_en_edited.wav', 'source': 'audio/voice_en_source.wav', 'sampleRate': 24000},
          'intro': intro, 'subject': None, 'statuses': STATUSES, 'shots': shots, 'stops': stops, 'regions': regions,
          'techChecks': [], **({'outro': outro} if outro else {})}
    open(os.path.join(PROJ, 'data', 'episode.js'), 'w').write(
        '// GENERATED by tools/build_mig.py from countries.csv + tools/plans.py + the real WAV word timestamps. Edit the plan there.\n'
        'window.EPISODE = ' + json.dumps(ep, ensure_ascii=False, indent=1) + ';\n')
    with open(os.path.join(PROJ, 'sync', 'sync_table.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['region', 'scene', 'country', 'line_or_keyword', 'audio_start_s', 'audio_end_s', 'map_event', 'map_event_s', 'map_frame'])
        for r in rows:
            w.writerow([r[0], r[1], r[2], r[3], '' if r[4] is None else round(r[4], 3), '' if r[5] is None else round(r[5], 3), r[6],
                        '' if r[7] is None else round(r[7], 3), '' if r[7] is None else int(round(r[7] * FPS))])


if __name__ == '__main__':
    main()
