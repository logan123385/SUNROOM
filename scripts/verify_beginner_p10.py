#!/usr/bin/env python3
"""P10 gate: beginner export uses Arrangement only, with empty/cancel/overwrite checks."""
import array
import json
import os
import pathlib
import subprocess
import sys
import time
import wave

ROOT = pathlib.Path(__file__).resolve().parents[1]
cli = pathlib.Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "build-sunroom/magda/daw/magda_cli_artefacts/Release/magda_cli"
).resolve()
qa = ROOT / "artifacts/beginner-p10"
qa.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
env["MAGDA_DATA_DIR"] = str(qa / "profile")
env["MAGDA_CONFIG_FILE"] = str(qa / "profile/config.json")
env.setdefault("MAGDA_AUTOSAVE_RECOVER", "discard")
records = []


def call(name, *argv, expect_ok=True, timeout=300):
    start = time.monotonic()
    result = subprocess.run(
        [str(cli), *map(str, argv)],
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
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
    assert "JUCE Assertion failure" not in log, log[-600:]
    if expect_ok:
        assert result.returncode == 0, f"{name} failed\n{log[-1200:]}"
    print(name, "passed", flush=True)
    return result


def saved(output):
    lines = [line[6:].strip() for line in output.splitlines() if line.startswith("Saved ")]
    assert lines, output[-500:]
    path = pathlib.Path(lines[-1])
    assert path.is_file()
    return path


def pcm_peak(path: pathlib.Path) -> int:
    with wave.open(str(path)) as rendered:
        frames = rendered.readframes(rendered.getnframes())
        width = rendered.getsampwidth()
        duration = rendered.getnframes() / float(rendered.getframerate() or 1)
    if width == 2:
        samples = array.array("h")
        samples.frombytes(frames)
        return max((abs(sample) for sample in samples), default=0), duration, rendered
    raise AssertionError(f"unsupported sample width {width}")


blank = saved(call("01-init", "init", qa / "Blank.mgd").stdout)
empty = call(
    "02-empty",
    "export-song",
    blank,
    "--wav",
    qa / "empty.wav",
    expect_ok=False,
)
empty_text = empty.stdout + empty.stderr
assert "arrangement is empty" in empty_text
assert "Session loop was not exported" in empty_text
assert not (qa / "empty.wav").exists()

fixture_b = saved(call("03-fixture-b", "exec", blank, "fixture-b", "--out", qa / "FixtureB.mgd").stdout)
preview_b = call("04-preview-b", "export-song", fixture_b, "--wav", qa / "fixture-b.wav", "--preview")
preview_text = preview_b.stdout + preview_b.stderr
assert "source arrangement" in preview_text
assert "duration 76.80s" in preview_text
assert not (qa / "fixture-b.wav").exists()

fixture_c = saved(call("05-fixture-c", "exec", blank, "fixture-c", "--out", qa / "FixtureC.mgd").stdout)
wav_c = qa / "fixture-c.wav"
exported = call("06-export-c", "export-song", fixture_c, "--wav", wav_c)
export_text = exported.stdout + exported.stderr
assert "source arrangement" in export_text
assert "Exported " in export_text
assert "reveal " in export_text
assert wav_c.is_file()
with wave.open(str(wav_c)) as rendered:
    assert rendered.getnchannels() == 2
    assert rendered.getframerate() == 44100
    duration = rendered.getnframes() / float(rendered.getframerate())
    width = rendered.getsampwidth()
    frames = rendered.readframes(rendered.getnframes())
assert 18.5 <= duration <= 20.5, duration
if width == 2:
    samples = array.array("h")
    samples.frombytes(frames)
    peak = max((abs(sample) for sample in samples), default=0)
else:
    raise AssertionError(f"unsupported sample width {width}")
assert peak > 1000, peak

marker = qa / "existing.wav"
marker.write_bytes(b"not-a-wav")
blocked = call(
    "07-overwrite-blocked",
    "export-song",
    fixture_c,
    "--wav",
    marker,
    expect_ok=False,
)
assert "already exists" in (blocked.stdout + blocked.stderr)
assert marker.read_bytes() == b"not-a-wav"

replaced = call("08-overwrite", "export-song", fixture_c, "--wav", marker, "--overwrite")
assert "Exported " in replaced.stdout
assert marker.is_file()
assert marker.read_bytes()[:4] == b"RIFF"

keep = qa / "keep.wav"
keep.write_bytes(b"keep-me")
canceled = call(
    "09-cancel",
    "export-song",
    fixture_c,
    "--wav",
    keep,
    "--overwrite",
    "--cancel",
    expect_ok=False,
)
assert "Export canceled" in (canceled.stdout + canceled.stderr)
assert keep.read_bytes() == b"keep-me"
assert not list(qa.glob("keep.wav.part"))

blocker = qa / "not-a-dir.txt"
blocker.write_text("file\n")
unwritable = call(
    "10-unwritable",
    "export-song",
    fixture_c,
    "--wav",
    blocker / "song.wav",
    expect_ok=False,
)
assert "not writable" in (unwritable.stdout + unwritable.stderr)

out = {
    "phase": "P10",
    "status": "PASS",
    "records": records,
    "gates": {
        "empty_arrangement": "refused; Session loop not exported",
        "fixture_b_duration": "preview 76.80s for 32 bars at 100 BPM",
        "fixture_c_source": "arrangement WAV 8 bars, stereo 44100, not silent",
        "overwrite": "refused without flag; replaced with --overwrite",
        "cancel": "destination bytes unchanged",
        "unwritable": "file-as-folder destination refused",
        "gui_reveal": "not run - CLI printed reveal path only",
    },
}
(qa / "result.json").write_text(json.dumps(out, indent=2) + "\n")
print("P10 PASS", flush=True)
