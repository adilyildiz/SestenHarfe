"""
Canlı Anlık Akış (Streaming CTC) Doğrulama Testi
"""
import sys
import time
import numpy as np

from audio.vad import VoiceActivityDetector
from audio.buffer import AudioBuffer
from transcriber.wav2vec2_engine import Wav2Vec2Engine
import config

print("=== Canlı Streaming Pipeline Testi Başlıyor ===")

vad = VoiceActivityDetector()
buf = AudioBuffer(vad=vad)

w2v = Wav2Vec2Engine()
w2v.load()

# 1 saniyelik konuşma simülasyonu (480 örneklik 33 adet parça)
sr = 16000
chunk_size = 480
dummy_voice_chunk = (np.sin(2 * np.pi * 350 * np.arange(chunk_size) / sr) * 0.4).astype(np.float32)

print("\nKonuşma parçaları akıtılıyor (anlık harf kontrolü)...")
for i in range(15):  # ~450ms konuşma
    segments = buf.process_chunk(dummy_voice_chunk)
    if buf.is_currently_speaking:
        partial_audio = buf.get_current_speech_audio()
        if len(partial_audio) >= int(sr * 0.15):
            t0 = time.time()
            text = w2v.transcribe(partial_audio)
            elapsed_ms = (time.time() - t0) * 1000
            print(f"Parça {i+1} [Anlık Çıkarım]: {elapsed_ms:.1f}ms sürdü | Metin: '{text}'")

# Sessizlik simülasyonu
print("\nSessizlik akıtılıyor (segment sonlandırma)...")
silence_chunk = np.zeros(chunk_size, dtype=np.float32)
final_segments = []
for i in range(25):  # ~750ms sessizlik
    segs = buf.process_chunk(silence_chunk)
    if segs:
        final_segments.extend(segs)

print(f"Oluşan kesin segment sayısı: {len(final_segments)}")
for s in final_segments:
    print(f"Kesinleşen Segment: {s}")

w2v.unload()
print("\n=== Canlı Streaming Testi Başarıyla Tamamlandı! ===")
