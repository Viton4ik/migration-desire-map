"""Build the edited voice timeline from the untouched source WAV and sync/audio_edits.json.

usage: python3 tools/audio_edit.py      -> audio/voice_en_edited.wav + sync/audio_mapping.json
Also importable: src2edit(t_seconds) maps a source time to the edited timeline (used by build_episode.py).
Inserted audio is digital silence; the source pause around it measures about -70 dBFS, so the join is inaudible.
"""
import json, os, wave
import numpy as np

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDITS = json.load(open(os.path.join(PROJ, 'sync', 'audio_edits.json')))
SR = EDITS['sample_rate']
INS = sorted(EDITS['inserts'], key=lambda x: x['at_source_sample'])


def src2edit_samples(s):
    return s + sum(i['samples'] for i in INS if i['at_source_sample'] <= s)


def src2edit(t):
    return src2edit_samples(t * SR) / SR


def src2edit_before(t):
    # a cut point that sits exactly on an insert stays BEFORE the inserted silence (the silence opens the next region)
    s = t * SR
    return (s + sum(i['samples'] for i in INS if i['at_source_sample'] < s - 0.5)) / SR


def main():
    w = wave.open(os.path.join(PROJ, 'audio', 'voice_en_source.wav'))
    assert w.getframerate() == SR and w.getnchannels() == 1 and w.getsampwidth() == 2
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16)
    parts, segs, prev, off = [], [], 0, 0
    for i in INS:
        s = i['at_source_sample']
        parts += [a[prev:s], np.zeros(i['samples'], np.int16)]
        segs.append({'source_samples': [prev, s], 'edited_samples': [prev + off, s + off]})
        segs.append({'inserted_silence': [s + off, s + off + i['samples']], 'reason': i['reason']})
        off += i['samples']; prev = s
    parts.append(a[prev:]); segs.append({'source_samples': [prev, len(a)], 'edited_samples': [prev + off, len(a) + off]})
    out = np.concatenate(parts)
    o = wave.open(os.path.join(PROJ, 'audio', 'voice_en_edited.wav'), 'wb'); o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR)
    o.writeframes(out.tobytes()); o.close()
    json.dump({'note': 'source-audio -> edited-timeline mapping. Nothing was cut or sped up; silence only where listed in sync/audio_edits.json.',
               'fps': 30, 'sample_rate': SR, 'samples_per_frame': SR // 30, 'source_samples': len(a), 'edited_samples': len(out),
               'segments': segs}, open(os.path.join(PROJ, 'sync', 'audio_mapping.json'), 'w'), indent=1)
    print('edited', len(out) / SR, 's, inserted', off / SR, 's')


if __name__ == '__main__':
    main()
