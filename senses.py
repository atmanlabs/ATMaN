"""Camera Sensory Subsystem for EXO Live (His First Eye).

Design Rules (Strict / Non-Negotiable):
1. Owner-toggled only, default OFF. `camera_enabled: false` in `config.yaml`.
   EXO cannot enable it himself -- attempting to is a permission fence violation.
2. Frames never leave the box. Processed entirely in volatile memory, discarded immediately.
   Only text descriptions enter the event log. Zero raw frames written to disk.
3. The existing fence already blocks network egress -- camera frames are never transmittable.
4. Rule-based backend (default): motion/presence detection via frame differencing only.
   Honest limit: the rule-based brain detects, it does not see.
5. Vision path: optional local vision model via Ollama (e.g. qwen2.5vl:7b).
   Model never stores frames.
6. Sensory descriptions flow as ordinary observations -> significant_events -> sleep -> sweep -> guardian.
"""
import base64
import json
from pathlib import Path
import time
from typing import Any, Dict, Optional, Tuple
import urllib.error
import urllib.request

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from config import Config, PermissionFenceError

HERE = Path(__file__).resolve().parent


class CameraSense:
    """The local, in-memory camera sensory system."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._last_gray_frame = None
        self._last_capture_time = 0.0

    @property
    def is_enabled(self) -> bool:
        """Owner-configured state. Default is False in config.yaml."""
        return bool(self.config.get("mind", "camera_enabled", default=False))

    @property
    def interval_seconds(self) -> float:
        return float(self.config.get("mind", "camera_interval_s", default=30.0))

    @property
    def camera_index(self) -> int:
        return int(self.config.get("mind", "camera_index", default=0))

    def enable(self, caller: str = "agent"):
        """Attempting to enable the camera programmatically from inside the agent
        is a strict permission fence violation. Only the owner can toggle it in config.yaml.
        """
        if caller != "owner_config":
            raise PermissionFenceError(
                "Permission fence blocked: camera cannot be enabled by EXO. "
                "Only the owner can toggle 'camera_enabled: true' in config.yaml."
            )

    def capture_frame(self) -> Optional[Any]:
        """Capture one frame from the local camera if enabled.
        
        Returns frame in volatile memory or None if disabled or camera unavailable.
        Zero frames are ever written to disk.
        """
        if not self.is_enabled:
            return None

        if not CV2_AVAILABLE:
            return None

        try:
            cap = cv2.VideoCapture(self.camera_index)
            if not cap.isOpened():
                return None
            # Discard initial stale driver buffer frames so auto-exposure/white-balance settles
            # and the live, real-time frame is returned
            ret, frame = False, None
            for _ in range(6):
                ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                return frame
            return None
        except Exception:
            return None

    def detect_motion(self, frame: Any, threshold_pct: float = 1.0) -> str:
        """Rule-based motion/presence detection via frame differencing in memory.
        
        Honest limit: the rule-based brain detects, it does not see.
        Returns: 'motion detected in room' or 'no presence'
        """
        if frame is None:
            return "no presence"

        if not CV2_AVAILABLE:
            return "no presence"

        # Convert to grayscale and blur
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame.copy()
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self._last_gray_frame is None or self._last_gray_frame.shape != gray.shape:
            # Baseline calibration frame
            self._last_gray_frame = gray
            return "sensory baseline established (no presence)"

        # Frame differencing
        delta = cv2.absdiff(self._last_gray_frame, gray)
        thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]

        # Calculate percentage of changed pixels
        changed_pixels = cv2.countNonZero(thresh)
        total_pixels = gray.shape[0] * gray.shape[1]
        pct = (changed_pixels / total_pixels) * 100.0 if total_pixels > 0 else 0.0

        self._last_gray_frame = gray

        if pct >= threshold_pct:
            return "motion detected in room"
        else:
            return "no presence"

    def describe_frame_with_vision(
        self,
        frame: Any,
        model: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> Optional[str]:
        """Optional vision model path. Frame is encoded in memory, sent locally to Ollama,
        and immediately discarded. Never stored.
        """
        if frame is None or not CV2_AVAILABLE:
            return None

        model = model or str(self.config.get("mind", "vision_model", default="moondream"))
        endpoint = endpoint or str(self.config.get("mind", "ollama_endpoint", default="http://127.0.0.1:11434"))

        # Check permission fence: network egress is blocked; only local endpoint allowed
        if not (endpoint.startswith("http://127.0.0.1") or endpoint.startswith("http://localhost")):
            return None

        try:
            ret, buffer = cv2.imencode(".jpg", frame)
            if not ret:
                return None
            img_b64 = base64.b64encode(buffer).decode("utf-8")
            del buffer

            timeout = float(self.config.get("mind", "vision_timeout_s", default=15.0))
            url = f"{endpoint.rstrip('/')}/api/generate"
            payload = {
                "model": model,
                "prompt": "What do you see in front of the camera? Focus directly on the person, what they are wearing or doing, and any objects they are holding or showing.",
                "images": [img_b64],
                "stream": False
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                desc = res_json.get("response", "").strip()
                return desc if desc else None
        except Exception:
            return None

    def process_frame(self, frame: Any, use_vision: bool = True) -> Optional[str]:
        """Process a frame in volatile memory and return a textual observation description.
        
        The frame is processed entirely in memory and discarded. Zero bytes are written to disk.
        """
        if frame is None:
            return None

        # Rule-based motion detection (active default)
        desc = self.detect_motion(frame)

        # Vision path fallback / enhancement if configured
        vision_model = self.config.get("mind", "vision_model")
        if vision_model and use_vision:
            endpoint = self.config.get("mind", "ollama_endpoint", default="http://127.0.0.1:11434")
            v_desc = self.describe_frame_with_vision(frame, model=vision_model, endpoint=endpoint)
            if v_desc:
                desc = v_desc

        # Memory hygiene: clear frame reference
        del frame
        return f"Visual observation: {desc}"

    def poll_observation(self, synthetic_frame: Optional[Any] = None) -> Optional[Dict[str, Any]]:
        """Poll camera sensor on interval. Returns sensory capture event dictionary or None."""
        if not self.is_enabled:
            return None

        now = time.time()
        if synthetic_frame is None and (now - self._last_capture_time < self.interval_seconds):
            return None

        is_synthetic = synthetic_frame is not None
        frame = synthetic_frame if is_synthetic else self.capture_frame()
        if frame is None:
            return None

        self._last_capture_time = now
        # Synthetic frames used in unit tests test motion detection directly without VLM inference
        desc = self.process_frame(frame, use_vision=(not is_synthetic))
        if not desc:
            return None

        return {
            "raw": desc,
            "source": "camera",
            "t": now
        }
