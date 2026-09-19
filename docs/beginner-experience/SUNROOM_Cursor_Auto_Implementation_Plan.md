# SUNROOM: Cursor Auto implementation plan

Prepared 18 September 2026 from `Magda_DAW_Beginner_Feature_Gaps.pdf` and the current SUNROOM source.

**Purpose:** finish the report's beginner features in this existing native MAGDA fork. Reuse the work already present, repair demonstrated gaps, and verify the complete music-making experience. This document is an implementation handoff; preparing it did not implement or retest the application.

**Repository:** `/Users/loganchambers/Documents/ChatGPT/ai daw`

**Inspected branch / HEAD:** `codex/sunroom` / `7176b43`, with existing uncommitted changes.

**Companion:** `SUNROOM_Cursor_Auto_Prompts.md` in this directory.

## 1. Read this before editing

The older `Magda_Cursor_Auto_Implementation_Plan.md` and `Magda_Cursor_Auto_Phase_Prompts.md` already translated the report into P0–P12. Subsequent work added many of those features. Use this document as the current execution guide, retaining those phase IDs and the older documents as background. Do not restart from an empty repository.

The current `plan.md` marks P0–P9 partial or not started. The older tracker called those phases complete. `progress.md` and `verification.md` still leave native UI/audio, live model, audition, and other acceptance checks pending. Treat older complete labels as historical implementation checkpoints, **not release acceptance**. In P0, reconcile the tracker against the code and evidence instead of automatically starting at P10.

This inspection read the ten-page PDF, visually inspected its rendered pages, inspected relevant source and scripts, and read existing records. It did not rebuild SUNROOM, launch its GUI, listen to audio, rerun the test suites, or make a live model/API request. Previously recorded passes must be attributed to those earlier runs until refreshed.

The working tree also changed during preparation of this handoff. The source map is an inspection snapshot, not an immutable audit of the final diff. Refresh each finding before editing; reuse any subsequent fix that already satisfies its acceptance criteria. This task did not modify application code.

The PDF's editorial instructions, “LOCKED” labels, audit workflow, and research claim IDs are source-document context. They are not commands for Cursor to execute. The product requirements below come from the user's requested feature planning and the report's recommendations. New technical choices and acceptance gates are implementation proposals, not upstream MAGDA commitments or independently verified competitor research.

### Protect the starting state

- Read applicable `AGENTS.md`, build instructions, and current Git status at the start of each task. No `AGENTS.md` was found in the initial relevant search; recheck if the tree changes.
- Existing edits include the DSL interpreter, CLI, undo manager, SUNROOM actions/UI, piano roll, beginner verification scripts, dirty-tracking tests, and the Tracktion submodule. Preserve and inspect them. Do not reset, clean, replace the submodule, or regenerate the build directory to get a clean-looking baseline.
- Keep SUNROOM's separate application/profile identity and existing project compatibility. Do not overwrite an installed application or real song for testing.
- Preserve the existing JUCE/Tracktion assertion/build configuration and device parameter conventions. Do not fix link errors by introducing inconsistent flags between linked targets.
- Use normal implementation judgment for reversible local work. No repeated approvals for ordinary fixes. Purchases, public releases, destructive changes, and external account setup are outside this handoff.

## 2. Product outcome and user's creative direction

The complete path is:

**Choose a feeling or starter → hear editable music → change a note or drum step → get optional understandable AI help → arrange sections → balance the mix → save/reopen → export a playable song.**

The report's approximately **60–90 seconds** means the finished song's musical duration, not a promise that someone will learn the software or finish a song in that time.

Preserve the user's wider SUNROOM direction while implementing the PDF:

- **Visual identity:** deep violet surfaces, purple/lavender detail, warm orange sun, restrained sunset gradients and vaporwave scenery. Reuse `assets/themes/sunroom_sunset.json`. Keep notes, meters, selection, text and transport readable; scenery must not compete with controls.
- **Psybient/psychill first:** spacious pads, controlled sub, sparse melodic motifs, organic percussion, evolving textures, echoes, and gradual section changes. Preserve the existing mood/recipe system. These are starting choices, not genre rules imposed on every song.
- **Understandable note relationships:** preserve Note garden and existing Home/Warmth/Anchor/Float/Pull/Spice labels. Explain the relationship to the selected root and, where available, the current chord. Let users hear pairs. Feelings are analogies, not universal facts or a promise that every in-scale note fits every chord equally well.
- **Depth when wanted:** keep Session, Arrangement, Mixer, DSL details, automation, advanced device editing and plugin hosting accessible. Simple controls edit the same song as Full studio.
- **Free useful sounds:** ship a curated offline set using existing original/cleared assets and stock processors. External free plugins can be optional later; first sound must not depend on downloading or scanning them.
- **AI choices:** preserve the Mac MLX route, optional Windows mini-PC server, and API route. Use one visible coach experience and the same validated editing boundary. No paid API fallback without the user's explicit provider selection.

### Beginner presentation rules

Show one primary next action and a short explanation. Use ordinary labels such as **Make a beat**, **Choose chords**, **Play a sound**, **Arrange my song**, and **Export song**. Keep “Fixture A/B/C,” enum names, backend syntax, and internal project IDs out of product copy. Put actual DSL in expandable **What changed / Commands** details.

Use text/icon cues as well as color. Provide visible keyboard focus, a reduced-motion option if introducing motion, and an uncluttered layout at the application's supported minimum size. Decorative animation must not consume resources needed for audio.

## 3. Requirement-to-delivery map

Every Must and Strong item is required for the core. Nice items are a separate backlog.

| PDF ID | Required user-visible result | Primary phases | Evidence needed |
|---|---|---|---|
| M1 | An offline first session makes audible editable Session clips, with truthful action details | P2, P3 | Actual Create and Play, audio, edits, undo and reopen |
| M2 | Coach explains a scoped proposal, shows actual actions/deltas, applies and auditions safely | P7, P8 | Validated live local response, audible change, before/after, undo |
| M3 | Session launches become an editable arrangement; user knows what is sounding | P3, P5 | Capture/placement distinction, source indicators, Return to Arrangement |
| M4 | Drum Grid, Chord Engine and a useful Sampler entry are easy to reach | P2, P4 | Each entry opens and operates the intended real instrument |
| M5 | Faders/pan/mute/solo first; advanced Mix and Analyze stay accessible | P6 | Native mix operation, routing persistence and real analysis |
| S1 | Curated media with useful kind/key/BPM filters, audition and safe import | P2, P9 | Filter/preview/import flow, asset ownership and reopening |
| S2 | Thin Beat / Song / Blank choices and editable sections | P3, P5 | Starter identity, section behavior and correct musical duration |
| S3 | Draw, rhythmic snap and scale assistance without damaging existing notes | P4 | Shared simple/advanced data, drum exclusions and save/load |
| S4 | Reliable undo/recovery and a prominent working export | P1, P10 | Failed-operation recovery, actual decoded export |
| S5 | Discoverable QWERTY play and simple spatial FX | P4, P6 | No typing-triggered/stuck notes; one valid shared return |
| S6 | Session-to-Arrangement guidance and one conductor conversation | P5, P7, P8 | Conversation survives view changes; one coordinated project writer |

The PDF calls Chord Track, stem separation, and audio/MIDI takes/comping existing capabilities. Preserve and verify the checked-out implementations; do not budget replacement systems as missing beginner features. Chord Track is harmonic guidance. Chord Engine is a MIDI musical tool that needs a sound-producing instrument downstream.

## 4. Current source map and remaining work

Paths below are relative to the repository root. They are inspected entry points, not permission to rewrite whole files.

| Area | Reuse these files/symbols | Current evidence and gap |
|---|---|---|
| Guided shell | `magda/daw/sunroom/SunroomStudio.{hpp,cpp}`; `MainWindow.cpp` callbacks | Beat/Song/Blank, guide/full-studio navigation, Create and Play, instrument links and export callback exist. Native usability/audio pending; internal fixture names appear in product copy. |
| Musical commands | `magda/daw/sunroom/SunroomActions.{hpp,cpp}` | Journey, Fixture A/B/C, scene placement and shared return commands exist. Complete failure/identity checks and verify real audio rather than replace them. |
| Theory/visual guidance | `magda/daw/sunroom/MusicTheory.hpp`; `PianoRollGridComponent.cpp`; `PianoRollContent.cpp` | Mood scales, note feelings, pair explanation and scale snapping exist. Verify consistency with actual project/clip context and all editing routes. |
| Session/Arrange | `ui/views/SessionView.*`; `ui/views/MainView.*`; `audio/session/SessionClipScheduler.*`; `SessionRecorder.*` | Launch/capture infrastructure exists. Source summaries and Capture/Return callbacks are wired; timing and audible ownership need native proof. `MainView` is the live arrangement surface. |
| Instruments | `audio/plugins/DrumGridPlugin.*`; `MidiChordEnginePlugin.*`; `music/ChordEngine.*`; existing device UI/factories | Guided links open fixture clips. Demonstrate actual Chord Engine and Sampler operation; a chord clip or PolySynth alone does not prove M4 complete. |
| Mix | `ui/views/MixerView.*`; `ui/components/mixer/MixerToggleRail.*`; `ApplySharedSpatialReturnCommand` | Open Mix and shared Aux reverb exist. Actual faders-first experience, Analyze and heard FX remain unverified. |
| Persistence | `core/UndoManager.*`; `project/ProjectManager.*`; `project/serialization/ProjectSerializer.*` | Existing undo/autosave, mutation revision and recovery infrastructure. Earlier CLI checks passed; failure atomicity and GUI recovery still require evidence. |
| Proposal boundary | `captureDslProposal`, `applyPendingDslProposal`, `extractCoachDsl`; `magda/agents/dsl_interpreter.*` | Stages a single DSL line and checks path/revision/selection. Not evidence of a complete conductor. Proposal storage is static; A/B identifies history by the generic label “Apply suggestion.” Strengthen identity/scope and test failures. |
| Model/UI | `magda/agents/sunroom_mlx_client.*`; `resources/sunroom/mlx_server.py`; `resources/sunroom/knowledge/coach.md`; `ConsoleAgentOrchestrator` | Local/LAN/API plumbing exists. Companion history currently keeps a short last exchange; docs record no live-model P8 verification. Share context across views and align prompt capabilities with actual tools. |
| Sounds | `loadStarterCatalog`, `queryStarterCatalog`, `ImportStarterSampleCommand`; `resources/sunroom/Sounds/manifest.json` | Offline kind/key/BPM query and import exist. Current records describe unknown key/BPM throughout the starter set; guided shelf lacks a separate preview flow. Imported clips currently reference the bundled source path. |
| Media preview | `ui/panels/content/MediaExplorerContent.*`; `MediaDbBrowserContent.*` | Existing preview transport and semantic library hooks should be reused. Do not create a second preview audio engine for the shelf. |
| Export | `ui/windows/MainWindowExport.cpp`; `ui/dialogs/ExportAudioDialog.*`; `OfflineRenderHelper.*` | A real export system and guide callback already exist. Finish beginner defaults/source explanation/error handling; do not add another renderer. |
| Evidence | `scripts/verify_beginner_p1.py` … `verify_beginner_p9.py`; `tests/sunroom/`; `artifacts/beginner-p*/` | Useful CLI evidence, not native UI proof. P5 includes an unconditional `or True` assertion; replace it with an observable assertion. Establish binary/source provenance before trusting reruns. |

## 5. Architecture contracts

### Shared song and history

Use the existing TrackManager, ClipManager, device factories, ProjectManager, UndoManager, transport and serializer. No separate “beginner song” representation or audio engine. UI presentation state belongs in existing settings; musical state belongs in the project using its versioning conventions.

Use stable object identity for recipe ownership, selected targets, proposals and undo operations. Track names and section names are editable labels, not durable identity. Undo is normally session history; save/reopen must preserve music, but persistent undo across launches is not assumed or newly required.

Group one intended edit into an appropriate undo unit. Validate before mutation. Failure or cancellation must preserve earlier music, history and dirty state. Do not clear all undo history to remove a failed command. Test failure after a partial operation, not only invalid input rejected before execution.

### Real-time behavior

Keep inference, HTTP, file reads, decoding, indexing, DSL parsing and heavy analysis off the audio callback. Use existing engine queues, scheduling and parameter smoothing. Do not hold a project write lock throughout model inference. Measure performance on the actual host rather than inventing latency guarantees.

### One visible coach, one mutation boundary

Models propose; validated host actions edit. Existing specialists remain available through a conductor with shared project/conversation state. Use stable project-session identity as well as revision and target IDs; two unsaved songs can share an empty pathname.

Show proposed versus applied actions distinctly. A model reply is not a tool permission grant. Revalidate on Apply, prevent duplicate application, invalidate canceled/late responses, and never retarget a stale response to the user's new selection. Keep existing MCP grants intact and audit all agent write entry points. A deliberate manual `/dsl` command may remain a direct advanced action; model-generated changes must not bypass coordination through that console.

### Audible truth and evidence

The active tab does not define what is sounding. Labels must reflect real per-track Session/Arrangement ownership and pending launch states. Export must identify its source. A filename, nonempty project, visible button or mock response does not prove playable music or a working model.

## 6. Implementation phases

Use P0–P12 so existing scripts and records remain useful. For each phase, **verify existing behavior first, then implement only the unmet work**. Implement in dependency order. Record small completed slices; do not call an entire phase accepted while its required gates are pending.

| Phase | Depends on | Deliverable |
|---|---|---|
| P0 | Current tree | Accurate inventory, build provenance and acceptance tracker |
| P1 | P0 | Safe commands, history, persistence and recovery |
| P2 | P1 | Reusable audible offline starter recipes |
| P3 | P2 | Coherent first-session flow |
| P4 | P2, P3 | Beginner instruments, note guidance and keyboard input |
| P5 | P1–P3 | Editable song sections and reliable playback ownership |
| P6 | P1, P2 | Progressive Mix and simple FX |
| P7 | P1, inventory of agent routes | Shared conductor and safe proposal application |
| P8 | P4–P7 | Grounded live coach and provider switching |
| P9 | P1–P4 | Previewable curated sounds and durable import |
| P10 | P1, P5, P6 | Beginner export of the intended arrangement |
| P11 | P3–P10 | Complete native journey and regression evidence |
| P12 | P11 | Reviewable local delivery and honest remaining gates |

### P0 — Reconcile the implementation and establish a usable baseline

1. Record HEAD, branch, all existing modifications, submodule status, build configuration and the exact app/CLI paths. Preserve these as baseline context, not a commit of unrelated work.
2. Update `inventory.md` and `plan.md` with separate columns for implementation, headless verification, native UI/audio verification, and model verification. Use **partial**, **passed**, **failed**, and **not run** accurately.
3. Check the existing Xcode prerequisite. System Git returned an unaccepted Xcode licence message during this inspection; the build cache selects `/usr/bin/c++`, and earlier records report the same build gate. No build was attempted for this plan. If still blocked, the owner must review/accept the licence through Xcode's normal flow. Do not bypass or accept it for them. Continue useful source/docs work and keep native gates pending.
4. Reuse `build-sunroom`; perform an incremental build when possible. Record source revision plus dirty state, build time, target and binary path. An older binary can establish a historical baseline but cannot verify newly changed source.
5. Inspect each verification script before running it. Correct vacuous assertions such as P5's `or True`; do not weaken expected outcomes to get green results. Preserve prior evidence before a script overwrites its fixed artifact directory.
6. Run focused baseline checks and launch the exact rebuilt app with a disposable profile/project when available. Record screenshot, audio-device state and build identity.

**Done:** the next unmet acceptance criterion is explicit, current evidence is separated from historical claims, and baseline blockers have exact next actions. Do not jump to export solely because the old phase table says P9 is complete.

### P1 — Close command, save and recovery gaps

Reuse `UndoManager`, `ProjectManager`, existing SUNROOM commands and dirty-tracking tests.

1. Trace insert → undo → redo → save → close → reopen through real objects. Compare notes, device state, routing, tempo, meter, key and clip placement, not only track count.
2. Verify dirty state changes on musical edits and returns correctly after undo/save. Failed saves must not clear it. Recovery must preserve the last valid save and present the recovered copy honestly.
3. Inject a failure after the first successful operation in a grouped edit. Prove rollback preserves preexisting tracks, selection, musical settings and earlier undo/redo entries. Cover redo after a failed proposal so a half-applied edit cannot be resurrected.
4. Exercise missing media, unwritable destination and interrupted autosave/recovery writes in a disposable project. Never corrupt a real song as a test.
5. Investigate the existing CLI `std::_Exit(0)` teardown workaround separately. A durable save before forced process exit is not proof of normal shutdown. Reproduce and fix the lifecycle problem if possible; otherwise retain an explicit unresolved shutdown gate rather than silently treating it as solved.

**Done:** data survives normal edit/reopen/recovery paths and failed edits preserve the earlier song/history. Native recovery and normal shutdown have actual results or remain visibly pending.

### P2 — Finish offline starter recipes and useful psybient content

Reuse `CreateFixtureACommand`, `CreateJourneyCommand`, `MusicTheory.hpp`, stock device factories and the current sound manifest.

1. Keep the deterministic test reference: eight bars, 4/4, A natural minor, 100 BPM, drums/bass/chords. Preserve the real Drum Grid pad mapping; do not assume General MIDI note numbers.
2. Reconcile the generic beginner starter with SUNROOM's mood-based journey. Give both a coherent recipe entry path and stable recipe/version/seed identity. Do not maintain separate persistence or editing systems.
3. Make mood/root/tempo controls truthful: the selected recipe must use them, or clearly state that a fixed starter uses its own settings. Avoid a displayed Dorian/84 BPM selection silently producing a fixed A-minor/100 BPM song.
4. Supply an immediately audible eight-bar psybient option with a pulse, bass, pad/chord and sparse motif; make denser percussion/textures optional. Preserve the existing longer evolving journey. Do not force a long quiet intro on the first listen.
5. Preflight all required devices/samples. Handle missing resources without a partial starter. Trigger playback only after the music and devices are ready.
6. Give each recipe actual editable Session clips. Show a factual summary of committed tracks, timing and harmony. Expose real executed DSL where supported; if starter actions are host commands, label their actual command trace honestly and add only the narrow DSL support needed by the report. Never display invented replayable syntax.
7. Maintain an asset manifest with source, creator, licence/attribution, and distribution evidence. Reuse original/cleared content; “free download” alone is not redistribution evidence. Keep first playback independent of external plugins.

**Done:** offline creation is audible, editable, undoable and reopenable; repeated pending submissions do not duplicate tracks; all intended layers sound at sensible levels. Verify per-layer output as well as the master so one loud track cannot hide silent instruments.

### P3 — Complete Beat / Song / Blank and the first minute of use

Reuse the current `SunroomStudio::createAndPlay`, starter controls and MainWindow callbacks.

1. Present Beat, Song and Blank with short descriptions; keep key/tempo/mood defaults usable without a questionnaire. Existing projects reopen normally rather than being treated as blank starters.
2. Beat creates/reuses the intended loop and opens Session. Song uses the same editable material and leads into P5 sections. Blank respects the existing unsaved-changes/cancel flow and never announces a new project before creation actually succeeds.
3. Make **Create and Play** launch the intended Session scene through the scheduler. Merely selecting the Session view and starting transport is insufficient if the audio still comes from duplicate Arrangement clips. Prove the real source.
4. Base retry/double-click prevention on operation/recipe identity. Renaming Drums/Bass/Chords or having unrelated tracks with those names must not break detection. Provide a deliberate way to add another idea without making every repeated click duplicate music.
5. Show one next edit with a direct editor link. Keep Session/Arrange/Mix/Full studio/Commands reachable, and make the guide easy to reopen.
6. Report audio-device readiness separately from project creation. A disconnected output must retain the music and offer device setup/retry; `isPlaying()` alone does not prove audible output.
7. Replace internal fixture labels and implementation language in current UI text. Keep the sunset identity across the guide and regular workspace.

**Done:** using a clean profile offline, ordinary controls produce music, an unaided edit, and a recoverable save. Measure clicks and time to first sound; do not invent a performance target before measuring.

### P4 — Finish the instrument front door and visual music guidance

Reuse Drum Grid, Chord Engine, the Sampler/device factory, Note garden and the existing piano roll. No new sequencer model.

1. **Make a beat** opens the actual Drum Grid with a loaded useful kit and editable steps. **Choose chords** exposes the actual Chord Engine and its audible downstream instrument, with a small playable starting choice. **Play a sound** offers a ready Sampler sound as well as existing synth options. A button that only selects a named MIDI clip does not satisfy these instrument requirements.
2. Keep simple note editing to draw, erase, select/move, duration, velocity, rhythmic snap and scale assistance. Provide advanced editing without copying/converting the clip or discarding expressive data.
3. Use one deterministic theory source for Note garden, piano roll colors and coach context. Display the current root/mode and note names; distinguish project harmony from a temporary recipe preview. Add current-chord context only when real harmonic data is available.
4. Keep the existing Home/orange, Anchor/lavender and other note labels consistent. Show text/icon alternatives and interval names with an auditionable pair. Explain “settled,” “floating,” and “tension” as contextual suggestions. A unison on a non-tonic is the same pitch, not necessarily “home.”
5. Scale lock affects new pitched notes through all supported creation routes; changing the scale does not rewrite existing music. Keep drum lanes excluded. Any transpose-to-scale operation must be separately explicit and undoable.
6. Expose QWERTY mode, key map, octave and velocity. Test note-off on focus loss, typing into search/coach/name fields, dialogs, track/device switches, mode disable and application deactivation. Respect the existing shortcut system.

**Done:** a beginner changes a beat, tries chords, plays a sampled sound and changes a melody with understandable visual feedback. Simple/advanced switches and save/reopen preserve all notes. No stuck notes or sound triggered by typing.

### P5 — Make Session-to-song behavior understandable and correct

Reuse Fixture B/C, `PlaceSceneInArrangementCommand`, SessionClipScheduler, SessionRecorder and existing track playback modes.

1. Keep **Place scene** and **Capture jam** distinct. Placement copies a chosen scene to an explicit range. Capture records actual launch/performance timing. Never call a static copy a recorded performance.
2. Replace any fixed first-scene/after-loop assumption with a visible scene and destination choice or a clearly explained simple default. Detect occupied ranges before applying; no silent overwrite or unexplained jump far down the timeline.
3. Use intro/main/variation/ending templates over editable clips. For the reference fixture, 32 bars at 100 BPM equals 76.8 seconds before tails. Calculate real duration through the tempo map; other moods/tempos need different duration choices, not a hardcoded “one minute” label.
4. Show per-track source labels and a truthful mixed-source summary near the relevant controls. Derive them from audible track state; empty projects and non-playing Aux returns must not misleadingly claim a performance source.
5. Provide **Return to Arrangement** when Session overrides apply. Switching views alone must not alter playback. Explain pending quantized changes and the actual source the user will hear.
6. Preserve timing, content, routing and supported automation during capture/placement. Test launch at boundaries, stop mid-bar, loop wrap, tempo changes, mute/solo, empty scene, occupied range and undo. Expose unsupported cases instead of silently dropping data.
7. Provide short next-step coaching: launch → capture/place → return → edit one section. Keep this connected to the same conductor conversation in P7.

**Done:** a visibly different Session/Arrangement fixture proves which source plays; recorded launches retain timing; Return changes the heard source; the finished song remains editable after undo/redo and reopen.

### P6 — Complete the approachable mixer and spatial effects

Reuse MixerView, MixerToggleRail, Mix Analyze and `ApplySharedSpatialReturnCommand`.

1. Verify the actual guided default exposes labels/meters, volume, pan, mute and solo. Collapse advanced sends/spectrum/routing in the presentation without changing stored processing. Preserve experienced users' preferences.
2. Keep **Analyze** discoverable and operational. Show measured results with their status/source. Do not generate a “mix health” score from a canned suggestion or claim the coach heard audio without analysis input.
3. Make Shared Space optional. Configure one suitable Aux return, send levels and reverb using established conventions; explain whether the knob controls send amount or wet/dry. Avoid feedback/self-routing and excessive dry duplication through the return.
4. Use durable ownership/configuration to reuse a SUNROOM return. Do not commandeer an unrelated user Aux merely because it contains reverb, rename it, or delete it on undo. Preserve existing sends and manual changes.
5. Offer a small curated set of existing FX/macros, with truthful parameter units, reset and undo. Verify that renamed tracks and non-fixture SUNROOM journeys can use the supported flow.

**Done:** levels, pan and FX audibly change; hidden routing remains intact; repeated Shared Space use does not multiply returns; undo/reopen preserve prior routing; Analyze displays real results.

### P7 — Complete the conductor and proposal transaction boundary

Reuse the staged proposal code and existing agent orchestration. Extend the smallest suitable controller rather than introducing an unrelated agent framework.

1. Inventory all model-backed mutation routes: companion DSL, recipe/melody application, console specialists, music/chord/mix tools and MCP. Route model writes through a consistent host-owned coordinator while retaining existing grants and direct manual workflows.
2. Maintain one project-scoped conversation/plan across Create, Session, Arrange and Mix. Track project-session identity, revision, stable selected IDs, request ID, provider/model and proposal state. A short last-exchange string is not the full conductor requirement.
3. Separate explanation, settings-only recipes and actual song edits in the UI and schemas. Never imply Apply recipe already generated tracks when it only changed settings.
4. Prevalidate permitted operations, target existence, parameter ranges, supported devices, asset references and complete DSL semantics. Prohibit shell/code execution from model responses. Validate all of a multi-action proposal before applying as far as the existing command system permits.
5. Recheck project/selection/revision at Apply and at asynchronous completion. Cover two unsaved projects, save-as, track deletion, renamed targets, manual edits, view switches, cancel, retry and double Apply. View changes alone should not discard useful conversation.
6. Use one bounded project writer; inference remains nonblocking for editing/playback. Late/canceled results cannot reopen or apply an old proposal. Expose failures and leave the song/history consistent.
7. Record actual before/after deltas and a stable undo transaction identity. Generic text “Apply suggestion” is insufficient to identify which suggestion an A/B control owns, especially after two suggestions.

**Done:** deterministic mock responses prove the real validator/executor and failure behavior, one coordinated conversation survives view changes, and stale/canceled/cross-project writes are prevented. Mock passes remain separate from P8 live model evidence.

### P8 — Ground the coach and verify local/API switching

Reuse `sunroom_mlx_client`, the existing MLX helper, provider settings, secure key storage, and `resources/sunroom/knowledge/coach.md`.

1. Build a concise capability/context packet from actual host state: current view, selected stable IDs, tempo/meter/key/mode, relevant notes/chords, section/source state, available devices with parameter schemas/units, supported action schemas, recent committed changes and any actual analysis. Do not describe every muted or idle track as “playing.”
2. Update the maintained knowledge file with the current product workflow and exact supported examples. It must teach Session versus Arrange, Drum Grid versus Chord Engine versus Chord Track, scale/color meanings, undo/export behavior, timing units and psybient arrangement/mixing examples. Remove obsolete capabilities or instructions when implementation changes.
3. Retrieve relevant guidance instead of appending unlimited manuals. Separate trusted tool instructions from quoted track names, imported metadata and conversation text. Keep context bounded and identify truncated material honestly.
4. Offer a few supported prompts: simplify this beat, vary this motif, explain these notes, help arrange this loop, explain measured mix feedback. Each is enabled only when the real action/context supports it. Explanations may remain read-only.
5. Verify local readiness, loading, cancellation, resource errors and idle cleanup. Missing AI must not block offline recipes or editing; fixed tips must be labeled as fixed tips. An installed-runtime check alone is not a live inference check.
6. Preserve the local Mac, LAN server and API selector. Show the active provider/model and resource/connection status. Do not silently fall back to paid cloud. Verify cloud model IDs and reasoning options against the configured provider's current capabilities before enabling them; a Codex/Cursor display name is not proof of public API availability.
7. Keep API credentials in the existing masked settings/Keychain flow, out of source, project files, prompts and logs. Do not generate, invent or request keys in chat. If no owner-configured key is available, implement/test the adapter contract and label the live cloud check pending.
8. Treat the 16 GB Windows mini PC as an optional separate inference server. Its CPU/GPU and endpoint remain to be verified; do not assume it can pool memory with MLX or run a named model effectively. Keep audio on the Mac, reuse current authenticated/trusted endpoint policy, and handle server-off/timeouts gracefully. Do not require remote setup to finish core local music workflows.
9. Implement audible before/after scoped to a specific applied proposal. Reuse existing history/preview infrastructure; block or refresh comparison after intervening edits. Preserve transport/source state and never roll back unrelated work. Explain if applying a new edit ends the comparison.
10. After a helpful edit, suggest one manual change. Ground theory in deterministic calculations and mix advice in supplied measurements; make no claim of hearing an unanalyzed track or measuring the user's learning.

**Done:** a real configured Mac-local model produces a useful validated suggestion, the user sees the action and hears apply/A-B/undo, then makes a manual edit. Provider switching, missing model, invalid reply, cancellation and failed connection have honest behavior. Record provider/model/runtime and latency with the test environment. Cloud/LAN live checks without credentials/hardware remain separate pending gates; do not claim them tested.

### P9 — Make the sound library useful before importing

Reuse the current manifest/catalog, MediaExplorerContent preview transport, MediaDbBrowserContent and normal media import/asset ownership.

1. Add a clear **Preview / Stop** action that does not add tracks, clips or dirty the song, plus a separate **Add to song** action and supported drag/drop. Reuse the preview subsystem, including its output routing and playback cleanup.
2. Connect curated collections and kind/key/BPM controls to the existing library/search experience. Preserve semantic/similarity search. Distinguish one-shots, pitched samples, tempo-based loops and textures so inappropriate filters are not offered as meaningful.
3. Keep metadata provenance: declared, analyzed estimate or unknown. Unpitched is different from unknown key. A one-shot can have BPM “not applicable”; do not fabricate tempo merely to fill a filter.
4. Add a small useful set of cleared psychill rhythm loops, tuned textures or generated recipe renders with verified metadata, alongside the current one-shots. Metadata filters need useful results, not only a truthful empty set. Keep editable starter recipes as the main composition path.
5. Reuse supported time stretching/transposition, showing the original and applied values. Do not promise matching when an engine transform or reliable metadata is unavailable.
6. Import to the intended selected Session slot/track or a clearly described new track. A library click must not silently create Arrangement audio at the origin while the UI implies Session insertion.
7. Resolve media through the existing managed/project asset system or a verified stable resource ID. Prove that projects reopen when the app/source checkout moves or updates. Do not rely on the current absolute bundled WAV path as durable project ownership.
8. Stop previews on cancellation/close/device changes. Cleanup may remove only owned unused temporary previews, accounting for undo/recovery references. Never delete user sources, imported media or shared bundled files on Undo.

**Done:** a user combines filters/search, previews safely, imports intentionally, hears the clip, undoes/redoes, saves and reopens with resolved media. Preview-only interactions leave the project unchanged.

### P10 — Finish the existing export flow for beginners

Reuse `MainWindowExport.cpp`, ExportAudioDialog and the existing offline rendering path. The guide's export button already invokes this system.

1. Make **Export song** a clear guided action with a preview of source, section/range, duration and destination. Choose a supported stereo WAV default; retain advanced format/rate/depth options. Do not introduce another codec or renderer for parity.
2. Establish the actual renderer's source behavior. If Session overrides exist, explicitly explain/resolve them or use a verified Arrangement-only render. Export must not silently differ from the source described in the UI.
3. Use real arrangement bounds/tempo map and the existing effect-tail policy. Handle an empty arrangement by linking to P5; do not silently export the currently visible eight-bar Session loop as a finished song.
4. Keep destination selection and overwrite handling. Render to a safe temporary output through existing facilities, finalize before announcing success, and provide real progress/cancel/error states. Canceled exports must not leave a misleading final file or destroy a previous export.
5. Offer Reveal/Open using actual host support. “Share” can mean finding the exported file; do not add cloud publishing or an account requirement.
6. Preserve unsaved project state and transport/source state through export. Verify live-audio external insert behavior only to the extent already supported; do not label untested external hardware routes accepted.

**Done:** the file independently decodes/plays, contains expected source content, has the expected channel/rate/duration plus explained tails, and can be found by the user. Empty, canceled, unwritable and overwrite scenarios behave correctly.

### P11 — Native end-to-end acceptance and focused polish

Use the exact rebuilt native app, a disposable profile, normal controls and recorded provenance. CLI/mocks/source inspection supplement this; they cannot replace it.

| Journey/check | Required observation |
|---|---|
| Offline new user | Beat/psybient recipe → audible Session clips; no network/model/key requirement |
| Own musical edit | Edit a drum step, chord or melody; real change, usable undo and note guidance |
| Instrument front door | Real Drum Grid, Chord Engine with sound source, and Sampler are usable |
| Keyboard/focus | Notes work; text entry, dialogs and focus loss do not cause sounds/stuck notes |
| AI help | Real local suggestion → explanation/commands → Apply → hear before/after → undo |
| AI races/errors | Manual edits, cancel, project switch, missing model and endpoint failure preserve music |
| Arrange | Different launches captured with correct timing; placement is distinct; Return/source labels accurate |
| Mix | Heard fader/pan/mute/solo/FX changes; advanced settings retained; real Analyze reachable |
| Media | Preview without mutation → intentional import → undo/redo → durable reopening |
| Persistence | Save/reopen equality; isolated recovery; failed save preserves last valid file |
| Export | Intended arrangement produces a playable independent file with expected timing/content |
| Advanced compatibility | Representative older songs, automation/devices, Session/DSL/Analyze and existing advanced tools remain usable |
| Appearance/access | Consistent purple/orange sunset; readable notes/meters; no color-only meaning; keyboard/text scaling/minimum-size checks |
| Performance/lifecycle | Playback while coaching/previewing stays usable; no new resource leak, shutdown crash or stuck worker |

Capture screenshots of first sound, note guidance, source state, mixer, coach proposal and export result; reference the actual project and exported audio. Record objective audio/duration checks separately from subjective listening. Never claim a headless nonzero render proves the native output device works.

After technical acceptance, a small optional beginner trial can identify friction: first sound, one independent edit, identify what is playing, finish/save/export. Record actual observations; a scripted developer run is not proof that untrained users succeeded. Do not make an external trial a blocker to completing safe implementation work.

**Done:** all eleven M/S items have concrete evidence, critical failures are repaired, and any unavailable verification is visibly pending rather than counted as accepted.

### P12 — Local delivery and review handoff

1. Update existing `inventory.md`, `plan.md`, `progress.md`, `verification.md`, `decisions.md` and relevant SUNROOM user guidance. Consolidate current status there; do not proliferate competing progress files per chat.
2. Attach the final requirement/evidence matrix, exact app/CLI revision and changed-source state, validation results, representative project, screenshots and playable export.
3. Document the local setup and provider-switching flow, clear build/model prerequisites, compatibility limits and pending cloud/LAN/hardware checks. Include a safe way to return to the prior app build without rewriting songs.
4. Prepare a concise review description. Local implementation and review are in scope; merging, public publishing and replacing the owner's installed app are separate actions unless explicitly requested.

**Core acceptance:** offline editable first sound → independent edit → real local coach when configured → safe arrangement/mix → save/recovery/reopen → verified export, with advanced tools available and the user's SUNROOM identity intact. Report pending gates by name and count, not a speculative completion percentage.

## 7. Validation commands and evidence handling

Run from the repository root. These are starting commands grounded in existing targets/scripts, **not results from this planning turn**. Read project build instructions and script arguments first. Resolve the Xcode prerequisite normally before claiming a fresh native build. Use modest build parallelism and preserve build caches.

```sh
cd '/Users/loganchambers/Documents/ChatGPT/ai daw'
git status --short
git log -1 --oneline
git diff --check
cmake --build build-sunroom --target magda_cli magda_daw_app sunroom_theory_test --parallel 2
ctest --test-dir build-sunroom -N
./build-sunroom/tests/sunroom_theory_test
python3 tests/sunroom/test_mlx_boundary.py
python3 scripts/verify_sunroom_native.py --cli build-sunroom/magda/daw/magda_cli_artefacts/Release/magda_cli
```

The beginner scripts accept an optional CLI path and otherwise use that existing `build-sunroom` path. Run the phases relevant to the change; after integration, run all P1–P9 scripts sequentially because they reuse project infrastructure and fixed artifact locations:

```sh
python3 scripts/verify_beginner_p1.py
python3 scripts/verify_beginner_p2.py
python3 scripts/verify_beginner_p3.py
python3 scripts/verify_beginner_p4.py
python3 scripts/verify_beginner_p5.py
python3 scripts/verify_beginner_p6.py
python3 scripts/verify_beginner_p7.py
python3 scripts/verify_beginner_p8.py
python3 scripts/verify_beginner_p9.py
```

Build/run relevant `magda_tests` and `magda_juce_tests` targets using the discovered test filters/CTest names, and run repository-required checks. Add a focused P10 export harness if existing render tests cannot cover the beginner export behavior. Do not write source-string/button-label tests as substitutes for behavior. Do not repeatedly run unrelated heavyweight suites after the required checks already pass without a new reason.

The current beginner scripts redirect `MAGDA_DATA_DIR` and `MAGDA_CONFIG_FILE` to artifact profiles. Verify native launch also uses an isolated profile before exercising recovery or preferences. Capture the exact binary used; build outputs and installed app bundles are different evidence targets.

For each phase record:

```text
Phase/slice:
Requirement IDs:
Source revision + dirty files; binary/build identity:
User-visible behavior delivered:
Reused components and changed files:
Automated checks: command -> actual result -> artifact:
Native UI/audio checks actually performed:
Live model/provider checks actually performed:
Remaining acceptance gates (passed / failed / not run):
Next eligible slice and its exact first action:
```

## 8. Nice backlog after core acceptance

| ID | Bounded implementation | Dependencies / acceptance |
|---|---|---|
| N1 | A few curated multi-scene psybient packs | P2/P5/P9; editable layers, provenance, sensible levels and measured size |
| N2 | Optional resumable tutorial | P3–P11; detects real completed actions, can skip/reopen, never blocks playback |
| N3 | Focused instrument surfaces | P4/P6; original controls over the same device state, advanced access preserved |
| N4 | Collaboration/cloud sharing | Separate product/architecture proposal before coding accounts/storage/conflicts; local export already covers basic sharing |
| N5 | Seeded dice/randomization | P2/P9; preserve locked parts, preview/cancel, one undo, reproducible seed |
| N5b | Genre/key/BPM loop matching | P7/P9; editable layered Session clips with real action trace, declared transforms/provenance; no opaque stereo song |
| N6 | Additional sound-design agent tools | P4/P6/P7/P8; bounded Sampler/Drum Grid/FX operations with parameter deltas, audition and undo |

Preservation/discoverability polish for existing Chord Track, stems and takes/comping may follow; verify actual platform/device support before promising it. Loop matching is distinct from black-box full-song generation and should not be prohibited merely because the latter is deferred.

## 9. Explicit boundaries

Do not add FL-style Pattern/Playlist as a fourth composition model, chase suite/plugin-count parity, build a plugin marketplace, require advanced routing before basic mixing, force cloud keys before first sound, hide Session/DSL/Analyze permanently, replace the native stack with a website, or clone competitor branding/UI. Keep optional stem/comping discoverability out of first-run requirements. Do not rebuild existing systems simply because the PDF compares them to other products.

**Recommended first Cursor task:** P0 reconciliation followed by the smallest unmet P1 acceptance slice. The old tracker makes export look next, but earlier mandatory flows still need completion and native evidence. Refresh the facts before choosing the first code edit.

## Source basis

Source PDF: `/Users/loganchambers/Downloads/Magda_DAW_Beginner_Feature_Gaps.pdf`; repository copy: `docs/beginner-experience/Magda_DAW_Beginner_Feature_Gaps.pdf`. Core priorities come from PDF pages 4–6; source distinctions and exclusions from pages 2–3 and 7–10. The plan also preserves the user's earlier SUNROOM aesthetic, psybient and AI-provider requirements. Internal research claim IDs were not independently reopened. Current source findings and unverified behavior are distinguished throughout.
