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
assert "delta tempo" in agent_staged.stdout
assert f"{float(blank_doc['tempo']):.1f} -> 90.0" in agent_staged.stdout
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
    "undo",
    "agent-automation-stage",
    "--out",
    qa / "AgentAuto.mgd",
)
assert "Staged" in automation_staged.stdout
assert "Not applied" in automation_staged.stdout
assert "proposal yes" in automation_staged.stdout
assert "points 0" in automation_staged.stdout
assert automation_staged.stdout.index("points 0") < automation_staged.stdout.index("Applied:")
assert "Wrote" in automation_staged.stdout
assert "delta points 0 -> 2" in automation_staged.stdout
assert "Undid: Apply suggestion" in automation_staged.stdout
after_undo = automation_staged.stdout.split("Undid: Apply suggestion", 1)[1]
assert "points 0" in after_undo
assert "points 2" not in after_undo

note_staged = run(
    "01t-agent-note-stage",
    "exec",
    blank,
    "add-track",
    "audio",
    "Host",
    "select-track",
    "1",
    "agent-note-stage",
    "apply-proposal",
    "--out",
    qa / "AgentNote.mgd",
)
assert "Staged" in note_staged.stdout
assert "Not applied" in note_staged.stdout
assert "proposal yes" in note_staged.stdout
assert "clips 0" in note_staged.stdout
assert note_staged.stdout.index("clips 0") < note_staged.stdout.index("Applied:")
applied_tail = note_staged.stdout[note_staged.stdout.index("Applied:") :]
assert "clip none" not in applied_tail
assert "clip " in applied_tail

named = run(
    "01u-undo-names",
    "exec",
    blank,
    "add-track",
    "audio",
    "Host",
    "select-track",
    "1",
    "agent-dsl-stage",
    "project.set(bpm=90)",
    "apply-proposal",
    "agent-automation-stage",
    "apply-proposal",
    "undo",
    "undo",
    "--out",
    qa / "NamedUndo.mgd",
)
undid = [line for line in named.stdout.splitlines() if line.startswith("Undid:")]
assert len(undid) == 2, named.stdout[-800:]
assert undid[0] != undid[1]
assert "Apply suggestion" in undid[0] and "Apply suggestion" in undid[1]
assert "track volume" in undid[0]
assert "project.set(bpm=90)" in undid[1]
deltas = [line for line in named.stdout.splitlines() if line.startswith("delta ")]
assert any("tempo" in line for line in deltas)
assert any("points" in line for line in deltas)
assert next(line for line in deltas if "tempo" in line) != next(
    line for line in deltas if "points" in line
)

cleared = run(
    "01v-agent-automation-clear",
    "exec",
    blank,
    "add-track",
    "audio",
    "Host",
    "select-track",
    "1",
    "agent-automation-stage",
    "apply-proposal",
    "agent-automation-clear",
    "apply-proposal",
    "undo",
    "agent-automation-clear",
    "--out",
    qa / "AgentClear.mgd",
)
assert "Staged" in cleared.stdout
assert "Not applied" in cleared.stdout
assert "Cleared lane." in cleared.stdout
assert "delta points 2 -> 0" in cleared.stdout
assert "Undid: Apply suggestion" in cleared.stdout
assert "clear track volume" in cleared.stdout
after_clear_undo = cleared.stdout.split("Undid: Apply suggestion", 1)[1]
assert "points 2" in after_clear_undo

views = run(
    "01w-conductor-views",
    "exec",
    blank,
    "agent-dsl-stage",
    "project.set(bpm=90)",
    "conductor-status",
    "conductor-view",
    "session",
    "conductor-status",
    "conductor-view",
    "arrange",
    "conductor-status",
    "conductor-view",
    "mix",
    "conductor-status",
    "conductor-view",
    "create",
    "conductor-status",
    "new-project",
    "conductor-status",
    "--out",
    qa / "ConductorViews.mgd",
)
statuses = []
block = []
for line in views.stdout.splitlines():
    if line.startswith("session "):
        if block:
            statuses.append(block)
        block = [line]
    elif block and (
        line.startswith("conversation ")
        or line.startswith("view ")
        or line.startswith("proposal ")
        or line.startswith("proposal-id ")
        or line.startswith("plan ")
    ):
        block.append(line)
if block:
    statuses.append(block)
assert len(statuses) >= 6, views.stdout[-1200:]
first = "\n".join(statuses[0])
assert "proposal yes" in first
assert "proposal-id 0" not in first
conversation = next(line for line in statuses[0] if line.startswith("conversation "))
proposal = next(line for line in statuses[0] if line.startswith("proposal-id "))
plan = next(line for line in statuses[0] if line.startswith("plan "))
assert plan != "plan none"
for status in statuses[1:5]:
    text = "\n".join(status)
    assert conversation in text
    assert proposal in text
    assert "proposal yes" in text
assert "view session" in "\n".join(statuses[1])
assert "view arrange" in "\n".join(statuses[2])
assert "view mix" in "\n".join(statuses[3])
assert "view create" in "\n".join(statuses[4])
last = "\n".join(statuses[-1])
assert "proposal no" in last
assert conversation not in last

explained = run(
    "01x-settings-recipe",
    "exec",
    blank,
    "coach-explain",
    "These notes sit in A minor.",
    "settings-recipe",
    "1",
    "9",
    "96",
    "32",
    "apply-settings",
    "--out",
    qa / "SettingsOnly.mgd",
)
assert "kind explanation" in explained.stdout
assert explained.stdout.index("kind explanation") < explained.stdout.index("kind settings")
assert "kind settings" in explained.stdout
assert "Settings applied. No tracks were created." in explained.stdout
assert "proposal no" in explained.stdout
assert "tracks 0" in explained.stdout
assert "settings-tempo 96.0" in explained.stdout
settings_doc = dump_project("01x-dump", saved(explained.stdout))
assert names(settings_doc) == names(blank_doc)
assert abs(float(settings_doc["tempo"]) - float(blank_doc["tempo"])) < 0.01

clear_out(qa / "Shell.mgd")
shell = run(
    "01y-refuse-shell",
    "exec",
    blank,
    "coach-stage",
    'SUNROOM_DSL: system("echo hi")',
    "--out",
    qa / "Shell.mgd",
    expect_ok=False,
)
shell_log = shell.stdout + "\n" + shell.stderr
assert shell.returncode != 0
assert "Refused" in shell_log
assert "shell or code" in shell_log.lower()
assert "music is unchanged" in shell_log.lower()
assert "proposal no" in shell.stdout
assert "Staged " not in shell.stdout
assert not (qa / "Shell.mgd").exists() and not (qa / "Shell").exists()
shell_doc = dump_project("01y-dump", blank)
assert names(shell_doc) == names(blank_doc)
assert abs(float(shell_doc["tempo"]) - float(blank_doc["tempo"])) < 0.01

clear_out(qa / "Ghost.mgd")
ghost = run(
    "01z-refuse-missing-target",
    "exec",
    blank,
    "coach-stage",
    'SUNROOM_DSL: filter(tracks, track.name == "Ghost").track.set(mute=true)',
    "apply-proposal",
    "--out",
    qa / "Ghost.mgd",
    expect_ok=False,
)
ghost_log = ghost.stdout + "\n" + ghost.stderr
assert ghost.returncode != 0
assert "Refused" in ghost_log
assert "target track does not exist" in ghost_log.lower()
assert "music is unchanged" in ghost_log.lower()
assert "proposal no" in ghost.stdout
assert "Applied:" not in ghost.stdout
assert not (qa / "Ghost.mgd").exists() and not (qa / "Ghost").exists()
ghost_doc = dump_project("01z-dump", blank)
assert names(ghost_doc) == names(blank_doc)
assert abs(float(ghost_doc["tempo"]) - float(blank_doc["tempo"])) < 0.01

clear_out(qa / "MissingId.mgd")
missing_id = run(
    "01z2-refuse-missing-id",
    "exec",
    blank,
    "propose-dsl",
    "track(id=99).track.set(mute=true)",
    "apply-proposal",
    "--out",
    qa / "MissingId.mgd",
    expect_ok=False,
)
missing_log = missing_id.stdout + "\n" + missing_id.stderr
assert missing_id.returncode != 0
assert "Refused" in missing_log
assert "target track id is missing" in missing_log.lower()
assert "music is unchanged" in missing_log.lower()
assert "Applied:" not in missing_id.stdout
assert not (qa / "MissingId.mgd").exists() and not (qa / "MissingId").exists()
missing_doc = dump_project("01z2-dump", blank)
assert names(missing_doc) == names(blank_doc)
assert abs(float(missing_doc["tempo"]) - float(blank_doc["tempo"])) < 0.01

clear_out(qa / "Range.mgd")
ranged = run(
    "01aa-refuse-range",
    "exec",
    blank,
    "coach-stage",
    "SUNROOM_DSL: project.set(bpm=2000)",
    "apply-proposal",
    "--out",
    qa / "Range.mgd",
    expect_ok=False,
)
range_log = ranged.stdout + "\n" + ranged.stderr
assert ranged.returncode != 0
assert "Refused" in range_log
assert "supported range" in range_log.lower()
assert "music is unchanged" in range_log.lower()
assert "proposal no" in ranged.stdout
assert "Applied:" not in ranged.stdout
assert not (qa / "Range.mgd").exists() and not (qa / "Range").exists()
range_doc = dump_project("01aa-dump", blank)
assert names(range_doc) == names(blank_doc)
assert abs(float(range_doc["tempo"]) - float(blank_doc["tempo"])) < 0.01

clear_out(qa / "Device.mgd")
device = run(
    "01ab-refuse-device",
    "exec",
    blank,
    "coach-stage",
    'SUNROOM_DSL: track(name="Lead").fx.add(name="NotADevice")',
    "apply-proposal",
    "--out",
    qa / "Device.mgd",
    expect_ok=False,
)
device_log = device.stdout + "\n" + device.stderr
assert device.returncode != 0
assert "Refused" in device_log
assert "device is not supported" in device_log.lower()
assert "music is unchanged" in device_log.lower()
assert "proposal no" in device.stdout
assert "Applied:" not in device.stdout
assert not (qa / "Device.mgd").exists() and not (qa / "Device").exists()
device_doc = dump_project("01ab-dump", blank)
assert names(device_doc) == names(blank_doc)
assert "Lead" not in names(device_doc)

clear_out(qa / "Asset.mgd")
asset = run(
    "01ac-refuse-asset",
    "exec",
    blank,
    "coach-stage",
    'SUNROOM_DSL: track(name="Sound").clip.new(bar=1, length_bars=4, file="GhostTake.wav")',
    "apply-proposal",
    "--out",
    qa / "Asset.mgd",
    expect_ok=False,
)
asset_log = asset.stdout + "\n" + asset.stderr
assert asset.returncode != 0
assert "Refused" in asset_log
assert "sound was not found" in asset_log.lower()
assert "music is unchanged" in asset_log.lower()
assert "proposal no" in asset.stdout
assert "Applied:" not in asset.stdout
assert not (qa / "Asset.mgd").exists() and not (qa / "Asset").exists()
asset_doc = dump_project("01ac-dump", blank)
assert names(asset_doc) == names(blank_doc)
assert "Sound" not in names(asset_doc)

clear_out(qa / "MultiDevice.mgd")
multi_device = run(
    "01ad-refuse-multi-device",
    "exec",
    blank,
    "coach-stage",
    'SUNROOM_DSL: project.set(bpm=90)\nSUNROOM_DSL: track(name="Lead").fx.add(name="NotADevice")',
    "apply-proposal",
    "--out",
    qa / "MultiDevice.mgd",
    expect_ok=False,
)
multi_device_log = multi_device.stdout + "\n" + multi_device.stderr
assert multi_device.returncode != 0
assert "Refused" in multi_device_log
assert "device is not supported" in multi_device_log.lower()
assert "music is unchanged" in multi_device_log.lower()
assert "proposal no" in multi_device.stdout
assert "Applied:" not in multi_device.stdout
assert "Staged " not in multi_device.stdout
assert not (qa / "MultiDevice.mgd").exists() and not (qa / "MultiDevice").exists()
multi_device_doc = dump_project("01ad-dump", blank)
assert names(multi_device_doc) == names(blank_doc)
assert "Lead" not in names(multi_device_doc)
assert abs(float(multi_device_doc["tempo"]) - float(blank_doc["tempo"])) < 0.01

clear_out(qa / "MultiStep.mgd")
multi_step = run(
    "01ae-refuse-multi-step",
    "exec",
    blank,
    "coach-stage",
    "SUNROOM_DSL: project.set(bpm=90)\nSUNROOM_DSL: please mute the ghost",
    "apply-proposal",
    "--out",
    qa / "MultiStep.mgd",
    expect_ok=False,
)
multi_step_log = multi_step.stdout + "\n" + multi_step.stderr
assert multi_step.returncode != 0
assert "Refused" in multi_step_log
assert "one step is not a song action" in multi_step_log.lower()
assert "music is unchanged" in multi_step_log.lower()
assert "proposal no" in multi_step.stdout
assert "Applied:" not in multi_step.stdout
assert not (qa / "MultiStep.mgd").exists() and not (qa / "MultiStep").exists()
multi_step_doc = dump_project("01ae-dump", blank)
assert names(multi_step_doc) == names(blank_doc)
assert abs(float(multi_step_doc["tempo"]) - float(blank_doc["tempo"])) < 0.01

clear_out(qa / "LateCoach.mgd")
late_coach = run(
    "01af-late-coach",
    "exec",
    blank,
    "coach-begin",
    "coach-begin",
    "coach-arrive",
    "1",
    "SUNROOM_DSL: project.set(bpm=90)",
    "apply-proposal",
    "--out",
    qa / "LateCoach.mgd",
    expect_ok=False,
)
late_log = late_coach.stdout + "\n" + late_coach.stderr
assert late_coach.returncode != 0
assert "late coach result" in late_log.lower()
assert "proposal no" in late_coach.stdout
assert "Applied:" not in late_coach.stdout
assert not (qa / "LateCoach.mgd").exists() and not (qa / "LateCoach").exists()
late_doc = dump_project("01af-dump", blank)
assert abs(float(late_doc["tempo"]) - float(blank_doc["tempo"])) < 0.01

clear_out(qa / "CanceledCoach.mgd")
canceled_coach = run(
    "01ag-canceled-coach",
    "exec",
    blank,
    "coach-begin",
    "coach-cancel",
    "coach-arrive",
    "1",
    "SUNROOM_DSL: project.set(bpm=90)",
    "apply-proposal",
    "--out",
    qa / "CanceledCoach.mgd",
    expect_ok=False,
)
canceled_log = canceled_coach.stdout + "\n" + canceled_coach.stderr
assert canceled_coach.returncode != 0
assert "canceled" in canceled_log.lower()
assert "proposal no" in canceled_coach.stdout
assert "Applied:" not in canceled_coach.stdout
assert not (qa / "CanceledCoach.mgd").exists() and not (qa / "CanceledCoach").exists()
canceled_doc = dump_project("01ag-dump", blank)
assert abs(float(canceled_doc["tempo"]) - float(blank_doc["tempo"])) < 0.01

clear_out(qa / "SaveAs.mgd")
clear_out(qa / "SaveAsApply.mgd")
save_as = run(
    "01ah-save-as",
    "exec",
    blank,
    "propose-dsl",
    "project.set(bpm=90)",
    "save-as",
    qa / "SaveAs.mgd",
    "apply-proposal",
    "--out",
    qa / "SaveAsApply.mgd",
    expect_ok=False,
)
save_as_log = save_as.stdout + "\n" + save_as.stderr
assert save_as.returncode != 0
assert "project changed" in save_as_log.lower()
assert "Applied:" not in save_as.stdout
assert not (qa / "SaveAsApply.mgd").exists() and not (qa / "SaveAsApply").exists()
save_as_doc = dump_project("01ah-dump", blank)
assert abs(float(save_as_doc["tempo"]) - float(blank_doc["tempo"])) < 0.01

clear_out(qa / "Renamed.mgd")
renamed = run(
    "01ai-renamed-target",
    "exec",
    blank,
    "add-track",
    "audio",
    "Ghost",
    "propose-dsl",
    'filter(tracks, track.name == "Ghost").track.set(mute=true)',
    "rename-track",
    "Ghost",
    "Beat",
    "apply-proposal",
    "--out",
    qa / "Renamed.mgd",
    expect_ok=False,
)
renamed_log = renamed.stdout + "\n" + renamed.stderr
assert renamed.returncode != 0
assert "Refused" in renamed_log
assert "Applied:" not in renamed.stdout
assert not (qa / "Renamed.mgd").exists() and not (qa / "Renamed").exists()
renamed_doc = dump_project("01ai-dump", blank)
assert names(renamed_doc) == names(blank_doc)

clear_out(qa / "Deleted.mgd")
deleted = run(
    "01aj-deleted-target",
    "exec",
    blank,
    "add-track",
    "audio",
    "Ghost",
    "propose-dsl",
    'filter(tracks, track.name == "Ghost").track.set(mute=true)',
    "delete-named-track",
    "Ghost",
    "apply-proposal",
    "--out",
    qa / "Deleted.mgd",
    expect_ok=False,
)
deleted_log = deleted.stdout + "\n" + deleted.stderr
assert deleted.returncode != 0
assert "Refused" in deleted_log
assert "Applied:" not in deleted.stdout
assert not (qa / "Deleted.mgd").exists() and not (qa / "Deleted").exists()
deleted_doc = dump_project("01aj-dump", blank)
assert names(deleted_doc) == names(blank_doc)

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
