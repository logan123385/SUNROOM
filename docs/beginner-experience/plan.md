# Beginner experience — adapted phase plan

Adapted from `Magda_Cursor_Auto_Implementation_Plan.md` to this SUNROOM/MAGDA checkout.

## Current phase status

Reconciled 2026-09-18 against `f6b5edb`. Older “complete” labels are historical implementation checkpoints, not acceptance. **partial** means some of the phase exists; it is not accepted while a required gate is pending.

| Phase | Implementation | Headless verification | Native UI/audio | Model |
|---|---|---|---|---|
| P0 Inventory | partial — tracker refreshed; `build.ninja` still needs a CMake re-run before the next ninja build | passed — P5 assertion repaired and rerun on the current CLI | not run | n/a |
| P1 History / recovery | partial — missing media and failed recovery leave the last save; native recovery dialog not run | passed 2026-09-18 (`verify_beginner_p1.py`, including steps 09–10) | not run | n/a |
| P2 Starter recipes | partial — stored fader levels and a non-silent master render are proven; per-layer audio and Session playback are not | passed 2026-09-18 (`verify_beginner_p2.py`: volumes 0.55/0.45/0.35, 2s master WAV peak above silence) | not run | n/a |
| P3 First session | partial — Beat/Song/Blank descriptions are in source; Session launch is not available headless | passed 2026-09-18 (`verify_beginner_p3.py`) | not run — tooltips and Arrange routing are source-only | n/a |
| P4 Instruments / notes | partial — typing, leaving the window, or losing focus releases held keyboard notes; a control still inside the window keeps them | passed 2026-09-18 (`verify_beginner_p4.py`) | not run | n/a |
| P5 Sections / ownership | partial — playback source counts only playable tracks. Empty projects and aux returns do not claim Arrangement | passed 2026-09-18 (`verify_beginner_p5.py`) | not run | n/a |
| P6 Mix / Shared Space | partial — Analyze opens an offline measurement modal; findings are levels and collisions, not a score. The measurement itself was not run | passed 2026-09-18 (`verify_beginner_p6.py`, including findings text) | not run — button and modal not opened | n/a |
| P7 Proposal boundary | partial — console agent DSL, music IR, and automation IR stage until apply. Point writes are not an undo step | passed 2026-09-18 (`verify_beginner_p7.py`) | not run | not run — mocks only |
| P8 Live coach | partial — missing-model refusal and DSL staging exist | passed 2026-09-17 (`verify_beginner_p8.py`) | not run | not run — weights not loaded |
| P9 Curated media | partial — shelf click previews through the sample browser in source; Shift-click still imports. Heard playback not proven | passed 2026-09-18 (`verify_beginner_p9.py`, including preview-sample leaving the project unchanged) | not run | n/a |
| P10 Export | not started under this plan | not run | not run | n/a |
| P11 Native journey | not started | not run | not run | not run |
| P12 Handoff | not started | not run | not run | not run |

**Next slice:** The chat panel still reads the generated clip id from execute, which no longer creates the clip. See whether apply can record that clip id. Do not start P10. Do not load a model.

## Architecture reuse (non-negotiable)

- Same project entities for guided + Full studio (`TrackManager`, `ClipManager`, `UndoManager`).
- No parallel beginner project model; no audio-callback I/O or inference.
- Chord Track ≠ Chord Engine; Drum Grid is a device, not a new sequencer rewrite.
- AI mutations must go through validated DSL/command path (P7 before claiming coach apply).

## SUNROOM overlap

Prior SUNROOM work already delivers a guided Create path, 8-bar default, coach, and offline journey generation. P2–P3 must **reconcile** Magda Fixture A (drums/bass/chords @ 100 BPM) with SUNROOM moods without inventing a fourth composition model. Prefer additive entry (Beat/Song/Blank) that can call either recipe pipeline once both exist.
