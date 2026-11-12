"""Map every word of the approved voice_en.txt onto the REAL WAV using ASR word timestamps.

usage: python3 tools/align.py <asr_words.json> <voice_en.txt> <out_dir>
ASR words come from Parakeet TDT (sherpa-onnx, run locally, audio never leaves the machine).
Writes script_words.json (script order, with start/end and how each time was obtained) and
align_report.json (matches, ASR-only words, script-only words). Recognition spelling is corrected
toward the approved script; the script itself is never rewritten.
"""
import json, re, sys, difflib, os

ONES = {'0': 'zero'}
SPELL = {'gray': 'grey', 'neighbour': 'neighbor', 'us': 'us', 'usa': 'usa'}


def norm(w):
    w = w.lower().replace('’', "'")
    w = re.sub(r"[^a-z0-9%$']", '', w).strip("'")
    return SPELL.get(w, w)


def asr_tokens(words):
    """Split ASR words into script-like tokens: '33%' -> 33, percent ; 'U.S.' -> us ; '$1' -> ..."""
    out = []
    for i, w in enumerate(words):
        raw = w['w'].lower()
        raw = raw.replace('u.s.', 'us').replace('u.s', 'us')
        parts = []
        for p in re.split(r'[\s\-]+', raw):
            n = norm(p)
            if not n: continue
            m = re.fullmatch(r'(\d+)%', n)
            if m: parts += [m.group(1), 'percent']; continue
            if n.endswith('%'): parts += [n[:-1], 'percent']; continue
            if n.startswith('$'): parts += [n[1:], 'dollars']; continue
            parts.append(n)
        for k, p in enumerate(parts):
            out.append({'n': p, 'wi': i, 'k': k, 'of': len(parts)})
    return out


def script_tokens(text):
    out = []
    for m in re.finditer(r"\S+", text):
        raw = m.group(0)
        for p in re.split(r'-', raw):
            n = norm(p)
            if n: out.append({'w': raw, 'n': n})
    return out


def main(asr_path, script_path, out_dir):
    A = json.load(open(asr_path)); words = A['words']
    at = asr_tokens(words)
    st = script_tokens(open(script_path).read())
    sm = difflib.SequenceMatcher(a=[x['n'] for x in st], b=[x['n'] for x in at], autojunk=False)
    times = [None] * len(st)
    matched = 0
    for a0, b0, n in sm.get_matching_blocks():
        for k in range(n):
            tk = at[b0 + k]; wd = words[tk['wi']]
            s, e = wd['start'], wd['end']
            if tk['of'] > 1:  # one ASR word spoken as several script words (33% -> 33 percent)
                seg = (e - s) / tk['of']; s, e = s + seg * tk['k'], s + seg * (tk['k'] + 1)
            times[a0 + k] = (s, e, 'asr'); matched += 1
    # script words the recogniser wrote differently: place them between real neighbours (flagged)
    i = 0
    while i < len(st):
        if times[i] is None:
            j = i
            while j < len(st) and times[j] is None: j += 1
            t0 = times[i - 1][1] if i > 0 else 0.0
            t1 = times[j][0] if j < len(st) else A['duration']
            for k in range(i, j):
                f0 = (k - i) / (j - i); f1 = (k - i + 1) / (j - i)
                times[k] = (t0 + (t1 - t0) * f0, t0 + (t1 - t0) * f1, 'between-neighbours')
            i = j
        else:
            i += 1
    res = [{'i': k, 'w': st[k]['w'], 'start': round(times[k][0], 3), 'end': round(times[k][1], 3), 'how': times[k][2]} for k in range(len(st))]
    ops = [op for op in sm.get_opcodes() if op[0] != 'equal']
    diffs = [{'op': o, 'script': ' '.join(x['n'] for x in st[a0:a1]), 'asr': ' '.join(x['n'] for x in at[b0:b1]),
              't': round(words[at[b0]['wi']]['start'], 2) if b0 < len(at) else None} for o, a0, a1, b0, b1 in ops]
    rep = {'script_tokens': len(st), 'asr_tokens': len(at), 'matched': matched,
           'match_rate': round(matched / len(st), 4), 'differences': diffs}
    os.makedirs(out_dir, exist_ok=True)
    json.dump(res, open(os.path.join(out_dir, 'script_words.json'), 'w'), indent=0)
    json.dump(rep, open(os.path.join(out_dir, 'align_report.json'), 'w'), indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in rep.items() if k != 'differences'}), len(diffs), 'difference spans')


if __name__ == '__main__':
    main(*sys.argv[1:4])
