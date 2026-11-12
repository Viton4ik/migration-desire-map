"""Voice with local Kokoro (kokoro-onnx, Apache 2.0), voice am_michael. python3 tools/gen_voice_kokoro.py [--force]
Model files: github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/{kokoro-v1.0.onnx,voices-v1.0.bin}; dir in env KOKORO."""
import csv, os, sys, json, soundfile as sf
from kokoro_onnx import Kokoro
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KD = os.environ.get('KOKORO', '/tmp/claude-0/-home-claude/df0984ad-f311-5254-a0a3-609fbc0cd6b9/scratchpad/kokoro/')
VOICE, SPEED = 'am_michael', 1.05
k = Kokoro(KD + 'kokoro-v1.0.onnx', KD + 'voices-v1.0.bin')
log = []
for s in csv.DictReader(open(os.path.join(ROOT, 'scenes.csv'))):
    out = os.path.join(ROOT, 'audio/para', s['scene_id'] + '.wav')
    if os.path.exists(out) and '--force' not in sys.argv: continue
    x, sr = k.create(s['voice_en_exact'], voice=VOICE, speed=SPEED, lang='en-us')
    sf.write(out, x, sr, subtype='PCM_16'); log.append(dict(scene=s['scene_id'], seconds=round(len(x) / sr, 2))); print(log[-1])
json.dump(dict(engine='kokoro-onnx v1.0 (Apache 2.0)', voice=VOICE, speed=SPEED, items=log), open(os.path.join(ROOT, 'audio/tts_log_kokoro.json'), 'w'), indent=1)
