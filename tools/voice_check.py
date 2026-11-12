"""Assemble paragraph WAVs into one timeline and check them with local ASR (Parakeet + Whisper).
python3 tools/voice_check.py  -> audio/voice_en_source.wav, sync/para_times.json, voice_check.json"""
import csv, os, re, json, subprocess, difflib, wave, numpy as np, sherpa_onnx
ONES = 'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()
TENS = 'zero ten twenty thirty forty fifty sixty seventy eighty ninety'.split()
def num2words(n):
    if 1900 < n < 2100 and n != 2000:
        a, b = divmod(n, 100); return num2words(a) + ' ' + (('oh ' + ONES[b]) if 0 < b < 10 else num2words(b) if b else 'hundred')
    if n < 20: return ONES[n]
    if n < 100: return TENS[n // 10] + ('' if n % 10 == 0 else ' ' + ONES[n % 10])
    if n < 1000: return ONES[n // 100] + ' hundred' + ('' if n % 100 == 0 else ' ' + num2words(n % 100))
    return num2words(n // 1000) + ' thousand' + ('' if n % 1000 == 0 else ' ' + num2words(n % 1000))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = os.environ.get('ASR', '/tmp/claude-0/-home-claude/df0984ad-f311-5254-a0a3-609fbc0cd6b9/scratchpad/asr/')
SR, GAP = 24000, 0.45
scenes = [s for s in csv.DictReader(open(os.path.join(ROOT, 'scenes.csv'))) if os.path.exists(os.path.join(ROOT, 'audio/para', s['scene_id'] + '.wav'))]
def load(f):
    return np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-ar', str(SR), '-ac', '1', '-f', 's16le', '-'], capture_output=True).stdout, dtype=np.int16)
def trim(a, thr=0.004, pad=0.08):
    x = np.abs(a.astype(np.float32) / 32768); idx = np.where(x > thr)[0]
    if not len(idx): return a
    p = int(pad * SR); return a[max(0, idx[0] - p): min(len(a), idx[-1] + p)]
parts, times, t = [], [], 0.0
for i, s in enumerate(scenes):
    a = trim(load(os.path.join(ROOT, 'audio/para', s['scene_id'] + '.wav')))
    gap = (0.25 if i == 0 else GAP) + float(s['flight_pause_s'] or 0)
    parts.append(np.zeros(int(gap * SR), np.int16)); t += gap
    times.append(dict(scene_id=s['scene_id'], start=round(t, 3), end=round(t + len(a) / SR, 3), flight_pause_before=float(s['flight_pause_s'] or 0)))
    parts.append(a); t += len(a) / SR
parts.append(np.zeros(int(0.8 * SR), np.int16))
full = np.concatenate(parts)
os.makedirs(os.path.join(ROOT, 'sync'), exist_ok=True)
with wave.open(os.path.join(ROOT, 'audio/voice_en_source.wav'), 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(full.tobytes())
json.dump(times, open(os.path.join(ROOT, 'sync/para_times.json'), 'w'), indent=1)
# ASR per paragraph
pk = M + 'sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8/'; wh = M + 'sherpa-onnx-whisper-small.en/'
P = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=pk + 'encoder.int8.onnx', decoder=pk + 'decoder.int8.onnx', joiner=pk + 'joiner.int8.onnx', tokens=pk + 'tokens.txt', model_type='nemo_transducer', num_threads=4)
W = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=wh + 'small.en-encoder.int8.onnx', decoder=wh + 'small.en-decoder.int8.onnx', tokens=wh + 'small.en-tokens.txt', num_threads=4)
def rec(R, a16):
    s = R.create_stream(); s.accept_waveform(16000, a16); R.decode_stream(s); return s.result.text
def norm(x):
    x = x.replace('%', ' percent').replace('-', ' ').replace("'", '')
    x = re.sub(r'\d+', lambda m: ' ' + num2words(int(m.group())) + ' ', x)
    x = x.lower().replace('-', ' ').replace(',', ' ').replace(' and ', ' ').replace('per cent', 'percent').replace('neighbour', 'neighbor')
    return re.findall(r"[a-z]+", x)
rep, total_bad = [], 0
for s, tm in zip(scenes, times):
    a = full[int(tm['start'] * SR): int(tm['end'] * SR)].astype(np.float32) / 32768
    a16 = np.interp(np.arange(0, len(a), SR / 16000), np.arange(len(a)), a).astype(np.float32)
    want = norm(s['voice_en_exact']); hp = rec(P, a16); hw = rec(W, a16) if len(a16) < 16000 * 29 else ''
    got = norm(hp); sm = difflib.SequenceMatcher(None, want, got)
    diffs = [(' '.join(want[i1:i2]), ' '.join(got[j1:j2])) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != 'equal']
    # a diff counts only if Whisper also disagrees with the script (independent check)
    gw = ' '.join(norm(hw)) if hw else ''
    real = [d for d in diffs if not hw or d[0] not in gw]
    total_bad += len(real)
    rep.append(dict(scene_id=s['scene_id'], start=tm['start'], end=tm['end'], parakeet=hp, whisper=hw, match=round(sm.ratio(), 3), diffs=diffs, diffs_confirmed_by_whisper=real))
json.dump(dict(duration_s=round(len(full) / SR, 2), sample_rate=SR, paragraphs=rep), open(os.path.join(ROOT, 'voice_check.json'), 'w'), indent=1)
print(json.dumps(dict(duration=round(len(full) / SR, 1), min_match=min(r['match'] for r in rep), confirmed_diffs=total_bad)))
for r in rep:
    if r['diffs_confirmed_by_whisper']: print(r['scene_id'], r['match'], r['diffs_confirmed_by_whisper'][:6])
