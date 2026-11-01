"""
SestenHarfe - Ses Tamponu ve Akıllı Parçalayıcı (Segmenter)
VAD durumuna göre konuşma ve sessizlik bloklarını paketler
"""
import time
import numpy as np
import config
from .vad import VoiceActivityDetector


class AudioSegment:
    """ASR motoruna veya arayüze iletilen ses paketi."""
    def __init__(self, audio_data: np.ndarray, is_speech: bool, start_time: float, duration: float):
        self.audio_data = audio_data  # 1D float32 numpy dizisi veya None (sessizlik için)
        self.is_speech = is_speech
        self.start_time = start_time
        self.duration = duration

    def __repr__(self):
        tip = "Konuşma" if self.is_speech else "Sessizlik"
        return f"<AudioSegment {tip} {self.duration:.2f}s>"


class AudioBuffer:
    def __init__(self, vad: VoiceActivityDetector = None, sample_rate: int = config.SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.vad = vad or VoiceActivityDetector()

        self.current_speech_chunks = []
        self.is_currently_speaking = False
        self.speech_start_time = 0.0

        # Sayaçlar (milisaniye cinsinden)
        self.ms_per_chunk = config.CHUNK_DURATION_MS
        self.silence_accumulated_ms = 0
        self.silence_start_time = 0.0
        self.silence_reported = False

    def reset(self):
        """Tamponu sıfırlar."""
        self.current_speech_chunks.clear()
        self.is_currently_speaking = False
        self.speech_start_time = 0.0
        self.silence_accumulated_ms = 0
        self.silence_start_time = time.time()
        self.silence_reported = False

    def get_current_speech_audio(self) -> np.ndarray:
        """Şu an konuşulmakta olan ve henüz kesinleşmemiş ses parçalarını birleşik dizi olarak döner."""
        if not self.current_speech_chunks:
            return np.empty(0, dtype=np.float32)
        return np.concatenate(self.current_speech_chunks)

    def process_chunk(self, chunk: np.ndarray) -> list[AudioSegment]:
        """
        Gelen bir ses parçasını işler ve hazır olan AudioSegment'leri döndürür.
        """
        ready_segments = []
        now = time.time()
        has_speech = self.vad.is_speech(chunk)

        if has_speech:
            self.silence_accumulated_ms = 0
            self.silence_reported = False

            if not self.is_currently_speaking:
                # Yeni bir konuşma başladı
                self.is_currently_speaking = True
                self.speech_start_time = now
                self.current_speech_chunks = [chunk]
            else:
                self.current_speech_chunks.append(chunk)

            # Maksimum konuşma süresi aşıldı mı? (Örn: 10 saniye boyunca hiç durmadan konuştu)
            current_duration_ms = len(self.current_speech_chunks) * self.ms_per_chunk
            if current_duration_ms >= config.MAX_SPEECH_DURATION_MS:
                # Zorunlu segment kesimi yap (gecikmeyi önlemek için)
                audio_data = np.concatenate(self.current_speech_chunks)
                duration_sec = len(audio_data) / self.sample_rate
                ready_segments.append(AudioSegment(
                    audio_data=audio_data,
                    is_speech=True,
                    start_time=self.speech_start_time,
                    duration=duration_sec
                ))
                self.current_speech_chunks.clear()
                self.speech_start_time = now

        else:
            # Sessizlik parçası geldi
            if self.is_currently_speaking:
                self.silence_accumulated_ms += self.ms_per_chunk
                # Doğal duraklamaları koparmamak için küçük sessizlikleri konuşma içine dahil et
                self.current_speech_chunks.append(chunk)

                # Yeterince uzun sessizlik oluştu mu? (Örn: 700ms)
                if self.silence_accumulated_ms >= config.SILENCE_TRIGGER_MS:
                    # Konuşmayı tamamla ve segment oluştur
                    total_ms = len(self.current_speech_chunks) * self.ms_per_chunk
                    if total_ms >= config.MIN_SPEECH_DURATION_MS:
                        audio_data = np.concatenate(self.current_speech_chunks)
                        duration_sec = len(audio_data) / self.sample_rate
                        ready_segments.append(AudioSegment(
                            audio_data=audio_data,
                            is_speech=True,
                            start_time=self.speech_start_time,
                            duration=duration_sec
                        ))

                    self.current_speech_chunks.clear()
                    self.is_currently_speaking = False
                    self.silence_accumulated_ms = 0
                    self.silence_start_time = now
            else:
                # Zaten sessizlik halindeyiz
                if self.silence_start_time == 0.0:
                    self.silence_start_time = now
                silence_duration = now - self.silence_start_time

                # 2 saniyeden uzun süren sessizlikte bir kereye mahsus sessizlik işareti üret
                if silence_duration >= 2.0 and not self.silence_reported:
                    ready_segments.append(AudioSegment(
                        audio_data=None,
                        is_speech=False,
                        start_time=self.silence_start_time,
                        duration=silence_duration
                    ))
                    self.silence_reported = True

        return ready_segments
