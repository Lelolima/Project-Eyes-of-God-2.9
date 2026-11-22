"""Fluxos ponta a ponta do legado v2 com vídeo sintético gravado em disco."""

import json
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import security_system
from security_system import AISecuritySystem, ConfigManager


@pytest.fixture(autouse=True)
def _tmp_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def write_video(path: Path, frames: int = 15) -> Path:
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter.fourcc(*"MJPG"), 10, (160, 120))
    for i in range(frames):
        frame = np.full((120, 160, 3), 50, dtype=np.uint8)
        cv2.rectangle(frame, (5 + i * 5, 30), (35 + i * 5, 90), (220, 220, 220), -1)
        writer.write(frame)
    writer.release()
    return path


def test_video_file_stops_at_end_instead_of_looping(tmp_path):
    video = write_video(tmp_path / "v.avi")
    system = AISecuritySystem(ConfigManager("nao_existe.json"))
    analyzed = []
    system._analyze_frame = lambda frame, source: analyzed.append(source)
    started = time.monotonic()
    system.process_video_stream(str(video))
    assert time.monotonic() - started < 10  # antes: reabria o arquivo para sempre
    assert len(analyzed) == 5  # 15 frames, 1 a cada 3


def test_incident_protocol_writes_image_and_log(tmp_path):
    system = AISecuritySystem(ConfigManager("nao_existe.json"))
    frame = np.zeros((120, 160, 3), dtype=np.uint8)
    faces = [(i * 5, 10, 20, 20) for i in range(11)]
    assert system._is_suspicious_behavior(frame, faces)
    system._trigger_security_protocol(frame, faces, "cam-teste")
    images = list((tmp_path / "incidents" / "images").glob("*.jpg"))
    logs = list((tmp_path / "logs" / "incidents").glob("*.json"))
    assert len(images) == 1 and len(logs) == 1
    entry = json.loads(logs[0].read_text())[0]
    assert entry["faces_detected"] == 11 and entry["source"] == "cam-teste"
    assert "image_path" not in entry  # log não inclui caminho da imagem


def test_cleanup_removes_only_old_images(tmp_path):
    system = AISecuritySystem(ConfigManager("nao_existe.json"))
    images = tmp_path / "incidents" / "images"
    old, new = images / "antigo.jpg", images / "novo.jpg"
    old.write_bytes(b"x")
    new.write_bytes(b"x")
    past = time.time() - 40 * 86400
    os.utime(old, (past, past))
    assert system.cleanup_old_incidents(retention_days=30) == 1
    assert not old.exists() and new.exists()


def test_config_roundtrip(tmp_path):
    cm = ConfigManager(str(tmp_path / "c.json"))
    cm.config["security_level"] = "high"
    cm.save_config()
    assert ConfigManager(str(tmp_path / "c.json")).config["security_level"] == "high"


def test_main_cli_with_video_and_without_sources(tmp_path, capsys):
    video = write_video(tmp_path / "v.avi", frames=6)
    (tmp_path / "cfg.json").write_text(json.dumps({"video_sources": [str(video)]}), encoding="utf-8")
    assert security_system.main(["--config", str(tmp_path / "cfg.json")]) == 0
    assert "[OK] Sistema finalizado" in capsys.readouterr().out

    (tmp_path / "vazio.json").write_text(json.dumps({"video_sources": []}), encoding="utf-8")
    assert security_system.main(["--config", str(tmp_path / "vazio.json")]) == 2
