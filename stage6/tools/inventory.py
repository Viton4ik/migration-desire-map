#!/usr/bin/env python3
"""Stage 6 inventory: region clips vs the accepted plan, registry and edited voice timeline.
usage: inventory.py <stage5 proj dir> <registry countries.csv> <out dir>"""
import csv, json, subprocess, sys, wave, hashlib, os, collections
import numpy as np
P, REG, OUT = sys.argv[1:4]
FPS, SR = 30, 24000

def probe(f):
    j = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', f]))
    v = next(s for s in j['streams'] if s['codec_type'] == 'video')
    a = [s for s in j['streams'] if s['codec_type'] == 'audio']
    return v, (a[0] if a else None), float(j['format']['duration'])

def stream_md5(f, sel):
    o = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', f, '-map', sel, '-c', 'copy', '-f', 'md5', '-'])
    return o.decode().strip().split('=')[1]

def pcm(f):
    w = wave.open(f); return np.frombuffer(w.readframes(w.getnframes()), np.int16), w.getframerate(), w.getnchannels()

ep_src = open(f'{P}/data/episode.js').read()
E = json.loads(ep_src[ep_src.index('{'):ep_src.rindex('}') + 1])
master, msr, _ = pcm(f'{P}/audio/voice_en_edited.wav')
rows, prev_n1, problems = [], 0, []
for R in E['regions']:
    rid = R['id']; d = f'{P}/export/{rid}'
    mp4 = f'{d}/{rid}.mp4'
    if not os.path.exists(mp4):
        problems.append(f'{rid}: MP4 missing'); continue
    iv = json.load(open(f'{d}/interval.json'))
    v, a, dur = probe(mp4)
    nb = int(v['nb_frames'])
    voice, vsr, vch = pcm(f'{d}/voice_{rid}.wav')
    s0, s1 = iv['n0'] * SR // FPS, iv['n1'] * SR // FPS
    voice_ok = vsr == msr == SR and np.array_equal(voice, master[s0:s1])
    vid_same = stream_md5(mp4, '0:v') == stream_md5(f'{d}/video_silent.mp4', '0:v')
    # decoded audio of the clip must exist and match the frame span
    adur = float(a['duration']) if a else 0
    ck = f'{P}/sync/checkpoint_{rid}_end.json'
    row = dict(region=rid, name=R['name'], file=f'export/{rid}/{rid}.mp4', n0=iv['n0'], n1=iv['n1'],
               plan_n0=R['n0'], plan_n1=R['n1'], contiguous=iv['n0'] == prev_n1,
               frames=nb, frames_expected=iv['n1'] - iv['n0'], t0_s=round(iv['n0'] / FPS, 3), t1_s=round(iv['n1'] / FPS, 3),
               video_s=round(nb / FPS, 3), audio_s=round(adur, 3), width=v['width'], height=v['height'], fps=v['r_frame_rate'],
               vcodec=f"{v['codec_name']} {v.get('profile')}", pix_fmt=v['pix_fmt'],
               acodec=a['codec_name'] if a else 'NONE', a_rate=a['sample_rate'] if a else '', a_ch=a['channels'] if a else '',
               voice_stem=f'voice_{rid}.wav', voice_samples=f'[{s0}, {s1})', voice_equals_timeline_slice=voice_ok,
               video_silent_equals_mp4_video=vid_same, end_checkpoint=os.path.exists(ck),
               countries_plan=R['countries'], last_word=R['lastWord']['w'], next_word=(R.get('nextWord') or {}).get('w', '(end)'))
    for k, ok in [('contiguous', row['contiguous']), ('frames', nb == row['frames_expected']),
                  ('plan', (iv['n0'], iv['n1']) == (R['n0'], R['n1'])), ('voice', voice_ok), ('video', vid_same),
                  ('audio', a is not None and abs(adur - nb / FPS) < 0.05)]:
        if not ok: problems.append(f'{rid}: {k} check failed')
    rows.append(row); prev_n1 = iv['n1']
total_frames = prev_n1
if total_frames * SR // FPS > len(master): problems.append('timeline longer than voice WAV')

# coverage vs registry
reg = list(csv.DictReader(open(REG)))
stops = E['stops']
codes = [s['code'] for s in stops]
dup = [c for c, n in collections.Counter(codes).items() if n > 1]
reg_codes = [r['code'] for r in reg]
per_reg = collections.Counter(s['region'] for s in stops)
per_reg_registry = collections.Counter(r['region_id'] for r in reg)
cont = collections.Counter(r['continent'] for r in reg if r['code'] in set(codes))
mismatch_status = [s['code'] for s in stops for r in reg if r['code'] == s['code'] and r['status'] != s['status']]
mismatch_region = [s['code'] for s in stops for r in reg if r['code'] == s['code'] and r['region_id'] != s['region']]
cov = dict(distinct_countries=len(set(codes)), stops=len(codes), duplicates=dup,
           missing_vs_registry=sorted(set(reg_codes) - set(codes)), extra_vs_registry=sorted(set(codes) - set(reg_codes)),
           per_region_episode=dict(per_reg), per_region_registry=dict(per_reg_registry),
           regions_under_10=[k for k, n in per_reg.items() if n < 10], by_continent=dict(cont),
           status_totals=dict(collections.Counter(s['status'] for s in stops)),
           status_mismatch_vs_registry=mismatch_status, region_mismatch_vs_registry=mismatch_region)
for k in ('duplicates', 'missing_vs_registry', 'extra_vs_registry', 'regions_under_10', 'status_mismatch_vs_registry', 'region_mismatch_vs_registry'):
    if cov[k]: problems.append(f'coverage: {k} = {cov[k]}')
if len(set(codes)) < 100: problems.append('coverage under 100')

with open(f'{OUT}/clips_inventory.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
json.dump(dict(total_frames=total_frames, total_s=total_frames / FPS, voice_wav_s=len(master) / SR,
               coverage=cov, problems=problems), open(f'{OUT}/inventory_summary.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(dict(total_frames=total_frames, total_s=round(total_frames / FPS, 3), coverage=cov, problems=problems), ensure_ascii=False, indent=1))
