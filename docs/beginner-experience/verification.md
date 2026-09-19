# Beginner experience — verification

## P0 reconciliation (2026-09-18)

Prior P1–P9 “PASS” lines below are historical CLI runs. They are not native UI, audio, or live-model evidence. The SUNROOM.app binary dated 2026-09-17 cannot verify `f6b5edb`.

| Check | Status | Evidence |
|---|---|---|
| P5 vacuous `or True` | repaired | dump must contain one Session Pulse (96 notes, extra pitches and a 0.5-beat hat) and one Arrangement Pulse (8 kick notes); Pad stays arrangement-only |
| P5 rerun | passed | `python3 scripts/verify_beginner_p5.py` on CLI sha256 `95c0f512…866b7` |
| Prior P5 artifacts | preserved | `artifacts/provenance/beginner-p5-before-p0-20260918T141634.tar.gz` |
| Native launch / screenshot / audio device | **not run** | app binary predates HEAD |
| Full P1–P9 suite | **not rerun** | only P5 was refreshed after the assertion change |
| Aikido scan | **not run** | plugin requires sign-in |
| P2 recipe truth | passed headless | `python3 scripts/verify_beginner_p3.py` on CLI sha256 `497a5532…0240`: summary says feeling, home note, and pace were not applied; dump tempo 100.0, keyRoot 9. GUI labels not in the 2026-09-17 app. |
| P2 clip view | passed headless | same script rerun on CLI sha256 `9b002d00…7526`: three Fixture A clips, view `arrangement`, zero session clips, log says "not Session". App still not relinked. |
| Session launch command | none | `magda_cli` usage has no launch command. Engine is created with `headless = true`, which skips `SessionClipScheduler`. |
| P2 stored levels and master render | passed headless | `python3 scripts/verify_beginner_p2.py` on CLI sha256 `4f5e4a58…217b`: drums/bass/chords volumes 0.55/0.45/0.35; `artifacts/beginner-p2/02-master.wav` is 2 seconds and not silent. Not per-track audio. Not device playback. |
| P9 shelf preview | passed headless | `python3 scripts/verify_beginner_p9.py` on CLI sha256 `a9d045ff…8467`: `preview-sample` does not add Heartbeat 01; `add-sample` still does. GUI player not started. |
| P6 guided mixer rows | passed headless | `python3 scripts/verify_beginner_p6.py` on CLI sha256 `4424a2b9…4044`: stored sends/spectrum/routing 1, presented 0, config file unchanged. App not relinked. Analyze not run. |
| P4 Drum Grid preference | passed headless | `python3 scripts/verify_beginner_p4.py` on CLI sha256 `d455812f…9653`: Drums `editor drum-grid identifier drumgrid`; Bass and Chords `editor piano-roll`. Panel not opened. |
| P4 Chord Engine on Chords | passed headless | `python3 scripts/verify_beginner_p4.py` and `verify_beginner_p2.py` on CLI sha256 `f3b7a74e…2b26`: Chords devices `midichordengine` then `magda_polysynth`. Bass has no Chord Engine. Master peak still not silent. Panel not opened. |
| P4 Sampler on Sound | passed headless | `python3 scripts/verify_beginner_p4.py` and `verify_beginner_p2.py` on CLI sha256 `3a69edc2…d3a3`: Sound device `magdasampler` with `Glass mote 01.wav` in plugin state. Bass stays `magda_polysynth`. Panel not opened. Live plugin file not queried. |
| P4 keyboard vs text | passed headless | `python3 scripts/verify_beginner_p4.py` on CLI sha256 `82a7b656…c13e`: text editor, its child, and an editable label yield; fixed label, plain component, and no focus do not. No key pressed. |
| P4 scale lock | passed headless | `python3 scripts/verify_beginner_p4.py` on CLI sha256 `25f898e1…3f3a`: pitched `10 -> 11`; drum-grid, lock-off, and no-guide stay `10`. Drum Grid editor source does not call `snapToScale`. No note drawn. |
| P4 held-note release | passed headless | `python3 scripts/verify_beginner_p4.py` on CLI sha256 `8352a261…a13e`: typing, outside, and no focus release held 0; inside and no-window keep held 2. No MIDI note-off sent. |
| P5 Capture vs Place | passed headless | `python3 scripts/verify_beginner_p5.py` on CLI sha256 `e51b898c…1035`: launch time 1.5 kept, otherwise transport 3.5. Headless recorder not constructed. Place Scene still copies. No jam recorded. |
| P5 Place Scene default | passed headless | `python3 scripts/verify_beginner_p5.py` on CLI sha256 `4f9ef651…88dd`: scene 0; loop 100 and 128 stay at beat 128; loop 160 goes to beat 160. No picker. Button not clicked. |
| P5 Return to Arrangement | passed headless | `python3 scripts/verify_beginner_p5.py` on CLI sha256 `5227997b…1293`: active clip is Session playback; cleared clip is Arrangement. Headless scheduler absent. Deactivate called. No clip stopped. View not switched. |
| P5 playback source | passed headless | `python3 scripts/verify_beginner_p5.py` on CLI sha256 `107c1788…93f3`: empty and aux say none; audio plus aux says Arrangement; session plus arrangement says mixed. Not shown on screen. |
| P6 Analyze findings | passed headless | `python3 scripts/verify_beginner_p6.py` on CLI sha256 `53cbc75e…663f`: levels, peak, and one collision; `has-score no`. Button opens the offline modal in source. Modal not opened. Measurement not run. |
| P7 remote pulse undo | passed headless | `python3 scripts/verify_beginner_p7.py` on CLI sha256 `779966f5…0d6e`: tempo 90.0 then `Undid: Set project tempo`; signature 7/8 then `Undid: Set time signature`, restored to the saved 4/4. Same run also staged automation: points 0 until apply. No model loaded. Point writes are not an undo step. |
| P7 applied clip id | passed headless | `python3 scripts/verify_beginner_p7.py` on CLI sha256 `c295cbb1…fb6e`: staged note printed `clips 0` before `Applied:`, then `clip 1`. No model loaded. Chat panel not opened. Point writes are not an undo step. |
| P7 automation curve undo | passed headless | `python3 scripts/verify_beginner_p7.py` on CLI sha256 `cec2d3ca…0e94`: staged line `points 0` before `Applied: Wrote 2 points`, then `Undid: Apply suggestion` and `points 0`. No model loaded. Lane clear is still not an undo step. |
| P7 suggestion undo name | passed headless | `python3 scripts/verify_beginner_p7.py` on CLI sha256 `1e9ba87d…0aa2`: `Undid: Apply suggestion 2: track volume` then `Undid: Apply suggestion 1: project.set(bpm=90)`. No model loaded. Hear before was not clicked. |
| P7 suggestion delta | passed headless | `python3 scripts/verify_beginner_p7.py` on CLI sha256 `2c923d78…430e`: `delta tempo 84.0 -> 90.0` and `delta points 0 -> 2`. No model loaded. Hear before was not clicked. Lane clear is still not an undo step. |
| P7 automation clear undo | passed headless | `python3 scripts/verify_beginner_p7.py` on CLI sha256 `5c82d754…e893`: clear apply printed `Cleared lane.` and `delta points 2 -> 0`, then `Undid: Apply suggestion 2: clear track volume` restored `points 2`. No model loaded. |
| P7 conductor views | passed headless | `python3 scripts/verify_beginner_p7.py` on CLI sha256 `4eec3346…94f8`: same `conversation` and `proposal-id` through create/session/arrange/mix; `new-project` printed `proposal no`. No model loaded. Views not opened. |
| P7 settings-only recipe | passed headless | `python3 scripts/verify_beginner_p7.py` on CLI sha256 `4b27c01e…584f`: explanation then settings apply printed `Settings applied. No tracks were created.`, `tracks 0`, blank tempo unchanged. No model loaded. |
| P7 model reply prevalidate | passed headless | `python3 scripts/verify_beginner_p7.py` on CLI sha256 `84731488…9e6a`: `system("echo hi")` printed `Refused: shell or code` and `proposal no`; missing filter name and `track(id=99)` refused; blank dump unchanged. No model loaded. |
| P7 range device asset | passed headless | `python3 scripts/verify_beginner_p7.py` on CLI sha256 `54a12ed2…7e03`: `bpm=2000` printed `supported range`; `NotADevice` printed `device is not supported` with no Lead track; `GhostTake.wav` printed `sound was not found` with no Sound track. No model loaded. |
| P7 multi-action prevalidate | passed headless | `python3 scripts/verify_beginner_p7.py` on CLI sha256 `e4947743…eba3`: two `SUNROOM_DSL` lines with `bpm=90` then `NotADevice` printed `device is not supported`, tempo unchanged, no Lead; a prose second step printed `one step is not a song action`. P8 still PASS. No model loaded. |
| P7 late canceled apply | passed headless | `python3 scripts/verify_beginner_p7.py` on CLI sha256 `bd478a0e…e937`: late request 1 after request 2 refused; canceled arrive refused; save-as then apply refused; rename and delete of Ghost refused. No model loaded. |
| P8 live local coach | passed headless | `python3 scripts/verify_beginner_p8.py` on CLI sha256 `16da207e…e51f`: isolated profile not installed; live `this-mac-mlx` Qwen3.5-4B-4bit 63.98s explained drums notes 24/25/26; cancel refused staging. No `sk-`. GUI A/B not run. |
| P10 export song | passed headless | `python3 scripts/verify_beginner_p10.py` on the same CLI: empty refused; Fixture B preview 76.80s; Fixture C stereo 44100 WAV not silent; overwrite/cancel/unwritable. Dialog not opened. |

## P9 curated media gate (ran 2026-09-18)

Command:

```bash
python3 scripts/verify_beginner_p9.py
```

| Scenario | Status | Evidence |
|---|---|---|
| Kind filter | pass | kick returns 8 Heartbeat files, declared-no, bpm unknown |
| Combined filters / empty text | pass | kick+horizon and text zzz return 0 with zero unknown counts |
| Key filter | pass | unpitched skipped 40; pitched bells unknown-key 8; no guessed key |
| BPM filter | pass | unknown-bpm 48; no match invented |
| Missing / escaped import | pass | refused; nothing added |
| Import, reopen, undo, redo | pass | Heartbeat 01 track; source WAV still on disk |
| Audition / GUI | **not run** | shelf click still imports; no separate preview player |
| Time-stretch | not applied | query and import say so |

Evidence: `artifacts/beginner-p9/result.json`

## P10 export gate (ran 2026-09-19)

Command:

```bash
python3 scripts/verify_beginner_p10.py
```

| Scenario | Status | Evidence |
|---|---|---|
| Empty arrangement | pass | `Refused: the arrangement is empty`; `empty.wav` not created |
| Fixture B duration | pass | preview `duration 76.80s` at 100 BPM; file not written |
| Fixture C Arrangement export | pass | stereo 44100 WAV, duration 18.5–20.5s, peak above silence |
| Overwrite | pass | existing bytes kept without `--overwrite`; RIFF after `--overwrite` |
| Cancel | pass | destination bytes unchanged; no leftover `.part` |
| Unwritable dest | pass | file-as-folder path refused |
| GUI dialog / Reveal / Open | **not run** | CLI printed `reveal <path>` only |

Evidence: `artifacts/beginner-p10/result.json`

## P8 coach gate (refreshed 2026-09-19)

Command:

```bash
python3 scripts/verify_beginner_p8.py
```

| Scenario | Status | Evidence |
|---|---|---|
| Missing local model | pass | isolated `MAGDA_DATA_DIR` says "not installed" and "not an AI answer"; no `sk-` |
| Prose without SUNROOM_DSL | pass | refused; no save |
| SUNROOM_DSL then apply-proposal | pass | real interpreter; Applied |
| Live files present | pass | copied `sunroom-ai.json`; `mlx-community/Qwen3.5-4B-4bit` revision `0e7ffd5c…` |
| Live local ask | pass | provider `this-mac-mlx`; latency 63.98s; named Fixture A / Drums notes 24/25/26; `Coach answered. Music is unchanged.` |
| Live cancel | pass | host printed `Refused: coach result canceled`; no proposal staged |
| Cloud / LAN | **not run** | no key entered; no mini PC |
| GUI audible before/after | **not run** | Hear before/after is undo/redo of "Apply suggestion" only |

Evidence: `artifacts/beginner-p8/result.json` and `08-live-ask.log`. The model also invented a **Fix** button that does not exist; that is model wording, not a product control.

## P7 staged DSL gate (ran 2026-09-17)

Command:

```bash
python3 scripts/verify_beginner_p7.py
```

| Scenario | Status | Evidence |
|---|---|---|
| Mock DSL groups tracks via real interpreter | pass | Applied; dump has All Tracks |
| One undo removes that group only | pass | same process; Drums remain |
| Invalid DSL | pass | Refused; no save |
| Stale revision | pass | bump-revision then refuse; no rollback |
| Selection change | pass | not retargeted |
| Cancel / second apply | pass | no duplicate save |
| Live model | **not run** | P8 |
| Console auto-apply | **unchanged** | still immediate |

Evidence: `artifacts/beginner-p7/result.json`

## Fixtures

- **Fixture A:** 8 bars @ 100 BPM 4/4, A natural minor; drums / bass / chords.
- **Fixture B:** 32-bar intro/main/variation/ending from A.
- **Fixture C:** distinct Session vs Arrangement playback sources.

## P6 Progressive Mix gate (ran 2026-09-17)

Command:

```bash
python3 scripts/verify_beginner_p6.py
```

| Scenario | Status | Evidence |
|---|---|---|
| Shared Space creates one Aux + magda_reverb | pass | dump devices on Shared Space |
| Starter tracks send at requested amount | pass | ≥3 sends @ 0.4 |
| Second apply reuses same Aux | pass | still one aux track |
| Undo removes created return | pass | space-return then undo in one exec |
| Open Mix | **code path** | `onShowMix` → `ViewMode::Mix` |
| Analyze reachable | **code path** | existing MixerToggleRail |
| GUI audible level/pan/FX | **not run** | Xcode license / app relink |

Evidence: `artifacts/beginner-p6/result.json`

## P5 Session→Arrangement gate (ran 2026-09-17)

Command:

```bash
python3 scripts/verify_beginner_p5.py
```

| Scenario | Status | Evidence |
|---|---|---|
| Fixture B 32-bar loop + section markers | pass | loopEndBeats ≥ 128; markers in .mgd |
| Place Scene empty range / occupied refuse | pass | Deterministic place; overwrite message |
| Fixture C dual sources | pass (refreshed 2026-09-18) | dump views and note counts; the old `or True` log check is gone |
| Capture Jam / Return / badges | **code path** | SessionRecorder / deactivateAllSessionClips / TrackPlaybackMode |
| GUI audible mixed Session+Arrangement | **not run** | Xcode license / app relink |

Evidence: `artifacts/beginner-p5/result.json`

## Earlier phases

P0–P4 evidence under `artifacts/beginner-p{0..4}/` and prior `verification.md` history.

## Manual GUI script (when unblocked)

1. Create and Play → Open Mix → faders / mute / solo; Analyze on mixer rail.
2. Shared Space with Space slider; confirm one Aux; undo.
3. Expand sends on mixer rail; confirm Shared Space send; collapse again.
