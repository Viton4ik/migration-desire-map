#!/usr/bin/env python3
"""Add ONE background music bed under the joined clean voice and mux it with the joined video.
usage: mix_music.py <video_full.mp4> <voice_full.wav> <music file> <out.mp4> <report.json> [--credit-check]
Music: looped with equal-power crossfades only if shorter than the film, cut to the film length, 2 s fade in,
3 s fade out. Ducking: speech activity from the clean voice (20 ms RMS > -45 dBFS, held 0.15 s), gain moves
smoothly (attack 0.25 s, release 0.9 s) between BED_DB in pauses and BED_DB - DUCK_DB under speech.
The video stream is copied untouched; the voice samples are not changed."""
import json, subprocess, sys, wave
import numpy as np
V, VOICE, MUS, OUT, REP = sys.argv[1:6]
SR, XF, FIN, FOUT = 48000, 2.0, 2.0, 3.0
BED_DB, DUCK_DB = -27.0, 11.0          # music RMS in pauses (dBFS), extra cut under speech

def dec(path, ch):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-ac', str(ch), '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).astype(np.float64)
voice = dec(VOICE, 1)[:, 0]; N = len(voice)
mus = dec(MUS, 2); M = len(mus)
rep = dict(music_file=MUS, music_s=round(M / SR, 3), film_s=round(N / SR, 3), loops=[], crossfade_s=None)
# 1. length: loop with equal-power crossfades only when needed, then cut
bed = mus.copy()
if M < N:
    x = int(XF * SR); t = np.linspace(0, np.pi / 2, x)[:, None]
    rep['crossfade_s'] = XF
    while len(bed) < N:
        rep['loops'].append(round((len(bed) - x) / SR, 3))
        bed = np.concatenate([bed[:-x], bed[-x:] * np.cos(t) + mus[:x] * np.sin(t), mus[x:]])
rep['trimmed'] = len(bed) > N
bed = bed[:N]
# 2. level: music RMS (over its non-silent part) to BED_DB
act = np.sqrt(np.mean(bed ** 2, axis=1)); ref = np.sqrt(np.mean(act[act > 1e-4] ** 2))
bed *= 10 ** (BED_DB / 20) / ref
# 3. ducking envelope from the clean voice
w = int(0.02 * SR); nw = N // w
rms = np.sqrt(np.mean(voice[:nw * w].reshape(nw, w) ** 2, axis=1))
speech = 20 * np.log10(rms + 1e-12) > -45
hold = int(0.15 / 0.02); sp = speech.copy()
for k in range(1, hold + 1): sp[:-k] |= speech[k:]; sp[k:] |= speech[:-k]
target = np.where(sp, -DUCK_DB, 0.0); g = np.zeros_like(target); cur = 0.0
a_att, a_rel = 1 - np.exp(-0.02 / 0.25), 1 - np.exp(-0.02 / 0.9)
for i, tg in enumerate(target):
    cur += (tg - cur) * (a_att if tg < cur else a_rel); g[i] = cur
gain_db = np.interp(np.arange(N), np.arange(nw) * w + w / 2, g)
fade = np.ones(N); fi, fo = int(FIN * SR), int(FOUT * SR)
fade[:fi] = np.sin(np.linspace(0, np.pi / 2, fi)) ** 2; fade[-fo:] = np.cos(np.linspace(0, np.pi / 2, fo)) ** 2
bed *= (10 ** (gain_db / 20) * fade)[:, None]
mix = bed + voice[:, None]
peak = float(np.max(np.abs(mix)))
safety = min(1.0, 10 ** (-1 / 20) / peak)   # keep peaks at or below -1 dBFS with one static gain, no limiter pumping
mix *= safety
step_db = float(np.max(np.abs(np.diff(g))))
rep.update(bed_db=BED_DB, duck_db=DUCK_DB, attack_s=0.25, release_s=0.9, fade_in_s=FIN, fade_out_s=FOUT,
           speech_share=round(float(sp.mean()), 3), max_gain_step_db_per_20ms=round(step_db, 3),
           peak_dbfs_before_safety=round(20 * np.log10(peak), 2), static_safety_gain_db=round(20 * np.log10(safety), 2),
           clipped_samples=int(np.sum(np.abs(mix) >= 1.0)))
tmp = OUT + '.mix.wav'
with wave.open(tmp, 'wb') as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes((np.clip(mix, -1, 1) * 32767).astype('<i2').tobytes())
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', V, '-i', tmp, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k',
                '-movflags', '+faststart', OUT], check=True)
json.dump(rep, open(REP, 'w'), indent=1)
print(json.dumps(rep, indent=1))
