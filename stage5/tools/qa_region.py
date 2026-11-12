"""QA of one exported region: part seams vs direct render, boundary vs previous region, audio null test.

usage: python3 tools/qa_region.py <RID> <N0> <N1> <workdir> [<prev RID>]
Needs node render/render.js (direct frames) and ffmpeg. Prints one line per check.
"""
import subprocess, sys, os, glob, json
import numpy as np
from PIL import Image

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS, SR = 30, 24000


def mf(src, n, out):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf', f'select=eq(n\\,{n})', '-vsync', '0', '-frames:v', '1', out], check=True)
    return np.asarray(Image.open(out).convert('RGB')).astype(float)


def psnr(a, b):
    return 10 * np.log10(255 ** 2 / np.mean((a - b) ** 2))


def pcm(args):
    out = subprocess.run(['ffmpeg', '-v', 'error'] + args + ['-f', 's16le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(out, np.int16).astype(float)


def main(rid, n0, n1, wd, prev=None):
    n0, n1 = int(n0), int(n1); os.makedirs(wd, exist_ok=True)
    M = os.path.join(PROJ, 'export', rid, rid + '.mp4')
    step = (n1 - n0 + 3) // 4; seams = [n0 + k * step for k in (1, 2, 3)]
    ns = sorted(set([n0] + [s + d for s in seams for d in (-1, 0)] + [n1 - 1]))
    subprocess.run(['node', 'render/render.js', 'frames', wd, ','.join('%.4f' % (n / FPS) for n in ns)], cwd=PROJ, check=True, capture_output=True)
    fs = glob.glob(os.path.join(wd, 'frame_*.png'))
    for n in ns:
        t = n / FPS
        f = min(fs, key=lambda x: abs(float(os.path.basename(x)[6:-5].replace('_', '.')) - t))
        print('frame', n, 'MP4 vs direct render PSNR %.1f dB' % psnr(mf(M, n - n0, os.path.join(wd, 'm%d.png' % n)), np.asarray(Image.open(f).convert('RGB')).astype(float)))
    if prev:
        a = mf(os.path.join(PROJ, 'export', prev, prev + '.mp4'), 10 ** 6, os.path.join(wd, 'prev_last.png')) if False else None
        pm = os.path.join(PROJ, 'export', prev, prev + '.mp4')
        cnt = int(subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', pm], capture_output=True, text=True).stdout)
        a = mf(pm, cnt - 1, os.path.join(wd, 'prev_last.png')); b = mf(M, 0, os.path.join(wd, 'first.png'))
        print('%s last vs %s first: changed px share %.4f, PSNR %.1f dB' % (prev, rid, (np.abs(a - b).max(2) > 40).mean(), psnr(a, b)))
    s0, s1 = n0 * SR // FPS, n1 * SR // FPS
    src = pcm(['-i', os.path.join(PROJ, 'audio', 'voice_en_edited.wav'), '-af', f'atrim=start_sample={s0}:end_sample={s1}'])
    dec = pcm(['-i', M]); n = min(len(src), len(dec))
    lag = max(range(-200, 201), key=lambda l: np.dot(src[1000:n - 1000], np.roll(dec, -l)[1000:n - 1000]))
    d = np.roll(dec, -lag)[:n]; g = np.dot(src[:n], d) / np.dot(d, d); r = src[:n] - g * d
    db = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) / 32768 + 1e-12)
    w = 2400; q = [np.sqrt(np.mean(dec[i:i + w] ** 2)) for i in range(0, n - w, w) if np.sqrt(np.mean(src[i:i + w] ** 2)) < 15]
    print('audio: lag %d samples, voice/residual %.1f dB, first 0.12 s %.1f dBFS, last 0.2 s %.1f dBFS, peak %.1f dBFS, quiet windows %d (max rms %.1f)' % (
        lag, 10 * np.log10(np.mean(src ** 2) / np.mean(r ** 2)), db(dec[:2880]), db(dec[n - 4800:n]), 20 * np.log10(np.abs(dec).max() / 32768), len(q), max(q) if q else 0))


if __name__ == '__main__':
    main(*sys.argv[1:])
