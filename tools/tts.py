"""Gemini TTS: python3 tools/tts.py MODEL VOICE out.wav "text" [style]. Key from env GEMINI_KEY (never stored)."""
import os, sys, json, base64, wave, urllib.request, urllib.error
model, voice, out, text = sys.argv[1:5]; style = sys.argv[5] if len(sys.argv) > 5 else ''
body = {'contents': [{'parts': [{'text': (style + '\n\n' + text) if style else text}]}],
        'generationConfig': {'responseModalities': ['AUDIO'], 'speechConfig': {'voiceConfig': {'prebuiltVoiceConfig': {'voiceName': voice}}}}}
req = urllib.request.Request(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent', data=json.dumps(body).encode(),
                             headers={'Content-Type': 'application/json', 'x-goog-api-key': os.environ['GEMINI_KEY']})
try:
    r = json.load(urllib.request.urlopen(req, timeout=300))
except urllib.error.HTTPError as e:
    print('HTTP', e.code, e.read().decode()[:600]); sys.exit(2)
part = r['candidates'][0]['content']['parts'][0]['inlineData']
raw = base64.b64decode(part['data'])
if raw[:4] == b'RIFF':
    open(out, 'wb').write(raw); w = wave.open(out); print(json.dumps({'out': out, 'mime': part['mimeType'], 'seconds': round(w.getnframes() / w.getframerate(), 2), 'rate': w.getframerate(), 'usage': r.get('usageMetadata', {})})); sys.exit(0)
pcm = raw; rate = int(part['mimeType'].split('rate=')[1].split(';')[0]) if 'rate=' in part['mimeType'] else 24000
with wave.open(out, 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(pcm)
print(json.dumps({'out': out, 'mime': part['mimeType'], 'seconds': round(len(pcm) / 2 / rate, 2), 'usage': r.get('usageMetadata', {})}))
