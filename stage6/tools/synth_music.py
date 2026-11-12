#!/usr/bin/env python3
"""Background music for "Countries People Want to LEAVE vs MOVE TO", synthesized in code (no samples, no third-party audio).
usage: synth_music.py <out.wav> <seconds>
Deterministic (seed 20261104). 100 BPM, A minor / C major travel groove: vi-IV-I-V (Am F C G), 1 bar per chord.
Layers: warm pad, plucked arpeggio, round bass, soft kick/snare/hat, bell motif on B sections. Simple
convolution reverb from a decaying noise impulse. Form: 4-bar intro, 16-bar A/B sections, a 4-bar
drum-free breath every 32 bars, 2-bar tail. 48 kHz stereo 16-bit."""
import sys, wave
import numpy as np
OUT, DUR = sys.argv[1], float(sys.argv[2])
SR, BPM = 48000, 100.0
BEAT = 60 / BPM; BAR = 4 * BEAT
rng = np.random.default_rng(20261104)
N = int((DUR + 4) * SR)
L = {k: np.zeros((N, 2)) for k in ('pad', 'pluck', 'bass', 'drums', 'bell')}

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def add(buf, t0, sig, pan=0.0):
    i = int(t0 * SR); j = min(N, i + len(sig))
    if j <= i: return
    gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i:j, 0] += sig[:j - i] * gl; buf[i:j, 1] += sig[:j - i] * gr

def tone(f, d, harm, decay=None, att=0.005, rel=0.05, det=0.0):
    n = int(d * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for k, a in enumerate(harm, 1):
        if f * k > 16000: break
        s += a * np.sin(2 * np.pi * f * k * t * (1 + det))
    env = np.minimum(1, t / att) * np.minimum(1, (d - t) / rel).clip(0)
    if decay: env *= np.exp(-t / decay)
    return s * env

# chords: Am F C G (MIDI)
CH = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
ROOT = [45, 41, 48, 43]
saw = [1 / k * (0.85 ** k) for k in range(1, 14)]
nb = int(np.ceil(DUR / BAR)) + 1
MOTIF = [[76, None, 72, 74, None, 76, 79, None], [77, None, 76, 72, None, 69, 72, None],
         [76, None, 79, 76, None, 72, 74, None], [74, None, 71, 74, None, 79, 74, None]]
for b in range(nb):
    t0 = b * BAR; c = b % 4
    intro = b < 4; outro = b >= nb - 2
    sec = (b - 4) // 16 if b >= 4 else -1
    breath = (not intro) and ((b - 4) % 32) >= 28
    # pad: whole bar, detuned pair, wide stereo
    for m in CH[c]:
        for det, pan in ((-0.0025, -0.6), (0.0025, 0.6)):
            add(L['pad'], t0, tone(hz(m), BAR + 0.6, saw, att=0.35, rel=0.6, det=det) * 0.055, pan)
    if outro: continue
    # pluck arpeggio, 8ths (from bar 2)
    if b >= 2:
        arp = CH[c] + [CH[c][0] + 12, CH[c][1] + 12, CH[c][2], CH[c][1], CH[c][0] + 12]
        for k in range(8):
            m = arp[k] + 12
            add(L['pluck'], t0 + k * BEAT / 2, tone(hz(m), 0.9, [1, 0.45, 0.2, 0.08], decay=0.22) * 0.09, -0.35 + 0.1 * (k % 3))
    if intro: continue
    # bass: root on 1, 2-and, 3, octave on 4
    for k, (pos, oct_, d) in enumerate(((0, 0, 0.8), (1.5, 0, 0.4), (2, 0, 0.8), (3, 12, 0.6))):
        add(L['bass'], t0 + pos * BEAT, tone(hz(ROOT[c] + oct_), d * BEAT, [1, 0.35, 0.1], decay=0.5, rel=0.08) * 0.22)
    if breath: continue
    # drums
    for k in range(4):
        tb = t0 + k * BEAT
        if k in (0, 2):
            n = int(0.35 * SR); t = np.arange(n) / SR
            ph = 2 * np.pi * np.cumsum(45 + 75 * np.exp(-t / 0.03)) / SR
            add(L['drums'], tb, np.sin(ph) * np.exp(-t / 0.12) * 0.42)
        if k in (1, 3):
            n = int(0.25 * SR); t = np.arange(n) / SR
            nz = rng.standard_normal(n); nz = nz - np.convolve(nz, np.ones(6) / 6, 'same')
            add(L['drums'], tb, (nz * 0.11 + np.sin(2 * np.pi * 190 * t) * 0.08) * np.exp(-t / 0.07), 0.1)
        for h in (0.5,) if sec % 2 == 0 else (0.5, 0.75):
            n = int(0.06 * SR); t = np.arange(n) / SR
            nz = np.diff(rng.standard_normal(n + 1))
            add(L['drums'], tb + h * BEAT, nz * np.exp(-t / 0.015) * 0.05, 0.4)
    # bell motif on B sections
    if sec % 2 == 1:
        for k, m in enumerate(MOTIF[c]):
            if m: add(L['bell'], t0 + k * BEAT / 2, tone(hz(m), 1.6, [1, 0, 0.3, 0, 0.12], decay=0.45) * 0.07, 0.3)

def reverb(x, secs=1.8, mix=0.25):
    n = int(secs * SR); t = np.arange(n) / SR
    ir = np.stack([rng.standard_normal(n), rng.standard_normal(n)], 1) * np.exp(-t / 0.45)[:, None]
    ir[:int(0.01 * SR)] = 0; ir /= np.sqrt(np.sum(ir ** 2, 0))
    out = np.zeros_like(x); B = 1 << 17; F = 1 << int(np.ceil(np.log2(B + n)))
    IR = np.fft.rfft(ir, F, axis=0)
    for i in range(0, len(x), B):
        blk = np.fft.irfft(np.fft.rfft(x[i:i + B], F, axis=0) * IR, F, axis=0)
        j = min(len(x), i + F); out[i:j] += blk[:j - i]
    return x + out * mix

mix = reverb(L['pad'] + L['pluck'] * 0.9 + L['bell'], mix=0.35) + L['bass'] + reverb(L['drums'], 0.8, 0.12)
mix = np.tanh(mix * 1.2) / 1.2
mix = mix[:int(DUR * SR)]
fo = int(3 * SR); mix[-fo:] *= np.cos(np.linspace(0, np.pi / 2, fo))[:, None] ** 2
mix *= 0.89 / np.max(np.abs(mix))
with wave.open(OUT, 'wb') as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes((mix * 32767).astype('<i2').tobytes())
print('bars', nb, 'peak ok', OUT)
