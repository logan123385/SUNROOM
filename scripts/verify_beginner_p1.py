#!/usr/bin/env python3
"""P1 beginner gate: grouped journey undo/redo via UndoManager, save/reopen, failed overwrite."""
import gzip
import json
import os
import pathlib
import subprocess
import sys
import time
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
cli = pathlib.Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "build-sunroom/magda/daw/magda_cli_artefacts/Release/magda_cli"
).resolve()
qa = ROOT / "artifacts/beginner-p1"
qa.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
env["MAGDA_DATA_DIR"] = str(qa / "profile")
env["MAGDA_CONFIG_FILE"] = str(qa / "profile/config.json")
env.setdefault("MAGDA_AUTOSAVE_RECOVER", "discard")
records = []


def call(name, *argv, env_override=None):
    start = time.monotonic()
    result = subprocess.run(
        [str(cli), *map(str, argv)],
        env=env_override or env,
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
    assert result.returncode == 0, f"{name} failed; see {qa / (name + '.log')}\n{log[-800:]}"
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
    # dump-json is printed before the Saved line
    payload = None
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("{") and '"tracks"' in line:
            payload = json.loads(line)
            break
    assert payload is not None, f"{name}: missing dump-json payload\n{stdout[-500:]}"
    return payload


def music_fingerprint(doc: dict) -> dict:
    """Stable musical identity; ignore project display name (follows save path)."""
    tracks = []
    for track in doc.get("tracks", []):
        clips = []
        for clip in track.get("clips", []):
            clips.append(
                {
                    "type": clip.get("type"),
                    "view": clip.get("view"),
                    "startBeat": clip.get("startBeat"),
                    "lengthBeats": clip.get("lengthBeats"),
                    "notes": clip.get("notes") or [],
                }
            )
        tracks.append(
            {
                "name": track.get("name"),
                "volume": track.get("volume"),
                "clips": clips,
            }
        )
    return {
        "tempo": doc.get("tempo"),
        "timeSignatureNumerator": doc.get("timeSignatureNumerator"),
        "timeSignatureDenominator": doc.get("timeSignatureDenominator"),
        "keyRoot": doc.get("keyRoot"),
        "keyQuality": doc.get("keyQuality"),
        "loopEnabled": doc.get("loopEnabled"),
        "loopStartBeats": doc.get("loopStartBeats"),
        "loopEndBeats": doc.get("loopEndBeats"),
        "tracks": tracks,
    }


def clip_count(doc: dict) -> int:
    return sum(len(t.get("clips") or []) for t in doc.get("tracks") or [])


def decode_mgd(data: bytes) -> dict:
    if data[:2] == b"\x1f\x8b":
        raw = gzip.decompress(data)
    else:
        raw = zlib.decompress(data)
    return json.loads(raw)


def encode_like(doc: dict, original: bytes) -> bytes:
    raw = json.dumps(doc).encode("utf-8")
    if original[:2] == b"\x1f\x8b":
        return gzip.compress(raw)
    return zlib.compress(raw)


def track_names(doc: dict) -> set[str]:
    return {track.get("name") for track in doc.get("tracks") or []}


blank = saved(call("01-init", "init", qa / "Blank.mgd"))
blank_fp = music_fingerprint(dump_project("01b-blank-dump", blank))

# Journey runs through UndoManager and verifies undo/redo internally, leaving music applied.
composed = saved(
    call(
        "02-compose",
        "exec",
        blank,
        "sunroom-journey",
        0,
        2,
        8,
        84,
        "--out",
        qa / "Idea.mgd",
    )
)
composed_fp = music_fingerprint(dump_project("02b-compose-dump", composed))
assert clip_count({"tracks": composed_fp["tracks"]}) > 0, "compose produced no clips"
assert composed_fp != blank_fp, "compose did not change musical state"

# Same-session undo removes the grouped insertion before save.
undone = saved(
    call(
        "03-undo",
        "exec",
        blank,
        "sunroom-journey",
        0,
        2,
        8,
        84,
        "undo",
        "--out",
        qa / "Idea-undone.mgd",
    )
)
undone_fp = music_fingerprint(dump_project("03b-undo-dump", undone))
assert undone_fp == blank_fp, "grouped undo did not restore blank musical state"

# Same-session undo then redo restores the grouped insertion.
redone = saved(
    call(
        "04-redo",
        "exec",
        blank,
        "sunroom-journey",
        0,
        2,
        8,
        84,
        "undo",
        "redo",
        "--out",
        qa / "Idea-redone.mgd",
    )
)
redone_fp = music_fingerprint(dump_project("04b-redo-dump", redone))
assert redone_fp == composed_fp, "grouped redo did not restore composed musical state"

reopened = saved(call("05-roundtrip", "run", redone, "--out", qa / "Idea-reopened.mgd"))
reopened_fp = music_fingerprint(dump_project("05b-roundtrip-dump", reopened))
assert reopened_fp == redone_fp, "save/reopen changed musical state"

# Failed overwrite must not clobber a good file.
prior = redone.read_bytes()
redone.chmod(0o444)
fail = subprocess.run(
    [str(cli), "run", str(redone), "--out", str(redone)],
    env=env,
    capture_output=True,
    text=True,
    timeout=120,
)
redone.chmod(0o644)
(qa / "06-readonly-save.log").write_text(fail.stdout + "\n" + fail.stderr)
assert fail.returncode != 0, "read-only overwrite unexpectedly succeeded"
assert redone.read_bytes() == prior, "read-only overwrite corrupted the prior project"
assert "not writable" in (fail.stdout + fail.stderr).lower() or "permission" in (
    fail.stdout + fail.stderr
).lower(), fail.stdout + fail.stderr
records.append({"step": "06-readonly-preserve", "returncode": fail.returncode, "preserved": True})
print("06-readonly-preserve passed", flush=True)

# Headless autosave recovery via MAGDA_AUTOSAVE_RECOVER=recover.
sidecar = redone.with_name(redone.name + ".autosave")
sidecar.write_bytes(undone.read_bytes())
os.utime(sidecar, None)
env_recover = env.copy()
env_recover["MAGDA_AUTOSAVE_RECOVER"] = "recover"
recovered = saved(
    call(
        "07-autosave-recover",
        "run",
        redone,
        "--out",
        qa / "Idea-recovered.mgd",
        env_override=env_recover,
    )
)
assert recovered.is_file()
recovered_fp = music_fingerprint(dump_project("07b-recover-dump", recovered))
assert recovered_fp == undone_fp, "autosave recovery did not load the sidecar"

inject_env = env.copy()
inject_env["MAGDA_SUNROOM_INJECT_FAIL"] = "fixture-a-after-first-track"
partial_out = qa / "Partial-failed.mgd"
if partial_out.exists():
    partial_out.unlink()
partial = subprocess.run(
    [
        str(cli),
        "exec",
        str(blank),
        "sunroom-journey",
        "0",
        "2",
        "8",
        "84",
        "undo",
        "fixture-a",
        "--out",
        str(partial_out),
    ],
    env=inject_env,
    capture_output=True,
    text=True,
    timeout=300,
)
partial_log = partial.stdout + "\n" + partial.stderr
(qa / "08-partial-failure.log").write_text(partial_log)
assert partial.returncode != 0, partial_log[-800:]
assert "Injected failure after the first track" in partial_log
assert "Redo: 'Create SUNROOM journey'" in partial_log
assert "Fixture clips remain: no" in partial_log
assert "Remaining track Drums" not in partial_log
assert "tempo 100" not in partial_log
assert "Redo after failure: 'Create SUNROOM journey'" in partial_log
assert "fixture resurrected: no" in partial_log
assert not partial_out.exists() and not (qa / "Partial-failed").exists()
records.append({"step": "08-partial-failure", "returncode": partial.returncode, "preserved": True})
print("08-partial-failure passed", flush=True)

sample = saved(
    call(
        "09-sample",
        "exec",
        blank,
        "add-sample",
        "Heartbeat 01.wav",
        "--out",
        qa / "Sample.mgd",
    )
)
sample_doc = decode_mgd(sample.read_bytes())
assert sample_doc.get("sources"), "imported sample did not record a source"
missing_wav = qa / "missing-media" / "gone.wav"
assert not missing_wav.exists()
for source in sample_doc["sources"]:
    source["filePath"] = str(missing_wav)
    source["sampleRate"] = 48000
missing_project = qa / "missing-src.mgd"
missing_project.write_bytes(encode_like(sample_doc, sample.read_bytes()))
missing_prior = missing_project.read_bytes()
reopened_missing = saved(
    call(
        "09b-missing-reopen",
        "exec",
        missing_project,
        "--dump-json",
        "--out",
        qa / "Missing-reopened.mgd",
    )
)
assert missing_project.read_bytes() == missing_prior, "reopen rewrote the project with missing media"
reopened_doc = decode_mgd(reopened_missing.read_bytes())
reopened_sources = reopened_doc.get("sources") or []
assert reopened_sources, "reopen dropped the missing source"
assert reopened_sources[0].get("filePath") == str(missing_wav)
assert float(reopened_sources[0].get("sampleRate") or 0) == 0.0
assert not missing_wav.exists()
records.append({"step": "09-missing-media", "returncode": 0, "preserved": True})
print("09-missing-media passed", flush=True)

keep = saved(call("10-keep", "init", qa / "Keep.mgd"))
rich = saved(call("10b-rich", "exec", keep, "fixture-a", "--out", qa / "Rich.mgd"))
keep_prior = keep.read_bytes()
rich_prior = rich.read_bytes()
assert "Drums" in track_names(decode_mgd(rich_prior))
sidecar = keep.with_name(keep.name + ".autosave")
sidecar.write_bytes(keep_prior[:24])
future = time.time() + 30
os.utime(sidecar, (future, future))
os.utime(keep, (future - 120, future - 120))
recover_env = env.copy()
recover_env["MAGDA_AUTOSAVE_RECOVER"] = "recover"
truncated = subprocess.run(
    [str(cli), "exec", str(keep), "--dump-json", "--out", str(qa / "Truncated-out.mgd")],
    env=recover_env,
    capture_output=True,
    text=True,
    timeout=300,
)
(qa / "10c-truncated.log").write_text(truncated.stdout + "\n" + truncated.stderr)
assert truncated.returncode != 0, truncated.stdout + truncated.stderr
assert keep.read_bytes() == keep_prior, "truncated autosave replaced the last valid save"
assert sidecar.read_bytes() == keep_prior[:24], "failed recovery deleted or rewrote the sidecar"
records.append({"step": "10c-truncated-autosave", "returncode": truncated.returncode, "preserved": True})
print("10c-truncated-autosave passed", flush=True)

sidecar.write_bytes(rich_prior)
os.utime(sidecar, (future + 30, future + 30))
locked_dir = qa / "locked"
locked_dir.mkdir(exist_ok=True)
locked = locked_dir / "locked.mgd"
locked.write_bytes(b"last-valid-destination")
locked.chmod(0o444)
blocked = subprocess.run(
    [str(cli), "exec", str(keep), "--dump-json", "--out", str(locked)],
    env=recover_env,
    capture_output=True,
    text=True,
    timeout=300,
)
locked.chmod(0o644)
(qa / "10d-blocked-save.log").write_text(blocked.stdout + "\n" + blocked.stderr)
assert blocked.returncode != 0, blocked.stdout + blocked.stderr
assert locked.read_bytes() == b"last-valid-destination"
assert keep.read_bytes() == keep_prior
assert sidecar.read_bytes() == rich_prior, "failed save deleted the recovered autosave"
records.append({"step": "10d-blocked-recovery-save", "returncode": blocked.returncode, "preserved": True})
print("10d-blocked-recovery-save passed", flush=True)

copied = saved(
    call(
        "10e-recover-copy",
        "exec",
        keep,
        "--dump-json",
        "--out",
        qa / "Recovered-copy.mgd",
        env_override=recover_env,
    )
)
assert keep.read_bytes() == keep_prior, "successful recovery rewrote the original project"
assert sidecar.read_bytes() == rich_prior, "saving a copy removed the original project's autosave"
assert "Drums" in track_names(decode_mgd(copied.read_bytes()))

saved_over = saved(
    call(
        "10f-save-over",
        "exec",
        keep,
        "--dump-json",
        "--out",
        keep,
        env_override=recover_env,
    )
)
assert "Drums" in track_names(decode_mgd(keep.read_bytes()))
assert "Drums" in track_names(decode_mgd(saved_over.read_bytes()))
assert not sidecar.exists(), "saving onto the original left the autosave sidecar behind"

out = {
    "steps": records,
    "composed": str(composed),
    "undone": str(undone),
    "redone": str(redone),
    "reopened": str(reopened),
    "recovered": str(recovered),
    "clip_counts": {
        "blank": clip_count({"tracks": blank_fp["tracks"]}),
        "composed": clip_count({"tracks": composed_fp["tracks"]}),
        "undone": clip_count({"tracks": undone_fp["tracks"]}),
        "redone": clip_count({"tracks": redone_fp["tracks"]}),
        "reopened": clip_count({"tracks": reopened_fp["tracks"]}),
        "recovered": clip_count({"tracks": recovered_fp["tracks"]}),
    },
}
(qa / "result.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
print("P1 beginner persistence gate passed", flush=True)
