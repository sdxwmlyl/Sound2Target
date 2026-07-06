import base64
import sounddevice as sd
import numpy as np
import threading
import queue
from typing import Optional, Callable


class AudioCapture:
    def __init__(self, sample_rate: int = 16000, chunk_duration: float = 0.5):
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        self.audio_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.is_recording = False
    
    def find_device(self, name_pattern: str = None) -> Optional[int]:
        """查找设备，优先 DirectSound（兼容任意采样率），避开 MME 16ch 衰减问题"""
        devices = sd.query_devices()
        best_ds = None  # DirectSound
        best_wasapi = None  # WASAPI
        best_fallback = None  # 兜底
        
        for i, d in enumerate(devices):
            if d['max_input_channels'] <= 0:
                continue
            if name_pattern and name_pattern.upper() not in d['name'].upper():
                continue
            
            host = d.get('hostapi', -1)
            if host == 1:  # DirectSound — 最兼容
                best_ds = i
                break  # DirectSound 优先，找到了就停
            elif host == 3:  # WASAPI — 可能不支持低采样率
                if best_wasapi is None:
                    best_wasapi = i
            elif best_fallback is None:
                best_fallback = i
        
        return best_ds or best_wasapi or best_fallback
    
    def get_default_input_device(self) -> Optional[int]:
        return sd.default.device[0] if sd.default.device[0] is not None else None
    
    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(f"Audio status: {status}")
        if not self.stop_event.is_set():
            # 多声道混音为单声道
            if indata.shape[1] > 1:
                mono_data = np.mean(indata, axis=1, keepdims=True).astype(np.int16)
            else:
                mono_data = indata
            self.audio_queue.put(mono_data.copy())
    
    def start(self, device_id: Optional[int] = None):
        if self.is_recording:
            return
        
        if device_id is None:
            device_id = self.get_default_input_device()
        
        # 获取设备信息，限制为最多 2 声道（避免 16ch 平均衰减）
        device_info = sd.query_devices(device_id)
        channels = min(device_info['max_input_channels'], 2)
        
        self.stop_event.clear()
        self.stream = sd.InputStream(
            device=device_id,
            samplerate=self.sample_rate,
            channels=channels,
            dtype=np.int16,
            blocksize=int(self.sample_rate * self.chunk_duration),
            callback=self._audio_callback
        )
        self.stream.start()
        self.is_recording = True
    
    def stop(self):
        if not self.is_recording:
            return
        
        self.stop_event.set()
        if self.stream:
            self.stream.stop()
            self.stream.close()
        self.is_recording = False
    
    def get_audio_chunk(self, timeout: float = 0.5) -> Optional[bytes]:
        try:
            indata = self.audio_queue.get(timeout=timeout)
            audio_bytes = indata.astype(np.int16).tobytes()
            return audio_bytes
        except queue.Empty:
            return None
    
    def get_audio_base64(self, timeout: float = 0.5) -> Optional[str]:
        audio_bytes = self.get_audio_chunk(timeout)
        if audio_bytes:
            return base64.b64encode(audio_bytes).decode()
        return None
    
    def clear_queue(self):
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break


class MicrophoneCapture(AudioCapture):
    def __init__(self, sample_rate: int = 16000, chunk_duration: float = 0.5):
        super().__init__(sample_rate, chunk_duration)
    
    def start_microphone(self):
        device_id = self.get_default_input_device()
        print(f"Starting microphone capture on device: {device_id}")
        self.start(device_id)


class SystemSoundCapture(AudioCapture):
    CABLE_DEVICE_PATTERN = "CABLE"
    
    def __init__(self, sample_rate: int = 16000, chunk_duration: float = 0.5):
        super().__init__(sample_rate, chunk_duration)
    
    def find_cable_device(self) -> Optional[int]:
        return self.find_device(self.CABLE_DEVICE_PATTERN)
    
    def start_system_sound(self):
        device_id = self.find_cable_device()
        if device_id is None:
            raise RuntimeError("CABLE virtual audio device not found. Please install VB-Audio Virtual Cable.")
        print(f"Starting system sound capture on CABLE device: {device_id}")
        self.start(device_id)


def get_supported_formats() -> list:
    from config.settings import get_settings
    settings = get_settings()
    return settings.audio.supported_formats