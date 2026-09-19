#!/usr/bin/env python3
"""P4 beginner gate: Fixture A clips exist; scale-lock rule covered by theory_test."""
import json
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
cli = pathlib.Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "build-sunroom/magda/daw/magda_cli_artefacts/Release/magda_cli"
).resolve()
theory = pathlib.Path(
    sys.argv[2]
    if len(sys.argv) > 2
    else "build-sunroom/tests/sunroom_theory_test"
).resolve()
qa = ROOT / "artifacts/beginner-p4"
qa.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
env["MAGDA_DATA_DIR"] = str(qa / "profile")
env["MAGDA_CONFIG_FILE"] = str(qa / "profile/config.json")
env.setdefault("MAGDA_AUTOSAVE_RECOVER", "discard")
records = []


def call(name, *argv, binary=None):
    start = time.monotonic()
    exe = binary or cli
    result = subprocess.run(
        [str(exe), *map(str, argv)],
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    log = result.stdout + "\n" + result.stderr
    (qa / f"{name}.log").write_text(log)
    records.append(
        {
            "step": name,
            "returncode": result.returncode,
            "seconds": round(time.monotonic() - start, 2),
        }
    )
    assert result.returncode == 0, f"{name} failed; see {qa / (name + '.log')}\n{log[-1200:]}"
    assert "JUCE Assertion failure" not in log
    print(name, "passed", flush=True)
    return result.stdout


def saved(output):
    lines = [line[6:].strip() for line in output.splitlines() if line.startswith("Saved ")]
    assert lines, output[-500:]
    path = pathlib.Path(lines[-1])
    assert path.is_file()
    return path


def dump_project(name: str, project: pathlib.Path) -> dict:
    out = qa / f"{name}-dump.mgd"
    stdout = call(name, "exec", project, "--dump-json", "--out", out)
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("{") and '"tracks"' in line:
            return json.loads(line)
    raise AssertionError(f"{name}: missing dump-json")


focus = call("00b-keyboard-focus", "keyboard-play-focus")
for line in (
    "none yield-no",
    "text-editor yield",
    "child-of-text-editor yield",
    "editable-label yield",
    "fixed-label yield-no",
    "plain yield-no",
):
    assert line in focus, focus

lock = call("00c-scale-lock-insert", "scale-lock-insert")
for line in (
    "pitched 10 -> 11",
    "drum-grid 10 -> 10",
    "lock-off 10 -> 10",
    "no-guide 10 -> 10",
):
    assert line in lock, lock
drum_grid = (ROOT / "magda/daw/ui/panels/content/DrumGridClipContent.cpp").read_text()
assert "snapToScale" not in drum_grid

release = call("00d-note-release", "keyboard-note-release")
for line in (
    "typing release held 0",
    "inside keep held 2",
    "outside release held 0",
    "none release held 0",
    "no-window keep held 2",
):
    assert line in release, release

assert theory.is_file(), f"missing theory_test binary: {theory}"
call("00-scale-lock-theory", binary=theory)

blank = saved(call("01-init", "init", qa / "Blank.mgd"))
starter = saved(
    call("02-create-and-play", "exec", blank, "create-and-play", "--out", qa / "Starter.mgd")
)
doc = dump_project("02b-dump", starter)
tracks = {t["name"]: t for t in doc.get("tracks") or []}
assert {"Drums", "Bass", "Chords"} <= set(tracks)

clip_names = set()
for track in doc.get("tracks") or []:
    for clip in track.get("clips") or []:
        clip_names.add(clip.get("name") or "")
# dump-json may nest clips differently — also scan top-level clips
for clip in doc.get("clips") or []:
    clip_names.add(clip.get("name") or "")

needed = {"Fixture A / Drums", "Fixture A / Bass", "Fixture A / Chords"}
missing = needed - clip_names
assert not missing, f"missing fixture clips {missing}; found {sorted(clip_names)[:20]}"

info_root = doc.get("keyRoot")
info_quality = doc.get("keyQuality")
assert info_root == 9, f"expected A (9), got {info_root}"
assert info_quality in ("minor", 1), f"expected minor, got {info_quality}"
assert tracks["Drums"]["devices"][0]["pluginId"] == "drumgrid"
chord_ids = [d.get("pluginId") for d in tracks["Chords"]["devices"]]
assert chord_ids[:2] == ["midichordengine", "magda_polysynth"], chord_ids
bass_ids = [d.get("pluginId") for d in tracks["Bass"]["devices"]]
assert "midichordengine" not in bass_ids
assert bass_ids[0] == "magda_polysynth"
assert "Sound" in tracks
sound_ids = [d.get("pluginId") for d in tracks["Sound"]["devices"]]
assert sound_ids == ["magdasampler"], sound_ids
sound_state = tracks["Sound"]["devices"][0].get("pluginState") or ""
assert "Glass mote 01.wav" in sound_state, sound_state[:400]

editors = call(
    "02c-editors",
    "exec",
    starter,
    "editor-for-track",
    "Drums",
    "editor-for-track",
    "Bass",
    "editor-for-track",
    "Chords",
)
assert "editor drum-grid identifier drumgrid" in editors
assert editors.count("editor piano-roll") >= 2

# sunroomMood/Guide live in the compressed .mgd payload; dump-json DTO omits them.
# Fixture A code sets sunroomMood=1 + sunroomGuide; keyRoot/quality above prove key.

result = {
    "phase": "P4",
    "status": "PASS",
    "records": records,
    "fixture_clips": sorted(needed),
    "keyRoot": info_root,
    "keyQuality": info_quality,
    "gates": {
        "gui_make_beat_add_chords_play_sound": "Sound track stores magdasampler with Glass mote 01; panel not opened",
        "qwerty_text_focus": "typing, outside, and no focus release held notes; inside the window keeps them",
        "scale_lock_new_notes_only": "scale-lock-insert: A# snaps to B only when lock and guide are on",
        "drum_lanes_no_scale_lock": "drum-grid insert stays 10; DrumGridClipContent does not call snapToScale",
    },
}
(qa / "result.json").write_text(json.dumps(result, indent=2) + "\n")
print("P4 PASS", flush=True)
