#!/usr/bin/env python3
"""P5 beginner gate: Fixture B sections, Place Scene, Fixture C dual sources."""
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
qa = ROOT / "artifacts/beginner-p5"
qa.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
env["MAGDA_DATA_DIR"] = str(qa / "profile")
env["MAGDA_CONFIG_FILE"] = str(qa / "profile/config.json")
env.setdefault("MAGDA_AUTOSAVE_RECOVER", "discard")
records = []


def call(name, *argv):
    start = time.monotonic()
    result = subprocess.run(
        [str(cli), *map(str, argv)],
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    log = result.stdout + "\n" + result.stderr
    (qa / f"{name}.log").write_text(log)
    records.append(
        {"step": name, "returncode": result.returncode, "seconds": round(time.monotonic() - start, 2)}
    )
    assert result.returncode == 0, f"{name} failed; see {qa / (name + '.log')}\n{log[-1500:]}"
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


report = call("00-capture-vs-place", "capture-vs-place")
assert "capture-start launch 1.5" in report, report
assert "capture-start transport 3.5" in report, report
assert "headless-recorder no" in report, report
assert "Not this command." in report

defaults = call("00b-place-default", "place-scene-default")
for line in ("scene 0", "loop 100 beat 128", "loop 128 beat 128", "loop 160 beat 160"):
    assert line in defaults, defaults

returned = call("00c-return", "return-to-arrangement")
for line in ("clip-set Session", "clip-cleared Arrangement", "headless-scheduler no", "deactivate-called"):
    assert line in returned, returned

sources = call("00d-playback-source", "playback-source")
for line in (
    "empty Playback source: none. No playable tracks yet.",
    "aux Playback source: none. No playable tracks yet.",
    "arrangement Playback source: Arrangement (all playable tracks).",
    "mixed Playback source: mixed - 1 Session, 1 Arrangement.",
):
    assert line in sources, sources

blank = saved(call("01-init", "init", qa / "Blank.mgd"))
song = saved(call("02-fixture-b", "exec", blank, "fixture-b", "--out", qa / "Song.mgd"))
doc = dump_project("02b-dump", song)
assert doc.get("loopEndBeats", 0) >= 127.9
# Markers may be absent from dump-json DTO — check compressed project
import zlib

raw = zlib.decompress(song.read_bytes()).decode("utf-8", "replace")
for name in ("Intro", "Main", "Variation", "Ending"):
    assert name in raw, f"missing marker {name}"

# Session scenes + arrangement sections should exist as named clips
clip_names = set()
for track in doc.get("tracks") or []:
    for clip in track.get("clips") or []:
        clip_names.add(clip.get("name") or "")
assert any("Scene Intro" in n for n in clip_names) or any("Intro / Drums" in n for n in clip_names)

# Place Scene into empty region after the song (beat 128)
placed = saved(
    call(
        "03-place-scene",
        "exec",
        song,
        "place-scene",
        "0",
        "128",
        "--out",
        qa / "Placed.mgd",
    )
)
assert "Deterministic place" in (qa / "03-place-scene.log").read_text()

# Occupied destination must refuse
bad = subprocess.run(
    [str(cli), "exec", placed, "place-scene", "0", "0", "--out", qa / "Conflict.mgd"],
    env=env,
    capture_output=True,
    text=True,
    timeout=300,
)
(qa / "04-conflict.log").write_text(bad.stdout + "\n" + bad.stderr)
records.append({"step": "04-conflict", "returncode": bad.returncode, "seconds": 0})
assert bad.returncode != 0
assert "overwrite" in (bad.stdout + bad.stderr).lower() or "already has clips" in (
    bad.stdout + bad.stderr
)
print("04-conflict passed", flush=True)

cblank = saved(call("05-init-c", "init", qa / "BlankC.mgd"))
cproj = saved(call("06-fixture-c", "exec", cblank, "fixture-c", "--out", qa / "FixtureC.mgd"))
cdoc = dump_project("06b-dump", cproj)
by_name = {t.get("name"): t.get("clips") or [] for t in cdoc.get("tracks") or []}
assert {"Pulse", "Pad"} <= set(by_name)
pulse = by_name["Pulse"]
pad = by_name["Pad"]
session = [
    c
    for c in pulse
    if c.get("view") == "session" and c.get("name") == "Fixture C / Session Pulse"
]
arrangement = [
    c
    for c in pulse
    if c.get("view") == "arrangement" and c.get("name") == "Fixture C / Arrangement Pulse"
]
assert len(session) == 1 and len(arrangement) == 1
# Arrangement is kick-on-1 only (8 notes). Session is a different full beat (96 notes).
assert len(arrangement[0].get("notes") or []) == 8
assert len(session[0].get("notes") or []) == 96
arrangement_notes = {n.get("note") for n in arrangement[0]["notes"]}
session_notes = {n.get("note") for n in session[0]["notes"]}
arrangement_starts = {n.get("startBeat") for n in arrangement[0]["notes"]}
session_starts = {n.get("startBeat") for n in session[0]["notes"]}
assert len(arrangement_notes) == 1
assert session_notes > arrangement_notes
assert 0.5 in session_starts and 0.5 not in arrangement_starts
assert all(c.get("view") == "arrangement" for c in pad)
assert any(c.get("name") == "Fixture C / Arrangement Pad" for c in pad)
assert not any(c.get("view") == "session" for c in pad)
summary = (qa / "06-fixture-c.log").read_text()
assert "different Session clip" in summary
assert "Pad is Arrangement-only" in summary

result = {
    "phase": "P5",
    "status": "PASS",
    "records": records,
    "gates": {
        "capture_jam": "code path - wraps SessionRecorder via StartRecordEvent",
        "return_to_arrangement": "code path - deactivateAllSessionClips",
        "source_badges": "transport tooltip from TrackPlaybackMode",
        "gui_audible_mixed_source": "not run - Xcode license / app relink",
    },
}
(qa / "result.json").write_text(json.dumps(result, indent=2) + "\n")
print("P5 PASS", flush=True)
