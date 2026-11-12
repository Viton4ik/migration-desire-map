Countries People Want to LEAVE vs MOVE TO - stage 6, final assembly (2026-11-05)

RESULT
  Countries_People_Want_to_LEAVE_vs_MOVE_TO_final.mp4       1920x1080, 30 fps, H.264 High yuv420p, 17497 frames, 583.233 s (9:43), AAC 48 kHz stereo 256 kb/s,
                       voice + music, -14.3 LUFS integrated, true peak -1.4 dBTP.
  Countries_People_Want_to_LEAVE_vs_MOVE_TO_voice_only.mp4  backup without music (-17.0 LUFS).
  Coverage: 159 distinct countries, 11 regions (10-20 each), no duplicates, all match countries.csv (qa/inventory_summary.json).

HOW IT WAS BUILT
  1. Video: export/Rxx/video_silent.mp4 of the 11 regions joined with the concat demuxer, -c copy. Packets equal the accepted region clips.
  2. Voice: export/Rxx/voice_Rxx.wav joined = audio/voice_en_edited.wav bit for bit (583.231 s, 2 ms shorter than the picture).
     Processing (voice_chain.txt): 48 kHz, +8 dB, compressor 2.5:1 at -18 dB, +6 dB, limiter -1.5 dB with latency compensation -> -16.1 LUFS.
  3. Music: tools/synth_music.py -> music/bed_synth.wav (own work). tools/mix_music.py: bed -24 dBFS RMS in pauses,
     -11 dB under speech (attack 0.25 s, release 0.9 s), fades 2 s / 3 s. Measured: bed 19.1 dB below the voice under speech.
  4. Final audio (final_audio_chain.txt): -0.8 dB and a -4 dB limiter before AAC, because the AAC encoder overshot to +1.9 dBFS without it.
  Commands: see tools/*.py headers. Re-render a region: stage5 render/render_region.sh Rxx n0 n1 4.

CHECKS (qa/)
  final_qc.json        full decode (no errors), 17497 frames, packets == region clips, no black frames, audio lag 0, no clipped samples.
                       Two flags are expected and explained in note_problems (residual vs raw voice; camera moving at the R08/R09 seam).
  seams_table.csv      10 seams: last/next word, real silence around every cut (0.16-1.54 s), pixel change at the cut.
  seams_sheet.jpg      frames n-30, n-1, n, n+29 of every seam.
  mix_report.json      ducking and level numbers.
NOT CHECKED: nobody has listened to or watched the whole file yet.
