"""
SestenHarfe - Metin Biçimlendirici ve Birleştirici
Transkripsiyon çıktılarını zaman damgaları ve sessizlik belirteçleriyle formatlar.
"""
import datetime


def format_timestamp(timestamp_sec: float) -> str:
    """Zaman damgasını [SS:DD:SN] biçimine dönüştürür."""
    dt = datetime.datetime.fromtimestamp(timestamp_sec)
    return dt.strftime("[%H:%M:%S]")


def format_transcript_entry(
    text: str,
    is_speech: bool,
    start_time: float,
    duration: float,
    show_timestamp: bool = True
) -> str:
    """
    Bir konuşma veya sessizlik segmentini formatlayarak kullanıcıya gösterilecek metni üretir.
    """
    ts = f"{format_timestamp(start_time)} " if show_timestamp else ""

    if not is_speech:
        # Sessizlik aralığı
        return f"{ts}--- [Sessizlik ({duration:.1f} sn)] ---"

    cleaned_text = text.strip()
    if not cleaned_text:
        return ""

    return f"{ts}{cleaned_text}"
