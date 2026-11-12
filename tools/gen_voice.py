"""Generate every voice paragraph with Gemini TTS (key from env GEMINI_KEY). Skips paragraphs that already exist."""
import csv, os, subprocess, time, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL, VOICE = 'gemini-3.8-flash-tts', 'Bodi'
STYLE = 'Read the following as a lively, curious map-game commentator: upbeat, light humour, clear numbers, natural pace.'
log = []
for s in csv.DictReader(open(os.path.join(ROOT, 'scenes.csv'))):
    out = os.path.join(ROOT, 'audio/para', s['scene_id'] + '.wav')
    if os.path.exists(out) and '--force' not in sys.argv: continue
    for attempt in range(6):
        r = subprocess.run(['python3', os.path.join(ROOT, 'tools/tts.py'), MODEL, VOICE, out, s['voice_en_exact'], STYLE], capture_output=True, text=True)
        if r.returncode == 0: print(s['scene_id'], r.stdout[:90]); log.append(json.loads(r.stdout)); break
        print(s['scene_id'], 'retry', attempt, r.stdout[:300]); time.sleep(20 * (attempt + 1))
    else: sys.exit('failed ' + s['scene_id'])
json.dump(dict(model=MODEL, voice=VOICE, style=STYLE, items=log), open(os.path.join(ROOT, 'audio/tts_log.json'), 'a'))
