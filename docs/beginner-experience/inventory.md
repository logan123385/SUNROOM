# Beginner experience — repository inventory (P0)

**Repo:** SUNROOM fork of MAGDA (`logan123385/magda-core`, branch `codex/sunroom`)  
**Baseline revision:** `f6b5edb` (2026-09-18), merged to `main` as `90bacab` via PR #1  
**Date:** 2026-09-18  
**Method:** git/build inspection + one refreshed headless script. Native app launch **not run**.

### Build provenance (this reconciliation)

| Item | Value |
|---|---|
| Branch | `codex/sunroom`, tracking `origin/codex/sunroom` |
| HEAD | `f6b5edb26712ba1d82b4e6bfb68336b5bb951eb4` |
| Dirty tracked files | `scripts/verify_beginner_p5.py` (assertion fix, not yet committed); `third_party/tracktion_engine` working tree dirty, pointer still `f7a2eb9` |
| Untracked, not part of the product | `CURSOR_GROK_4_6_HANDOFF.md`, `docs/beginner-experience/SUNROOM_Cursor_Auto_*.md`, `tmp/` |
| Generator | Ninja, `CMAKE_BUILD_TYPE=Release`, `CMAKE_CXX_COMPILER=/usr/bin/c++` |
| Compiler check | `/usr/bin/c++ --version` returned Apple clang 21.0.0. The earlier licence block is not currently reproducing. |
| Ninja | `ninja -C build-sunroom -n magda_cli` warned `premature end of file; recovering` and would re-run CMake. No configure or compile was started. |
| CLI used for the P5 rerun | `build-sunroom/magda/daw/magda_cli_artefacts/Release/magda_cli` |
| CLI identity at P5 | mtime 2026-09-18 13:57:26, sha256 `95c0f512235b7c914b15d530b2fbd0d08c21d1dcbf6fb620a175c15e681866b7` |
| CLI identity after P1 slice | mtime 2026-09-18 14:22:43, sha256 `f8247c2d92482ab85ee42ae6bab12787499684e068d04f66e709bf02e25f5f39`. Manual clang++ link, not a ninja stamp. |
| CLI identity after P8/P10 | mtime 2026-09-19 01:43:53, sha256 `16da207e6203fdbc5ed2763e116426928e9fa5aca4f749b5b2abaf5ee103e51f`. Manual clang++ link, not a ninja stamp. |
| CLI vs source | Linked after the P8/P10 C++ edits. It can verify those CLI paths. It is not a ninja stamp of HEAD. |
| App | `build-sunroom/magda/daw/magda_daw_app_artefacts/Release/SUNROOM.app/Contents/MacOS/SUNROOM`, mtime 2026-09-17 20:59:08. Older than `f6b5edb`. Cannot verify current source. |

Source scope: `Magda_DAW_Beginner_Feature_Gaps.pdf` (M1–M5, S1–S6). Execution: `Magda_Cursor_Auto_Implementation_Plan.md`, `Magda_Cursor_Auto_Phase_Prompts.md`.

---

## Capability status (M/S map)

| ID | Requirement | Status | Evidence / notes |
|---|---|---|---|
| M1 | Guided first session | **needs extension** | `SunroomStudio` is default guided overlay (`MainWindow` `guidedStudio_ = true`). Feeling → Build → Play path exists; Beat/Song/Blank welcome picker and Fixture A drum/bass/chords starter **missing**. |
| M2 | Auditable agent coach | **present, needs native A/B** | P7 staging/apply/undo plus live local `coach-ask` (P8). Heard before/after and native coach UI are still pending. |
| M3 | Session → Arrangement | **working/reusable** | `SessionView`, `MainView` (arrange), `SessionClipScheduler`, `TrackPlaybackMode`, `SessionRecorder`. Beginner Capture Jam / source badges need wiring (P5). |
| M4 | Beginner instruments | **working/reusable** | Guided Make a Beat / Add Chords / Play a Sound open Fixture A Drum Grid / Chords / Bass (P4). Chord Track ≠ Chord Engine. |
| M5 | Progressive Mix | **needs extension** | `MixerView` exists; guided collapsed presentation + shared spatial return macros not productized (P6). |
| S1 | Curated packs / filters | **needs extension** | Media DB + SUNROOM Sounds exist; curated packs + key/BPM filter UX incomplete (P9). |
| S2 | Scene / section templates | **needs extension** | Session scenes exist; Beat/Song/Blank landed (P3); intro/main/variation/ending templates incomplete (P5). |
| S3 | Simple piano roll | **working/reusable** | Scale lock + fold-as-simple for guided projects (P4); shares clip data with advanced view. |
| S4 | Export, autosave, undo | **working/reusable** | CLI `export-song` is Arrangement-only with empty/cancel/overwrite gates (P10). GUI dialog and Reveal were not opened. |
| S5 | QWERTY + simple FX | **needs extension** | QWERTY text-focus skip + focus-loss flush (P4); shared spatial return macros still P6. |
| S6 | Graduation coach / conductor | **present, needs native proof** | Conductor views and live local coach exist in CLI. Native conversation and heard A/B are pending. |

Nice items N1–N6: **deferred**.

---

## System map (real symbols)

### Guided / first-run
- `magda/daw/sunroom/SunroomStudio.{hpp,cpp}` — Create / Note garden / Sound shelf / AI companion
- `magda/daw/sunroom/SunroomActions.{hpp,cpp}` — `CreateJourneyCommand`, `AddMelodyCommand`, …
- `magda/daw/sunroom/MusicTheory.hpp` — moods, compose, Options (default 8 bars)
- `magda/daw/ui/dialogs/SplashScreen.*`, `ProjectManager::newProject()`

### Session / Arrangement / Mix
- `magda/daw/ui/views/SessionView.*`
- `magda/daw/ui/views/MainView.*` (arrangement; `ArrangementView` is not the live UI)
- `magda/daw/ui/views/MixerView.*`
- `magda/daw/core/ViewModeController.hpp` — `ViewMode::{Live,Arrange,Mix,Master}`

### Tracks / clips / transport arbitration
- `magda/daw/core/TrackManager.*`, `TrackInfo.hpp` (`TrackPlaybackMode::{Arrangement,Session}`)
- `magda/daw/core/ClipManager.*`, `ClipInfo.hpp`, `ClipTypes.hpp`
- `magda/daw/audio/session/SessionClipScheduler.*` — sync modes / revert to arrangement
- `magda/daw/audio/session/SessionRecorder.*` — session→arrangement capture

### Commands / persistence
- `magda/daw/core/UndoManager.*` — `UndoableCommand`, `CompoundCommand`
- `magda/daw/project/ProjectManager.*` — save/load/autosave/recovery prompt
- `magda/daw/project/serialization/ProjectSerializer.*`

### Devices / music tools
- Drum Grid: `magda/daw/audio/plugins/DrumGridPlugin.*`, `DrumGridUI`
- Chord Engine: `magda/daw/music/ChordEngine.*`, `MidiChordEnginePlugin`
- Chord Track: `TrackType::Chord`, `TrackManager::ensureChordTrack()`

### Export / media / agents / models
- Export: `MainWindowExport.cpp`, `OfflineRenderHelper.*`, CLI render
- Media: `MediaExplorerContent`, `MediaDbBrowserContent`, `paths::dataDir()`
- DSL: `magda/agents/dsl_interpreter.*`, `ConsoleAgentOrchestrator`
- Models: `llama_model_manager`, `sunroom_mlx_client` (MLX / LAN / Luna)

---

## Baseline commands (this environment)

| Check | Result |
|---|---|
| `./build-sunroom/tests/sunroom_theory_test` | **PASS** — 144 arrangements, 43728 notes |
| `python3 tests/sunroom/test_mlx_boundary.py` | **PASS** — 7 tests |
| `python3 scripts/verify_sunroom_native.py --cli …/magda_cli` | **PASS** — 7 tracks, 14 clips, 97 notes; peak −12.6 dBFS |
| Launch `SUNROOM.app` | **not run** — Xcode license / host GUI gate |
| `magda_tests` / `magda_juce_tests` full suite | **not run** — long rebuild; license risk |
| Live Luna / mini-PC | **not run** — needs owner key/server |

Build tree: `build-sunroom` (Ninja Release). Targets: `magda_daw_app`, `magda_cli`.

---

## Next required proof

The 2026-09-17 journey insert → undo → redo → save → reopen path still stands as **headless evidence only** (`scripts/verify_beginner_p1.py`). It does not accept P1. Missing-media and recovery-write checks in that script passed on 2026-09-18 and still do not accept native recovery.

**Next required proof:** a model reply is still not checked for shell, code, or a missing target before apply. Native autosave prompt remains not run.

**Proven this slice:** `coach-explain` is kind explanation with no proposal. `settings-recipe` applies Create settings only (`settings-tempo 96.0`) and prints `Settings applied. No tracks were created.` The saved project tempo and track names match the blank. No model was loaded. The installed app was not relinked.

**Touchpoints:**
1. `UndoManager::executeCommand` + `CompoundCommand` (or existing `CreateJourneyCommand` group)
2. `ProjectManager::saveProject` / load + dirty tracking
3. Failure seam: mid-command abort leaves prior project intact
4. Verification: `scripts/verify_beginner_p1.py` (dump-json musical fingerprint)

Do **not** build Beat/Song/Blank welcome UI in P1.
