ENGINE TEMPLATE (copied 2026-11-04 from countries-love-hate-usa/stage5 + stage6)

Files
  index.html                  canvas engine, every pixel = drawFrame(t); reads data/world.js + data/episode.js
  data/world.js               Natural Earth geometry (universal)
  data/prep_world.mjs         builds world.js (universal)
  data/episode_example_love_hate.js   example episode, NOT for this video; real episode.js is generated at stage 5
  render/render.js            headless Playwright render: chunk / video / frames / checkpoint / tech
  render/render_region.sh     one region = frames [N0,N1) in 4 workers + one audio slice
  tools/align.py              script words vs ASR words (Parakeet + Whisper)
  tools/audio_edit.py         silence inserts (flight pauses), keeps a sample map
  tools/build_episode.py      countries/scenes + WAV timestamps -> data/episode.js (region plan lives here)
  tools/qa_region.py          per-region QA sheet
  stage6_tools/inventory.py, qc_final.py, mix_music.py   final assembly, QC, ONE music bed under voice
  assets/flags/ (157 SVG), assets/fonts/ (Lilita One, Nunito)

Universal (reuse as is)
  map, camera fly/zoom, flag fill of a country, faces + blinks, clouds, name tag, bottom card,
  right-hand "recent" list, route progress bar, render pipeline, region checkpoints, QA, assembly.

Topic-dependent (must change for "migration desire")
  1) E.statuses: 6 relation statuses -> value BANDS of the chosen metric (e.g. PNMI: big gain / gain / balanced / loss / big loss),
     colours as a diverging scale (green in, red out) instead of alliance colours.
  2) HUD top-left: 6 status counters -> band legend with counts, or "WANT IN vs WANT OUT" two counters.
  3) Status icons (shield, handshake, bolt, swords...) -> arrows in / arrows out / balance icon.
  4) Bottom card pill "TREATY ALLY · NATO 1949" -> the number itself ("+225% WANT IN", "-24% WANT OUT") + data years.
  5) Poll chip event (ev.kind 'poll') -> reuse as the number chip; pollColor() thresholds -> band thresholds.
  6) Face emotion: relation-based -> value-based (happy when people want in, sad/sweating when people want out).
  7) theme_heart_love_hate.png (intro emblem with US flag) -> new emblem (suitcase / door / plane); assets/ not copied on purpose.
  8) E.subject (US flag fill) -> not needed, there is no single subject country.
  9) Outro: scoreboard + alliance/poll mini maps -> top 5 "want in" vs top 5 "want out" + one full value map.
