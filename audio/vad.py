"""
SestenHarfe - Ses Aktivite Algılama (VAD)
WebRTC VAD ve Enerji Tabanlı Yedek VAD desteği
"""
import numpy as np
import config

try:
    import webrtcvad
    WEBRTC_AVAILABLE = True
except ImportError:
    webrtcvad = None
    WEBRTC_AVAILABLE = False


class VoiceActivityDetector:
    def __init__(self, aggressiveness: int = config.VAD_AGGRESSIVENESS, sample_rate: int = config.SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.aggressiveness = aggressiveness
        self.vad = None

        if WEBRTC_AVAILABLE:
            try:
                self.vad = webrtcvad.Vad(aggressiveness)
            except Exception as e:
                print(f"[VAD Uyarısı] webrtcvad başlatılamadı, enerji tabanlı VAD kullanılacak: {e}")
                self.vad = None
        else:
            print("[VAD Bilgisi] webrtcvad yüklü değil, enerji tabanlı VAD kullanılacak.")

    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """
        Gelen ses parçasında (float32 veya int16) konuşma olup olmadığını döner.
        audio_chunk: 1D numpy array, 16000Hz (örn. 480 örnek = 30ms)
        """
        if len(audio_chunk) == 0:
            return False

        # WebRTC VAD varsa onu kullan
        if self.vad is not None:
            try:
                # float32 (-1.0 to 1.0) ise int16'ya dönüştür
                if audio_chunk.dtype == np.float32:
                    int16_chunk = (np.clip(audio_chunk, -1.0, 1.0) * 32767).astype(np.int16)
                else:
                    int16_chunk = audio_chunk.astype(np.int16)

                raw_bytes = int16_chunk.tobytes()
                # WebRTC VAD 10, 20 veya 30ms gerektirir. 16kHz'de 30ms = 480 örnek
                if len(int16_chunk) in (160, 320, 480):
                    return self.vad.is_speech(raw_bytes, self.sample_rate)
            except Exception:
                pass  # Hata olursa enerji yöntemine düş

        # Enerji tabanlı yedek kontrol
        energy = self.calculate_energy(audio_chunk)
        return energy > config.ENERGY_THRESHOLD

    @staticmethod
    def calculate_energy(audio_chunk: np.ndarray) -> float:
        """
        RMS (Root Mean Square) genlik enerjisini 0.0 - 1.0 arasında hesaplar.
        Mikrofon seviye göstergesi için de kullanılır.
        """
        if len(audio_chunk) == 0:
            return 0.0
        if audio_chunk.dtype != np.float32:
            float_chunk = audio_chunk.astype(np.float32) / 32768.0
        else:
            float_chunk = audio_chunk

        rms = np.sqrt(np.mean(np.square(float_chunk)) + 1e-12)
        # 0 - 1 arasına normalize et (logaritmik veya doğrusal)
        normalized = float(np.clip(rms * 5.0, 0.0, 1.0))
        return normalized
