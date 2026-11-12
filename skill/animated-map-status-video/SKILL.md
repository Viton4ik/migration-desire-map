---
name: animated-map-status-video
description: Make an English YouTube animated world-map video where every country gets a status, a face and a number (e.g. "Countries People Want to LEAVE vs MOVE TO"), stage by stage 0-7 with the user's approval after each stage.
---

# Animated status-map video (stages 0-7)

Use this for videos of the type "Countries that X vs Y": the camera flies over 100-160 countries region by region,
each country fills with its flag, gets a cartoon face, a status colour and a number chip, a narrator names it,
and the film ends on a final map with totals. Proven on "Countries That LOVE vs HATE the USA" (156 countries, 14:09)
and "Countries People Want to LEAVE vs MOVE TO" (159 countries, 9:43).

Full stage prompts and the lessons behind them: `references/pipeline_animated_map_video.md` (Russian).
Working engine and tools to copy: the last finished project folder (`engine/`, `stage5/`, `stage6/tools`, `stage7/thumbnail`).

## Working rules (do not skip)

- **One stage at a time.** Finish a stage, show it, wait for the user's OK before the next. Exception: in stage 5,
  after the first region the user may say "все без вопросов" -> render the rest one by one with QA and collect questions at the end.
- **Replies to the user in Russian, short, unwelcome truth first**, confidence tags [Точно]/[Вероятно]/[Догадка],
  no em-dashes. Channel text (title, voice, description) in English.
- **Links are https artifact pages**, never /mnt paths. Heavy files (MP4, ZIP) go to the project folder and as message attachments.
- **API keys pasted in chat are never written to files or memory.** Pass them only via an env variable for one command.
  Generate nothing paid (TTS, images, music) without an explicit "go".
- **Every number on screen comes from the registry** (`countries.csv`) with source and year; nothing typed by hand in scenes.
- Never claim you listened to or watched something. Automatic checks are numbers; say what is left for the user's eyes and ears.

## Project layout

```
{ROOT}/ project_brief.txt, project_status.txt (log every stage with date and decision)
  music/ engine/ countries.csv facts.csv scenes.csv sources.txt voice_en.txt voice_ru.txt voice_numbers.csv
  audio/ sync/ stage4/ stage5/(index.html data/ render/ tools/ export/Rxx/) stage6/ stage7/
```

## Stage 0. Environment, music, engine
- Check what the network allows (usually npm, PyPI, GitHub only). Chromium + Playwright are preinstalled; do not reinstall.
- Music decided here: a CC0 track with a verified licence, or a code-synthesized bed (own work, no attribution).
- ASR for voice acceptance must work now: sherpa-onnx + Parakeet TDT 0.6B v2 int8 (GitHub release assets).
- Copy the engine template (canvas page, `drawFrame(t)` pure function of time, headless render).

## Stage 1. Title from a donor
- The user gives a donor video/thumbnail. Keep the donor title structure; the user picks the final title, then it is verbatim forever.
- Agree the metrics and the status scale (4-6 statuses, diverging colours, one icon each) and the data-quality marks
  (main source plain; other survey dotted outline; model estimate hatched).

## Stage 2. Research, route, script
- `countries.csv`: code, m49, name, short_name (for long names), region, status, basis, quality, numbers with period and source id.
- Route: 10-11 regions of 10-20 countries, geographic order, no backtracking. `scenes.csv` lists shots and which number is spoken.
- Script: intro of exactly 2 sentences landing on the first country; transitions "Next stop"; numbers written as the narrator says them
  (`voice_numbers.csv`). Mark every number that is not spoken as a silent chip.
- `fact_check.html` page with every claim and its source. Prefer official pages over Wikipedia.

## Stage 3. Voice and acceptance
- TTS options that worked: Kokoro `am_michael` (kokoro-onnx, Apache 2.0, local) or the user's own Gemini key.
  sherpa kokoro lexicon mode drops out-of-vocabulary words; use kokoro-onnx with espeak phonemes.
- Put flight pauses into the text/WAV now (0.6-1.6 s before each "Next stop"), not later.
- Acceptance = ASR the WAV per paragraph and align to the script (`tools/align.py`; >= 98% tokens matched), check every number
  in `voice_numbers.csv` is heard exactly. Show a voice check page with audio and the diff.

## Stage 4. 10-second visual test
- 3 countries, silent, plus technical frames picked automatically from the data: longest name, smallest face, too-small countries,
  enclave/holes, most complex flag, widest (flag strict vs stretched), most elongated, each quality mark, the status sheet.
- Decisions from past projects: stripe flags of very wide countries stretched to width; very elongated countries (Chile) get the face
  in a cloud callout beside them; countries too small for a face get a camera "punch" zoom in and back out; after the camera leaves,
  the flag wipes radially into the status colour so the map becomes the answer.

## Stage 5. Sync and render by region
- Word timestamps: run ASR per paragraph -> `sync/parakeet_words.json`; align to script words; unmatched words interpolated.
- `tools/build_mig.py`-style builder: plan per region (shots, `arrive_at` phrase, stops `at` phrase, `num_at` phrase, events) ->
  `data/episode.js` + `sync/sync_table.csv` + `sync/region_Rxx.json`.
- Timing rules that held up:
  - shot fly starts after the previous line ends (max 1.6 s before the next line); first country activates at
    `min(wordT, max(fly+0.3, arrive-0.3))`, others at `wordT-0.08`;
  - spoken numbers appear on the word; silent chips at activation+0.45; chips in one shot queue with >= 1.1 s each;
  - **dwell rule**: the last chip of a shot stays >= 1.25 s before the camera leaves, also across region boundaries
    (fast lists put ~1 country per second; otherwise chips flash for 0.5 s);
  - region boundary in the silence after the closing sentence: frames [n0, n1), audio samples n*SR/FPS.
- Render: `render/render_region.sh Rxx n0 n1 4` (4 Playwright workers, H.264 chunks, concat -c copy, one audio slice muxed).
  Speed seen: 6-13 min per region on 4 workers (older box: 0.7-1.2 s/frame).
- QA per region (`tools/qa_region.py`): part seams vs direct render (PSNR > 33 dB = only compression), previous region last vs
  this first frame, audio lag 0 vs the timeline WAV, no clicks at edges; contact sheet every 2 s and read it. A big pixel change at a
  boundary is fine only if the direct render shows the same change between neighbours (camera mid-flight).
- After R01: one review page (light 960x540 preview <= 15 MB, key frames, what was checked, one question), then wait.
- Re-render only the chunk you changed: split the affected part into sub-chunks, concat with the untouched parts, re-run QA.
  Before that, diff the old and new episode.js for stops/shots with t inside the rendered regions; they must be identical.

## Stage 6. Music and assembly
- Video: concat demuxer -c copy of `export/Rxx/video_silent.mp4`; check packets equal the region clips and the expected frame count.
- Voice: concat `voice_Rxx.wav` (must equal the timeline WAV bit for bit). Kokoro output is peaky (-24 LUFS, 0 dBFS peaks):
  `aresample=48000:resampler=soxr,volume=8dB,acompressor=threshold=0.126:ratio=2.5:attack=5:release=120,volume=6dB,`
  `alimiter=limit=0.84:attack=5:release=60:level=disabled:latency=1` -> -16 LUFS mono. Without `latency=1` the limiter delays voice 5 ms.
- Music bed (`mix_music.py`): -24 dBFS RMS in pauses, -11 dB under speech (attack 0.25 s, release 0.9 s), fades 2/3 s -> bed ~19 dB
  under the voice. Narration fills ~94% of the time, so the bed is mostly ducked.
- Final AAC: put `volume=-0.8dB,alimiter=limit=0.63:...:latency=1` before the encoder; native AAC overshot to +1.9 dBFS without it.
  Target -14 LUFS integrated, true peak <= -1 dBTP (dual-mono stereo reads ~3 dB louder than the mono voice).
- QC: full decode, frames, black frames, lag 0, seams sheet (n-30, n-1, n, n+29), seams in real silence, `final_qc.json`.
- Code-synth bed recipe (`synth_music.py`): 100 BPM, Am-F-C-G one chord per bar, pad + plucked arpeggio + bass + soft drums +
  bell motif on B sections, drum-free breath every 32 bars, simple FFT convolution reverb, deterministic seed. Nobody can hear it
  from the sandbox: ask the user to listen.

## Stage 7. Packaging
- Thumbnail 1280x720 in HTML/SVG from the donor layout: headline, 3 countries (happy green / sad orange / angry red) with real
  Natural Earth outlines, flags, glow, faces, 3 status pills, CTA pill. Replace only the meaning; remove donor logos and duration.
  Use only verified registry countries; drop tiny far islands (`minArea`). Compare with the donor at full size and at 320 px.
- Title verbatim. Description: 2 lines of what the viewer learns, coverage, how statuses were measured, cut-off date, final totals,
  chapters from real region boundaries (ceil to the next second, first 0:00, each >= 10 s), 4-6 official sources, map and music
  attribution, one subscribe line, one comment question. Full source list in `pinned_comment.txt`.
- Tags <= 500 chars, 3 hashtags. Page with copy buttons. Remind the user to re-check fast-changing facts before upload.

## Artifact and environment gotchas
- Publish pages from a scratchpad copy with `root` + `files`; .m4a is not served (use .mp3); pages <= 15 MB per media file.
- `/mnt/project-files` is a slow network mount: render and encode in the scratchpad, copy results at the end.
- Background jobs over 2 h: chain regions in one nohup loop and wait with a separate poll command.
