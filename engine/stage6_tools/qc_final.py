#!/usr/bin/env python3
"""Stage 6 final QC of the joined episode.
usage: qc_final.py <final.mp4> <stage5 proj dir> <voice_full.wav> <out dir>
Checks: full decode, packets == region clips, black frames, audio vs voice timeline, every seam
(boundary frames, state diff, speech gap, audio residual and jumps), start and end."""
import json, subprocess, sys, wave, os
import numpy as np
F, P, VW, OUT = sys.argv[1:5]
FPS, SR = 30, 24000
os.makedirs(f'{OUT}/seams', exist_ok=True)
src = open(f'{P}/data/episode.js').read(); E = json.loads(src[src.index('{'):src.rindex('}') + 1])
REG = E['regions']; res = {'file': os.path.basename(F)}

def run(cmd): return subprocess.run(cmd, capture_output=True, text=True)

# 1. full decode, stop on first error
r = run(['ffmpeg', '-v', 'error', '-xerror', '-i', F, '-f', 'null', '-'])
res['full_decode_errors'] = r.stderr.strip() or 'none'
pr = json.loads(run(['ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', F]).stdout)
v = next(s for s in pr['streams'] if s['codec_type'] == 'video'); a = next(s for s in pr['streams'] if s['codec_type'] == 'audio')
res['video'] = dict(codec=v['codec_name'], profile=v.get('profile'), size=f"{v['width']}x{v['height']}", fps=v['r_frame_rate'],
                    pix_fmt=v['pix_fmt'], frames=int(v['nb_read_frames']), duration_s=float(v['duration']))
res['audio'] = dict(codec=a['codec_name'], rate=int(a['sample_rate']), channels=a['channels'], duration_s=float(a['duration']))
res['container_duration_s'] = float(pr['format']['duration'])
res['frames_expected'] = REG[-1]['n1']

# 2. packets identical to the accepted region clips
def pk(f): return [l.split(',')[-1].strip() for l in run(['ffmpeg', '-v', 'error', '-i', f, '-map', '0:v', '-c', 'copy', '-f', 'framemd5', '-']).stdout.splitlines() if not l.startswith('#')]
fin = pk(F); srcpk = []
for R in REG: srcpk += pk(f"{P}/export/{R['id']}/{R['id']}.mp4")
res['video_packets_equal_region_clips'] = fin == srcpk

# 3. black frames
r = run(['ffmpeg', '-i', F, '-vf', 'blackdetect=d=0.03:pix_th=0.10', '-an', '-f', 'null', '-'])
res['black_segments'] = [l.split('blackdetect')[1].strip() for l in r.stderr.splitlines() if 'black_start' in l]

# 4. audio: decoded final vs voice timeline
def wav(f):
    w = wave.open(f); return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
voice = wav(VW)
tmp = f'{OUT}/_dec.wav'
run(['ffmpeg', '-v', 'error', '-y', '-i', F, '-map', '0:a', '-ac', '1', '-ar', str(SR), '-c:a', 'pcm_s16le', tmp])
dec = wav(tmp); os.remove(tmp)
seg = slice(SR * 10, SR * 20)
xc = [np.dot(dec[seg.start + k:seg.stop + k], voice[seg]) for k in range(-200, 201)]
lag = int(np.argmax(xc)) - 200
n = min(len(dec) - max(lag, 0), len(voice))
d = dec[max(lag, 0):max(lag, 0) + n]; vv = voice[:n]
# AAC stereo upmix + mono downmix changes the level (about -3 dB), so fit one gain like stage-5 qa_region.py
G = float(np.dot(vv, d) / np.dot(d, d))
def snr(x, y): x = G * x; return 10 * np.log10(np.sum(y ** 2) / max(np.sum((x - y) ** 2), 1e-20))
res['audio_check'] = dict(lag_samples=lag, level_gain_fit=round(G, 4), voice_over_residual_db=round(snr(d, vv), 2),
                          decoded_s=round(len(dec) / SR, 3), voice_timeline_s=round(len(voice) / SR, 3),
                          peak_dbfs=round(20 * np.log10(np.max(np.abs(dec)) + 1e-12), 2),
                          clipped_samples=int(np.sum(np.abs(dec) >= 0.999)))
win = int(0.05 * SR); rms = np.sqrt(np.convolve(dec ** 2, np.ones(win) / win, 'same'))
res['audio_check']['speech_rms_p95_dbfs'] = round(20 * np.log10(np.percentile(rms, 95) + 1e-12), 2)

# 5. seams
def frame(n, path):
    out = f'{OUT}/seams/f{n:05d}.png'
    if n >= REG[-1]['n1'] - 1:  # last frame: seek from the end and keep the final decoded picture
        run(['ffmpeg', '-v', 'error', '-y', '-sseof', '-0.3', '-i', F, '-update', '1', out]); return out
    run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{n / FPS + 0.001:.4f}', '-i', F, '-frames:v', '1', out]); return out
def gray_b(n):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{n / FPS + 0.001:.4f}', '-i', F, '-frames:v', '1', '-vf', 'scale=480:270', '-pix_fmt', 'gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).astype(np.int16)
seams = []
for i in range(len(REG) - 1):
    A, B = REG[i], REG[i + 1]; n = A['n1']; ts = n / FPS
    g = {k: gray_b(n + k) for k in (-2, -1, 0, 1)}
    def pct(x, y): return round(100 * np.mean(np.abs(x - y) > 12), 3)
    s0 = n * SR // FPS
    a_ctx = dec[max(lag, 0) + s0 - SR: max(lag, 0) + s0 + SR]
    jumps = np.abs(np.diff(dec[max(lag, 0) + s0 - 240: max(lag, 0) + s0 + 240]))
    vr = voice[s0 - int(0.04 * SR): s0 + int(0.04 * SR)]
    lw, nw = A['lastWord'], B['lastWord'] and A.get('nextWord')
    def silent(t):
        x = voice[int(t * SR):int(t * SR) + int(0.02 * SR)]; return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12) < -45
    gb = 0.0
    while silent(ts - gb - 0.02) and gb < 3: gb += 0.02
    ga = 0.0
    while silent(ts + ga) and ga < 3: ga += 0.02
    seams.append(dict(silence_before_cut_s=round(gb, 2), silence_after_cut_s=round(ga, 2),seam=f"{A['id']}->{B['id']}", frame=n, interval_prev=f"[{A['n0']}, {A['n1']})", interval_next=f"[{B['n0']}, {B['n1']})",
                      time_s=round(ts, 3), last_word=lw['w'], last_word_end_s=lw['end'], gap_before_s=round(ts - lw['end'], 3),
                      next_word=nw['w'], next_word_start_s=nw['start'], gap_after_s=round(nw['start'] - ts, 3),
                      voice_rms_at_cut_dbfs=round(20 * np.log10(np.sqrt(np.mean(vr ** 2)) + 1e-12), 1),
                      decoded_max_jump_at_cut=round(float(jumps.max()), 4),
                      residual_db_pm1s=round(snr(a_ctx, voice[s0 - SR:s0 + SR]), 2),
                      px_changed_pct_prev_step=pct(g[-2], g[-1]), px_changed_pct_at_seam=pct(g[-1], g[0]), px_changed_pct_next_step=pct(g[0], g[1]),
                      png=[os.path.basename(frame(k, F)) for k in (n - 30, n - 1, n, n + 29)]))
res['seams'] = seams
# 6. start and end
res['start_end_png'] = [os.path.basename(frame(k, F)) for k in (0, 60, 207, res['frames_expected'] - 1)]
tail = dec[-SR:]; res['audio_last_1s_rms_dbfs'] = round(20 * np.log10(np.sqrt(np.mean(tail ** 2)) + 1e-12), 1)
problems = []
if res['full_decode_errors'] != 'none': problems.append('decode errors')
if res['video']['frames'] != res['frames_expected']: problems.append('frame count')
if not res['video_packets_equal_region_clips']: problems.append('video packets differ from region clips')
if res['black_segments']: problems.append('black frames')
if res['audio_check']['lag_samples'] != 0 or res['audio_check']['voice_over_residual_db'] < 25: problems.append('audio vs voice')
if res['audio_check']['clipped_samples']: problems.append('clipping')
for s in seams:
    if s['silence_before_cut_s'] < 0.1 or s['silence_after_cut_s'] < 0.1: problems.append(f"{s['seam']}: speech too close to cut")
    if s['voice_rms_at_cut_dbfs'] > -45: problems.append(f"{s['seam']}: speech at cut")
    if s['px_changed_pct_at_seam'] > 5: problems.append(f"{s['seam']}: visual jump")
res['problems'] = problems
json.dump(res, open(f'{OUT}/final_qc.json', 'w'), indent=1, ensure_ascii=False)
import csv
with open(f'{OUT}/seams_table.csv', 'w', newline='') as f:
    ks = [k for k in seams[0] if k != 'png']; w = csv.writer(f); w.writerow(ks)
    for s in seams: w.writerow([float(s[k]) if isinstance(s[k], np.floating) else s[k] for k in ks])
print(json.dumps({k: res[k] for k in res if k != 'seams'}, indent=1, ensure_ascii=False))
for s in seams: print({k: s[k] for k in s if k != 'png'})
