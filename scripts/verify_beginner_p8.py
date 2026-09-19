#!/usr/bin/env python3
"""P8 gate: missing local model is labeled honestly; live local coach when weights exist."""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
cli = pathlib.Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "build-sunroom/magda/daw/magda_cli_artefacts/Release/magda_cli"
).resolve()
qa = ROOT / "artifacts/beginner-p8"
qa.mkdir(parents=True, exist_ok=True)
home_ai = pathlib.Path.home() / "Library" / "SUNROOM" / "sunroom-ai.json"
records = []


def make_env(profile: pathlib.Path) -> dict:
    env = os.environ.copy()
    env["MAGDA_DATA_DIR"] = str(profile)
    env["MAGDA_CONFIG_FILE"] = str(profile / "config.json")
    env.setdefault("MAGDA_AUTOSAVE_RECOVER", "discard")
    return env


def run(name, env, *argv, expect_ok=True, timeout=300):
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
        {"step": name, "returncode": result.returncode, "seconds": round(time.monotonic() - start, 2)}
    )
    assert "JUCE Assertion failure" not in log, log[-600:]
    if expect_ok:
        assert result.returncode == 0, f"{name} failed\n{log[-1200:]}"
    print(name, "passed", flush=True)
    return result


absent_env = make_env(qa / "profile")
blank = None
init = run("01-init", absent_env, "init", qa / "Blank.mgd")
for line in init.stdout.splitlines():
    if line.startswith("Saved "):
        blank = pathlib.Path(line[6:].strip())
assert blank and blank.is_file()

status = run("02-coach-status", absent_env, "exec", blank, "coach-status", "--out", qa / "Status.mgd")
text = status.stdout + status.stderr
assert "not installed" in text.lower()
assert "not an AI answer" in text
assert "sk-" not in text
assert "Simplify this beat" in text

prose = run(
    "03-prose",
    absent_env,
    "exec",
    blank,
    "coach-stage",
    "Try a slower tempo. Your music is unchanged.",
    "--out",
    qa / "Prose.mgd",
    expect_ok=False,
)
assert prose.returncode != 0
assert "no SUNROOM_DSL" in (prose.stdout + prose.stderr)

dsl = 'Please consider this. SUNROOM_DSL: filter(tracks).track.group(name="All Tracks")'
starter = run("04-fixture", absent_env, "exec", blank, "fixture-a", "--out", qa / "Starter.mgd")
starter_path = [line[6:].strip() for line in starter.stdout.splitlines() if line.startswith("Saved ")][-1]
staged = run(
    "05-stage-apply",
    absent_env,
    "exec",
    starter_path,
    "coach-stage",
    dsl,
    "apply-proposal",
    "--out",
    qa / "Applied.mgd",
)
assert "Staged " in staged.stdout
assert "Applied:" in staged.stdout

missing_ask = run(
    "06-ask-missing",
    absent_env,
    "exec",
    starter_path,
    "coach-ask",
    "Explain these notes.",
    "--out",
    qa / "AskMissing.mgd",
    expect_ok=False,
)
assert "not installed" in (missing_ask.stdout + missing_ask.stderr).lower()
assert "sk-" not in (missing_ask.stdout + missing_ask.stderr)

live_status = "not run - local sunroom-ai.json was not found"
live_model = "not run - no weights loaded, no server, no API spend"
live_latency = None
live_provider = None
if home_ai.is_file():
    live_profile = qa / "live-profile"
    live_profile.mkdir(parents=True, exist_ok=True)
    shutil.copy2(home_ai, live_profile / "sunroom-ai.json")
    live_env = make_env(live_profile)
    live = run("07-live-status", live_env, "exec", starter_path, "coach-status", "--out", qa / "LiveStatus.mgd")
    live_text = live.stdout + live.stderr
    assert "Local model files are present" in live_text
    assert "not an AI answer" not in live_text
    assert "sk-" not in live_text
    live_status = "files present; weights not loaded in status"

    asked = run(
        "08-live-ask",
        live_env,
        "exec",
        starter_path,
        "select-named-clip",
        "Fixture A / Drums",
        "coach-ask",
        "Explain these notes. Do not change the song.",
        "--out",
        qa / "LiveAsk.mgd",
        timeout=180,
    )
    asked_text = asked.stdout + asked.stderr
    assert "provider this-mac-mlx" in asked_text
    assert "sk-" not in asked_text
    assert "api.openai.com" not in asked_text.lower()
    assert "latency " in asked_text
    assert "next-manual" in asked_text
    live_provider = "this-mac-mlx"
    for line in asked.stdout.splitlines():
        if line.startswith("latency "):
            live_latency = line.split(" ", 1)[1]
    live_model = "live local coach answered; no cloud fallback"

    canceled = run(
        "09-live-cancel",
        live_env,
        "exec",
        starter_path,
        "coach-ask",
        "Explain these notes.",
        "--cancel-ms",
        "50",
        "--out",
        qa / "LiveCancel.mgd",
        expect_ok=False,
        timeout=180,
    )
    canceled_text = canceled.stdout + canceled.stderr
    assert canceled.returncode != 0
    assert "sk-" not in canceled_text
    assert (
        "canceled" in canceled_text.lower()
        or "stopped" in canceled_text.lower()
        or "did not respond" in canceled_text.lower()
    )

result = {
    "phase": "P8",
    "status": "PASS",
    "records": records,
    "gates": {
        "live_model": live_model,
        "live_status": live_status,
        "live_provider": live_provider,
        "live_latency_seconds": live_latency,
        "absent_model": "coach-status says not installed and not an AI answer",
        "apply_boundary": "SUNROOM_DSL stages then apply-proposal; prose does not mutate",
        "before_after": "code path - Hear before/after only undo or redo Apply suggestion",
        "gui_audible": "not run",
        "cloud_lan": "not run - no key and no mini PC requested",
    },
}
(qa / "result.json").write_text(json.dumps(result, indent=2) + "\n")
print("P8 PASS", flush=True)
