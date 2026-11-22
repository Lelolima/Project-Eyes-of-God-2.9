#!/usr/bin/env python3
"""Testes de regressão da auditoria 2026-11-22 (dados sintéticos, sem câmera)."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import security_system  # noqa: E402
from security_system import AISecuritySystem, ConfigManager, SecureDataHandler  # noqa: E402


def _system():
    return AISecuritySystem(ConfigManager("config_inexistente.json"))


class TestOpenCV(unittest.TestCase):
    def test_haar_cascade_available(self):
        """OpenCV 5 removeu CascadeClassifier; requirements agora fixa <5."""
        self.assertTrue(hasattr(cv2, "CascadeClassifier"))
        system = _system()
        self.assertIsNotNone(system.face_detection_model)
        self.assertFalse(system.face_detection_model.empty())

    def test_detect_faces_on_synthetic_frame_returns_nothing(self):
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        self.assertEqual(len(_system()._detect_faces(frame)), 0)


class TestVideoSources(unittest.TestCase):
    def test_rtsp_public_host_accepted(self):
        self.assertTrue(_system()._validate_video_source("rtsp://camera.example.com:554/stream"))

    def test_rtsp_private_ip_follows_ssrf_policy(self):
        self.assertFalse(_system()._validate_video_source("rtsp://10.0.0.5:554/stream"))

    def test_webcam_index_is_passed_as_int(self):
        system = _system()
        fake_cap = MagicMock()
        fake_cap.isOpened.return_value = False
        with patch.object(security_system.cv2, "VideoCapture", return_value=fake_cap) as vc:
            system.process_video_stream("0")
        vc.assert_called_once_with(0)


class TestNotifications(unittest.TestCase):
    def test_no_channel_means_nothing_sent(self):
        system = _system()
        system.config_manager.config["notification_emails"] = ["a@example.com"]
        system.config_manager.config["notification_webhook"] = None
        self.assertEqual(system._notify_authorities({"id": "x"}), [])

    def test_webhook_success_is_reported(self):
        system = _system()
        system.config_manager.config["notification_emails"] = []
        system.config_manager.config["notification_webhook"] = "https://hooks.example.com/x"
        with patch.object(security_system.requests, "post") as post:
            post.return_value.raise_for_status.return_value = None
            self.assertEqual(system._notify_authorities({"id": "x"}), ["webhook"])

    def test_webhook_failure_is_not_reported_as_sent(self):
        system = _system()
        system.config_manager.config["notification_emails"] = []
        system.config_manager.config["notification_webhook"] = "https://hooks.example.com/x"
        with patch.object(security_system.requests, "post",
                          side_effect=security_system.requests.ConnectionError("down")):
            self.assertEqual(system._notify_authorities({"id": "x"}), [])


class TestHashSalt(unittest.TestCase):
    def test_salt_from_env(self):
        default = SecureDataHandler.hash_sensitive_data("abc")
        with patch.dict("os.environ", {"SECURITY_HASH_SALT": "outro"}):
            self.assertNotEqual(SecureDataHandler.hash_sensitive_data("abc"), default)


if __name__ == "__main__":
    unittest.main()
