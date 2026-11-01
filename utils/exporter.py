"""
SestenHarfe - Dışa Aktarıcı (TXT ve SRT Altyazı Formatı)
"""
import datetime
from pathlib import Path


def _format_srt_time(seconds: float) -> str:
    """Saniye değerini SRT altyazı zaman formatına (00:00:00,000) çevirir."""
    td = datetime.timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def export_to_txt(entries: list[dict], filepath: str, include_timestamps: bool = True):
    """
    Kayıtları TXT dosyasına yazar.
    entries: [{'text': str, 'start': float, 'duration': float, 'is_speech': bool}]
    """
    path = Path(filepath)
    with open(path, "w", encoding="utf-8") as f:
        for entry in entries:
            text = entry.get("text", "").strip()
            if not text:
                continue

            if include_timestamps:
                dt = datetime.datetime.fromtimestamp(entry.get("start", 0))
                time_str = dt.strftime("[%H:%M:%S] ")
                f.write(f"{time_str}{text}\n")
            else:
                f.write(f"{text}\n")


def export_to_srt(entries: list[dict], filepath: str):
    """
    Kayıtları standart SRT altyazı formatında dosyaya yazar.
    """
    path = Path(filepath)
    speech_entries = [e for e in entries if e.get("is_speech", True) and e.get("text", "").strip()]
    if not speech_entries:
        return

    # İlk konuşmanın başlangıcını 0.0 saniye olarak referans al
    base_time = speech_entries[0].get("start", 0.0)

    with open(path, "w", encoding="utf-8") as f:
        counter = 1
        for entry in speech_entries:
            text = entry.get("text", "").strip()
            start_offset = max(0.0, entry.get("start", 0.0) - base_time)
            end_offset = start_offset + entry.get("duration", 2.0)

            start_str = _format_srt_time(start_offset)
            end_str = _format_srt_time(end_offset)

            f.write(f"{counter}\n")
            f.write(f"{start_str} --> {end_str}\n")
            f.write(f"{text}\n\n")
            counter += 1
