"""Word timestamps of the real WAV: Parakeet TDT 0.6B v2 (sherpa-onnx, local) run per paragraph (sync/para_times.json).
usage: python3 tools/asr_words.py  -> sync/parakeet_words.json {duration, words:[{w,start,end}]}  (times on the source WAV)
"""
import json, os, wave
import numpy as np, sherpa_onnx
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASR = os.environ.get('ASR', '/tmp/claude-0/-home-claude/df0984ad-f311-5254-a0a3-609fbc0cd6b9/scratchpad/asr')
pk = ASR + '/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8/'
R = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=pk + 'encoder.int8.onnx', decoder=pk + 'decoder.int8.onnx', joiner=pk + 'joiner.int8.onnx',
                                                  tokens=pk + 'tokens.txt', model_type='nemo_transducer', num_threads=4)
w = wave.open(os.path.join(PROJ, 'audio', 'voice_en_source.wav')); SR = w.getframerate()
a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
words = []
for p in json.load(open(os.path.join(PROJ, 'sync', 'para_times.json'))):
    s0 = max(0, p['start'] - 0.15); s1 = min(len(a) / SR, p['end'] + 0.25)
    st = R.create_stream(); st.accept_waveform(SR, a[int(s0 * SR):int(s1 * SR)]); R.decode_stream(st); r = st.result
    toks, ts = r.tokens, r.timestamps
    cur = None
    for k, (tk, t) in enumerate(zip(toks, ts)):
        t = s0 + t
        if tk.startswith('▁') or tk.startswith(' ') or cur is None:
            if cur: words.append(cur)
            cur = {'w': tk.lstrip('▁ '), 'start': round(t, 3), 'end': round(t + 0.08, 3), 'para': p['scene_id']}
        else:
            cur['w'] += tk; cur['end'] = round(t + 0.08, 3)
    if cur: words.append(cur)
# end of a word = start of the next word in the same paragraph (capped), so key-word onsets are exact and ends are sane
for i, x in enumerate(words[:-1]):
    nx = words[i + 1]
    if nx['para'] == x['para']: x['end'] = round(min(nx['start'], x['end'] + 0.6), 3)
json.dump({'duration': len(a) / SR, 'model': 'parakeet-tdt-0.6b-v2-int8', 'words': words}, open(os.path.join(PROJ, 'sync', 'parakeet_words.json'), 'w'), indent=0)
print(len(words), 'words')
