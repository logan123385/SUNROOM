#!/usr/bin/env python3
"""P7 gate: staged DSL proposal. Mocks exercise the real interpreter; not a live model."""
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
qa = ROOT / "artifacts/beginner-p7"
qa.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
env["MAGDA_DATA_DIR"] = str(qa / "profile")
env["MAGDA_CONFIG_FILE"] = str(qa / "profile/config.json")
env.setdefault("MAGDA_AUTOSAVE_RECOVER", "discard")
records = []
DSL = 'filter(tracks).track.group(name="All Tracks")'


def clear_out(path):
    path = pathlib.Path(path)
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()
    stem = path.with_suffix("")
    if stem != path and stem.is_dir():
        shutil.rmtree(stem)


def run(name, *argv, expect_ok=True):
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
    assert "JUCE Assertion failure" not in log, log[-800:]
    if expect_ok:
        assert result.returncode == 0, f"{name} failed\n{log[-1500:]}"
    print(name, "passed", flush=True)
    return result


def saved(output):
    lines = [line[6:].strip() for line in output.splitlines() if line.startswith("Saved ")]
    assert lines, output[-500:]
    path = pathlib.Path(lines[-1])
    assert path.is_file()
    return path


def dump_project(name: str, project: pathlib.Path) -> dict:
    out = qa / f"{name}-dump.mgd"
    result = run(name, "exec", project, "--dump-json", "--out", out)
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("{") and '"tracks"' in line:
            return json.loads(line)
    raise AssertionError(f"{name}: missing dump-json")


def names(doc):
    return {t.get("name") for t in doc.get("tracks") or []}


blank = saved(run("01-init", "init", qa / "Blank.mgd").stdout)
blank_doc = dump_project("01b-dump", blank)
tempo_restored = run(
    "01c-remote-tempo",
    "exec",
    blank,
    "set-tempo",
    "90",
    "undo",
    "--out",
    qa / "TempoRestored.mgd",
)
assert "tempo 90.0" in tempo_restored.stdout
assert "undo Set project tempo" in tempo_restored.stdout
assert "Undid: Set project tempo" in tempo_restored.stdout
restored_doc = dump_project("01d-dump", saved(tempo_restored.stdout))
assert abs(float(restored_doc["tempo"]) - float(blank_doc["tempo"])) < 0.01

signature_restored = run(
    "01e-remote-signature",
    "exec",
    blank,
    "set-time-signature",
    "7",
    "8",
    "undo",
    "--out",
    qa / "SignatureRestored.mgd",
)
assert "signature 7/8" in signature_restored.stdout
assert "undo Set time signature" in signature_restored.stdout
assert "Undid: Set time signature" in signature_restored.stdout
signature_doc = dump_project("01f-dump", saved(signature_restored.stdout))
assert signature_doc["timeSignatureNumerator"] == blank_doc["timeSignatureNumerator"]
assert signature_doc["timeSignatureDenominator"] == blank_doc["timeSignatureDenominator"]

osc_restored = run(
    "01g-osc-tempo",
    "exec",
    blank,
    "osc-tempo",
    "90",
    "undo",
    "--out",
    qa / "OscTempo.mgd",
)
assert "osc-tempo 90.0" in osc_restored.stdout
assert "undo Set project tempo" in osc_restored.stdout
assert "Undid: Set project tempo" in osc_restored.stdout
assert "Proposal" not in osc_restored.stdout
osc_doc = dump_project("01h-dump", saved(osc_restored.stdout))
assert abs(float(osc_doc["tempo"]) - float(blank_doc["tempo"])) < 0.01

timeline_restored = run(
    "01i-timeline-tempo",
    "exec",
    blank,
    "timeline-tempo",
    "90",
    "undo",
    "--out",
    qa / "TimelineTempo.mgd",
)
assert "timeline-tempo 90.0" in timeline_restored.stdout
assert "undo Set project tempo" in timeline_restored.stdout
assert "Undid: Set project tempo" in timeline_restored.stdout
timeline_doc = dump_project("01j-dump", saved(timeline_restored.stdout))
assert abs(float(timeline_doc["tempo"]) - float(blank_doc["tempo"])) < 0.01

timeline_sig = run(
    "01k-timeline-signature",
    "exec",
    blank,
    "timeline-signature",
    "7",
    "8",
    "undo",
    "--out",
    qa / "TimelineSignature.mgd",
)
assert "timeline-signature 7/8" in timeline_sig.stdout
assert "undo Set time signature" in timeline_sig.stdout
assert "Undid: Set time signature" in timeline_sig.stdout
timeline_sig_doc = dump_project("01l-dump", saved(timeline_sig.stdout))
assert timeline_sig_doc["timeSignatureNumerator"] == blank_doc["timeSignatureNumerator"]
assert timeline_sig_doc["timeSignatureDenominator"] == blank_doc["timeSignatureDenominator"]

direct = run(
    "01m-direct-dsl",
    "exec",
    blank,
    "direct-dsl",
    "project.set(bpm=90)",
    "undo",
    "--out",
    qa / "DirectDsl.mgd",
)
assert "direct" in direct.stdout
assert "proposal no" in direct.stdout
assert "tempo 90.0" in direct.stdout
assert "Proposal " not in direct.stdout
assert "Undid: Set project tempo" in direct.stdout
direct_doc = dump_project("01n-dump", saved(direct.stdout))
assert abs(float(direct_doc["tempo"]) - float(blank_doc["tempo"])) < 0.01

agent_staged = run(
    "01o-agent-dsl-stage",
    "exec",
    blank,
    "agent-dsl-stage",
    "project.set(bpm=90)",
    "apply-proposal",
    "undo",
    "--out",
    qa / "AgentDsl.mgd",
)
assert "Staged" in agent_staged.stdout
assert "Not applied" in agent_staged.stdout
assert "proposal yes" in agent_staged.stdout
assert f"tempo {float(blank_doc['tempo']):.1f}" in agent_staged.stdout
assert "Applied:" in agent_staged.stdout
assert "Undid: Apply suggestion" in agent_staged.stdout
agent_doc = dump_project("01p-dump", saved(agent_staged.stdout))
assert abs(float(agent_doc["tempo"]) - float(blank_doc["tempo"])) < 0.01

music_staged = run(
    "01q-agent-music-stage",
    "exec",
    blank,
    "agent-music-stage",
    "MusicStage",
    "apply-proposal",
    "undo",
    "--out",
    qa / "AgentMusic.mgd",
)
assert "Staged" in music_staged.stdout
assert "Not applied" in music_staged.stdout
assert "proposal yes" in music_staged.stdout
assert "track no" in music_staged.stdout
assert "Applied:" in music_staged.stdout
assert "Created track 'MusicStage'" in music_staged.stdout
assert "Undid: Apply suggestion" in music_staged.stdout
music_doc = dump_project("01r-dump", saved(music_staged.stdout))
assert names(music_doc) == names(blank_doc)

automation_staged = run(
    "01s-agent-automation-stage",
    "exec",
    blank,
    "add-track",
    "audio",
    "Host",
    "select-track",
    "1",
    "agent-automation-stage",
    "apply-proposal",
    "--out",
    qa / "AgentAuto.mgd",
)
assert "Staged" in automation_staged.stdout
assert "Not applied" in automation_staged.stdout
assert "proposal yes" in automation_staged.stdout
assert "points 0" in automation_staged.stdout
assert automation_staged.stdout.index("points 0") < automation_staged.stdout.index("Applied:")
assert "Wrote" in automation_staged.stdout

starter = saved(run("02-fixture-a", "exec", blank, "fixture-a", "--out", qa / "Starter.mgd").stdout)
starter_bytes = starter.read_bytes()
rack = run(
    "02b-rack-bypass",
    "exec",
    starter,
    "rack-bypass-undo",
    "--out",
    qa / "RackBypass.mgd",
)
assert "bypass 1" in rack.stdout
assert "undo Set rack bypass" in rack.stdout
assert "restored 0" in rack.stdout
removed = run(
    "02c-rack-remove",
    "exec",
    starter,
    "rack-remove-undo",
    "--out",
    qa / "RackRemoved.mgd",
)
assert "removed undo Remove rack" in removed.stdout
assert "restored Remove Test" in removed.stdout
created = run(
    "02d-rack-create",
    "exec",
    starter,
    "rack-create-undo",
    "--out",
    qa / "RackCreated.mgd",
)
assert "created Create Test undo Add rack" in created.stdout
assert "undo removed" in created.stdout

applied = run(
    "03-apply",
    "exec",
    starter,
    "propose-dsl",
    DSL,
    "apply-proposal",
    "--out",
    qa / "Grouped.mgd",
)
assert "Proposal " in applied.stdout
assert "Applied:" in applied.stdout
gdoc = dump_project("03b-dump", saved(applied.stdout))
assert "All Tracks" in names(gdoc)
assert "Drums" in names(gdoc)

undone = run(
    "04-undo",
    "exec",
    starter,
    "propose-dsl",
    DSL,
    "apply-proposal",
    "undo",
    "--out",
    qa / "Ungrouped.mgd",
)
assert "Apply suggestion" in undone.stdout
udoc = dump_project("04b-dump", saved(undone.stdout))
assert "All Tracks" not in names(udoc)
assert "Drums" in names(udoc)

clear_out(qa / "Invalid.mgd")
bad = run(
    "05-invalid",
    "exec",
    starter,
    "propose-dsl",
    "not dsl",
    "apply-proposal",
    "--out",
    qa / "Invalid.mgd",
    expect_ok=False,
)
assert bad.returncode != 0
assert "Refused" in (bad.stdout + bad.stderr)
assert not (qa / "Invalid.mgd").exists() and not (qa / "Invalid").exists()

clear_out(qa / "Stale.mgd")
stale = run(
    "06-stale",
    "exec",
    starter,
    "propose-dsl",
    DSL,
    "bump-revision",
    "apply-proposal",
    "--out",
    qa / "Stale.mgd",
    expect_ok=False,
)
assert stale.returncode != 0
assert "project changed" in (stale.stdout + stale.stderr).lower()
assert not (qa / "Stale.mgd").exists() and not (qa / "Stale").exists()

clear_out(qa / "Selection.mgd")
sel = run(
    "07-selection",
    "exec",
    starter,
    "propose-dsl",
    DSL,
    "select-track",
    "99",
    "apply-proposal",
    "--out",
    qa / "Selection.mgd",
    expect_ok=False,
)
assert sel.returncode != 0
assert "selection changed" in (sel.stdout + sel.stderr).lower()
assert not (qa / "Selection.mgd").exists() and not (qa / "Selection").exists()

clear_out(qa / "Canceled.mgd")
cancel = run(
    "08-cancel",
    "exec",
    starter,
    "propose-dsl",
    DSL,
    "apply-proposal",
    "cancelled",
    "--out",
    qa / "Canceled.mgd",
    expect_ok=False,
)
assert cancel.returncode != 0
assert "canceled" in (cancel.stdout + cancel.stderr).lower()
assert not (qa / "Canceled.mgd").exists() and not (qa / "Canceled").exists()

clear_out(qa / "Twice.mgd")
twice = run(
    "09-double",
    "exec",
    starter,
    "propose-dsl",
    DSL,
    "apply-proposal",
    "apply-proposal",
    "--out",
    qa / "Twice.mgd",
    expect_ok=False,
)
assert twice.returncode != 0
assert "already applied" in (twice.stdout + twice.stderr).lower()
assert not (qa / "Twice.mgd").exists() and not (qa / "Twice").exists()
assert starter.read_bytes() == starter_bytes

result = {
    "phase": "P7",
    "status": "PASS",
    "records": records,
    "gates": {
        "live_model": "not run - mocks only; P8 owns a real local model",
        "console_still_applies_immediately": "unchanged; beginner CLI stages then applies",
        "mcp_grants": "untouched - model text is not a scope grant",
    },
}
(qa / "result.json").write_text(json.dumps(result, indent=2) + "\n")
print("P7 PASS", flush=True)
