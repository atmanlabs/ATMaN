"""Voice Sensory and Vocal Subsystem for ATMAN Live (His Local Ears and Mouth).

Design Rules & Constraints (Strict / Non-Negotiable):
1. Owner-toggled only, default OFF. `voice_enabled: false` in `config.yaml`.
   ATMAN cannot enable the microphone or voice loop himself -- attempting to do so
   is a strict permission fence violation.
2. Zero audio stored on disk. All audio capture, synthesis, and buffering are
   performed strictly in volatile system RAM (`io.BytesIO`, `numpy` arrays).
   Audio buffers are discarded immediately after transcription/playback.
   Only transcripts enter the 8-stage mind loop as standard operator inputs.
3. CPU only for voice processing. The GPU (RTX 3050) belongs exclusively to
   the LLM brain. STT runs on the Ryzen 7 5700 via `faster-whisper` (CPU quantized int8);
   TTS runs on CPU via `piper-tts`.
4. Walkie-talkie style: listen -> transcribe -> think -> speak.
   One side at a time; no full-duplex promises.
5. Push-to-talk default (press Enter to talk / press Enter to stop).
   Open-mic with RMS silence detection is opt-in, default OFF.

THREAT-MODEL HONESTY STATEMENT:
Session authentication binds at system startup (via operator passphrase),
NOT per-utterance. The voice recognition pipeline transcribes human speech phonetically;
it does NOT authenticate biometric voiceprints or identify the speaker.
Anyone physically present in the room who speaks into the microphone can inject
input as the operator. Spoken input therefore carries ZERO special privilege
over typed input. All spoken inputs pass through the exact same 8-stage mind loop,
evaluated by the exact same Judge, and gated by the exact same immutable TSC
invariants and permission fence. Physical room control, the immutable core, and
the unchanged Judge/fence are the only true mitigations.
"""
from __future__ import annotations

import io
import logging
import math
import os
from pathlib import Path
import queue
import sys
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import wave

import numpy as np

try:
    import sounddevice as sd
    SD_AVAILABLE = True
except ImportError:
    SD_AVAILABLE = False

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    import piper
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False

from config import Config, PermissionFenceError

HERE = Path(__file__).resolve().parent
logger = logging.getLogger("atman.voice")


class WhisperSTT:
    """Local Speech-to-Text engine powered by faster-whisper on CPU."""

    def __init__(
        self,
        model_name: str = "base",
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self._model: Optional[WhisperModel] = None
        self._lock = threading.Lock()

    def _ensure_model(self) -> WhisperModel:
        if not WHISPER_AVAILABLE:
            raise RuntimeError("faster-whisper is not installed. Run 'pip install faster-whisper'.")
        with self._lock:
            if self._model is None:
                logger.info("Loading faster-whisper model '%s' on %s (%s)...", self.model_name, self.device, self.compute_type)
                self._model = WhisperModel(
                    self.model_name,
                    device=self.device,
                    compute_type=self.compute_type
                )
            return self._model

    def transcribe(
        self,
        audio_input: Union[np.ndarray, bytes, io.BytesIO, str, Path],
        language: str = "en"
    ) -> str:
        """Transcribe audio from memory or file into plain text.
        
        Accepts:
        - 1D numpy array of float32 samples (16 kHz)
        - bytes or io.BytesIO of WAV audio
        - file path (not recommended by default, but supported)
        """
        model = self._ensure_model()

        if isinstance(audio_input, np.ndarray):
            # Ensure 1D float32 normalized
            if audio_input.dtype != np.float32:
                audio_input = audio_input.astype(np.float32)
            if audio_input.ndim > 1:
                audio_input = audio_input.mean(axis=1)
            # If silence / empty array
            if len(audio_input) == 0 or np.max(np.abs(audio_input)) < 1e-4:
                return ""
            segments, info = model.transcribe(audio_input, language=language, beam_size=1)
        elif isinstance(audio_input, (bytes, bytearray)):
            buf = io.BytesIO(audio_input)
            segments, info = model.transcribe(buf, language=language, beam_size=1)
        elif isinstance(audio_input, io.BytesIO):
            audio_input.seek(0)
            segments, info = model.transcribe(audio_input, language=language, beam_size=1)
        elif isinstance(audio_input, (str, Path)):
            segments, info = model.transcribe(str(audio_input), language=language, beam_size=1)
        else:
            raise ValueError(f"Unsupported audio input type: {type(audio_input)}")

        text = " ".join(seg.text for seg in segments).strip()
        return text


class PiperTTS:
    """Local Text-to-Speech engine powered by piper-tts on CPU."""

    def __init__(
        self,
        model_path: Union[str, Path] = "voices/en_US-ryan-medium.onnx",
        config_path: Optional[Union[str, Path]] = None
    ):
        self.model_path = Path(model_path)
        if not self.model_path.is_absolute():
            self.model_path = HERE / self.model_path
        self.config_path = Path(config_path) if config_path else self.model_path.with_suffix(".onnx.json")
        self._voice: Optional[piper.PiperVoice] = None
        self._lock = threading.Lock()

    def _ensure_voice(self) -> piper.PiperVoice:
        if not PIPER_AVAILABLE:
            raise RuntimeError("piper-tts is not installed. Run 'pip install piper-tts'.")
        with self._lock:
            if self._voice is None:
                if not self.model_path.exists():
                    # Attempt to download into voices dir
                    logger.info("Piper model not found at %s. Attempting download...", self.model_path)
                    import urllib.request
                    voices_dir = self.model_path.parent
                    voices_dir.mkdir(parents=True, exist_ok=True)
                    model_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx"
                    json_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json"
                    urllib.request.urlretrieve(model_url, str(self.model_path))
                    urllib.request.urlretrieve(json_url, str(self.config_path))

                self._voice = piper.PiperVoice.load(
                    str(self.model_path),
                    config_path=str(self.config_path),
                    use_cuda=False
                )
            return self._voice

    @property
    def sample_rate(self) -> int:
        voice = self._ensure_voice()
        return voice.config.sample_rate

    def synthesize_to_buffer(self, text: str) -> io.BytesIO:
        """Synthesize text directly into an in-memory WAV BytesIO buffer.
        
        Zero disk writes.
        """
        voice = self._ensure_voice()
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            voice.synthesize_wav(text, wav_file)
        buf.seek(0)
        return buf

    def synthesize_to_bytes(self, text: str) -> bytes:
        """Synthesize text and return raw WAV bytes."""
        buf = self.synthesize_to_buffer(text)
        return buf.getvalue()

    def synthesize_to_samples(self, text: str) -> Tuple[np.ndarray, int]:
        """Synthesize text and return (numpy_float32_array, sample_rate)."""
        buf = self.synthesize_to_buffer(text)
        with wave.open(buf, "rb") as wf:
            n_channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            raw_frames = wf.readframes(n_frames)

        if sample_width == 2:
            data = np.frombuffer(raw_frames, dtype=np.int16).astype(np.float32) / 32768.0
        elif sample_width == 1:
            data = (np.frombuffer(raw_frames, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
        elif sample_width == 4:
            data = np.frombuffer(raw_frames, dtype=np.int32).astype(np.float32) / 2147483648.0
        else:
            data = np.frombuffer(raw_frames, dtype=np.float32)

        if n_channels > 1:
            data = data.reshape(-1, n_channels)
        return data, framerate

    def speak(self, text: str, play_audio: bool = False) -> bytes:
        """Synthesize text to speech, optionally playing via sounddevice.
        
        Returns the generated WAV bytes.
        """
        samples, sr = self.synthesize_to_samples(text)
        wav_bytes = self.synthesize_to_bytes(text)
        if play_audio and SD_AVAILABLE:
            try:
                sd.play(samples, sr)
                sd.wait()
            except Exception as e:
                logger.warning("Audio playback failed: %s", e)
        return wav_bytes


class AudioRecorder:
    """Microphone audio capture into volatile memory only."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    def record_push_to_talk_enter(self, prompt: str = "") -> np.ndarray:
        """Console push-to-talk using Enter key. Holds audio strictly in RAM.
        Records immediately upon calling, stops when operator presses Enter.
        """
        if not SD_AVAILABLE:
            raise RuntimeError("sounddevice is not installed.")

        # Flush any trailing keypresses from typing 'voice'
        if sys.platform == "win32":
            try:
                import msvcrt
                while msvcrt.kbhit():
                    msvcrt.getch()
            except Exception:
                pass

        print("\n" + "=" * 70)
        print("  [VOICE] MICROPHONE ACTIVE -- RECORDING NOW!")
        print("  Speak your question or thought clearly into the microphone.")
        print("  When you are finished speaking, press [ENTER] to send.")
        print("=" * 70)

        chunks: List[np.ndarray] = []
        stop_event = threading.Event()

        def _audio_callback(indata, frames, time_info, status):
            if status:
                logger.warning("Recording status: %s", status)
            chunks.append(indata.copy())

        stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            callback=_audio_callback
        )

        with stream:
            try:
                sys.stdin.readline()
            finally:
                stop_event.set()

        print("[RECORDING STOPPED. Processing in memory...]\n")
        if not chunks:
            return np.zeros(0, dtype=np.float32)

        audio = np.concatenate(chunks, axis=0).flatten()
        peak = float(np.max(np.abs(audio))) if len(audio) > 0 else 0.0
        rms = float(np.sqrt(np.mean(audio ** 2))) if len(audio) > 0 else 0.0

        if peak < 0.005 and len(audio) > 8000:
            print(f"[VOICE NOTICE] Audio signal is very quiet (Peak: {peak:.4f}, RMS: {rms:.4f}).")
            print("If your speech was not detected, verify your microphone is unmuted and set as Windows default.\n")

        return audio


    def record_open_mic(
        self,
        silence_threshold: float = 0.01,
        silence_duration_s: float = 1.5,
        max_duration_s: float = 15.0
    ) -> np.ndarray:
        """Open-mic with RMS silence detection. Holds audio strictly in RAM."""
        if not SD_AVAILABLE:
            raise RuntimeError("sounddevice is not installed.")

        chunks: List[np.ndarray] = []
        speech_started = False
        silence_start_time: Optional[float] = None
        start_time = time.time()
        chunk_duration = 0.1
        chunk_samples = int(self.sample_rate * chunk_duration)

        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="float32") as stream:
            while (time.time() - start_time) < max_duration_s:
                chunk, _ = stream.read(chunk_samples)
                chunks.append(chunk.copy())
                rms = math.sqrt(float(np.mean(chunk ** 2)))

                if rms >= silence_threshold:
                    speech_started = True
                    silence_start_time = None
                elif speech_started:
                    if silence_start_time is None:
                        silence_start_time = time.time()
                    elif (time.time() - silence_start_time) >= silence_duration_s:
                        break

        if not chunks:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(chunks, axis=0).flatten()


class VoiceEngine:
    """The local, in-memory voice sensory and vocal subsystem."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        stt_model = str(self.config.get("mind", "stt_model", default="base"))
        stt_device = str(self.config.get("mind", "stt_device", default="cpu"))
        stt_compute = str(self.config.get("mind", "stt_compute_type", default="int8"))
        tts_model_path = str(self.config.get("mind", "tts_model_path", default="voices/en_US-ryan-medium.onnx"))

        self.stt = WhisperSTT(model_name=stt_model, device=stt_device, compute_type=stt_compute)
        self.tts = PiperTTS(model_path=tts_model_path)
        self.recorder = AudioRecorder(sample_rate=16000)

    @property
    def is_enabled(self) -> bool:
        """Owner-configured state. Default is False in config.yaml."""
        return bool(self.config.get("mind", "voice_enabled", default=False))

    @property
    def voice_mode(self) -> str:
        """'push-to-talk' (default) or 'open-mic'."""
        return str(self.config.get("mind", "voice_mode", default="push-to-talk"))

    @property
    def push_to_talk_key(self) -> str:
        return str(self.config.get("mind", "push_to_talk_key", default="enter"))

    def enable(self, caller: str = "agent"):
        """Attempting to enable voice programmatically from inside the agent
        is a strict permission fence violation. Only the owner can toggle it in config.yaml.
        """
        if caller != "owner_config":
            raise PermissionFenceError(
                "Permission fence blocked: voice/mic cannot be enabled by ATMAN. "
                "Only the owner can toggle 'voice_enabled: true' in config.yaml."
            )

    def talk_turn(
        self,
        loop: Any,
        audio_input: Optional[Union[np.ndarray, bytes, io.BytesIO]] = None,
        speak_output: bool = False,
        force_enabled: bool = False,
        capture_vision: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Execute one complete walkie-talkie conversation turn:
        1. Capture speech (from mic or provided memory buffer).
        2. Optionally capture live camera frame and describe with local vision model (Moondream).
        3. Transcribe speech to text (CPU STT).
        4. Feed multimodal observation into 8-stage loop (generative brain & Judge gating).
        5. Synthesize spoken reply (CPU TTS).
        
        Zero audio and zero camera frames are ever written to disk.
        Returns comprehensive latency and cycle outcome telemetry.
        """
        if not self.is_enabled and not force_enabled:
            raise PermissionFenceError(
                "Voice subsystem is disabled in config.yaml ('voice_enabled: false'). "
                "Operator must explicitly enable it in config.yaml."
            )

        # 1. Capture audio in memory
        if audio_input is None:
            if self.voice_mode == "open-mic":
                audio_data = self.recorder.record_open_mic()
            else:
                audio_data = self.recorder.record_push_to_talk_enter()
        else:
            audio_data = audio_input

        # 2. Transcribe (STT)
        t_stt_start = time.time()
        transcript = self.stt.transcribe(audio_data)
        stt_latency_s = time.time() - t_stt_start

        if not transcript.strip():
            return {
                "transcript": "",
                "cycle_result": None,
                "response_text": "",
                "wav_bytes": b"",
                "vision_desc": None,
                "vision_latency_s": 0.0,
                "stt_latency_s": stt_latency_s,
                "brain_latency_s": 0.0,
                "tts_latency_s": 0.0,
                "roundtrip_latency_s": stt_latency_s
            }

        # 2b. Live Camera Vision Capture (Multimodal Perception)
        do_vision = capture_vision if capture_vision is not None else (
            audio_input is None and hasattr(loop, "camera") and getattr(loop.camera, "is_enabled", False)
        )
        vision_desc = None
        vision_latency_s = 0.0
        if do_vision:
            try:
                frame = loop.camera.capture_frame()
                if frame is not None:
                    t_vis_start = time.time()
                    vision_model = str(self.config.get("mind", "vision_model", default="moondream"))
                    endpoint = str(self.config.get("mind", "ollama_endpoint", default="http://127.0.0.1:11434"))
                    vision_desc = loop.camera.describe_frame_with_vision(frame, model=vision_model, endpoint=endpoint)
                    vision_latency_s = time.time() - t_vis_start
                    if vision_desc:
                        print(f"\n[VISION EYE] Saw: \"{vision_desc}\" ({vision_latency_s:.2f}s)")
            except Exception as e:
                logger.warning("Live camera capture in voice turn failed: %s", e)

        # 3. Inject transcript (+ optional visual context) into 8-stage mind loop
        if vision_desc:
            raw_input = f"[Visual observation: {vision_desc}] Operator says: \"{transcript}\""
        else:
            raw_input = transcript

        t_brain_start = time.time()
        cycle_res = loop.run_cycle({"raw": raw_input, "source": "operator"})
        brain_latency_s = time.time() - t_brain_start

        # 4. Speak response (TTS)
        verdict = cycle_res.get("verdict")
        action_res = cycle_res.get("action_result", {})
        response_text = ""
        wav_bytes = b""
        tts_latency_s = 0.0

        if verdict and verdict.approved and action_res.get("action") in ("respond", "tool_call"):
            response_text = action_res.get("content", "")
            if response_text:
                t_tts_start = time.time()
                wav_bytes = self.tts.speak(response_text, play_audio=speak_output)
                tts_latency_s = time.time() - t_tts_start

        roundtrip_latency_s = stt_latency_s + vision_latency_s + brain_latency_s + tts_latency_s

        return {
            "transcript": transcript,
            "cycle_result": cycle_res,
            "response_text": response_text,
            "wav_bytes": wav_bytes,
            "vision_desc": vision_desc,
            "vision_latency_s": vision_latency_s,
            "stt_latency_s": stt_latency_s,
            "brain_latency_s": brain_latency_s,
            "tts_latency_s": tts_latency_s,
            "roundtrip_latency_s": roundtrip_latency_s
        }
