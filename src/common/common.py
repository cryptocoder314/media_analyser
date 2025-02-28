LANGUAGES = {
    "english": ["english", "ingles", "ingles-us", "en"],
    "portuguese": ["portuguese", "portugues", "pt", "br", "pt-br", "pt_br", "ptbr"],
    "japanese": ["japanese", "japones", "jp", "ja"],
    "chinese": ["chinese (mainland china)", "zh"]
}
LANGUAGE_MAP = {alias.lower(): lang for lang, aliases in LANGUAGES.items() for alias in aliases}

CODEC_MAP = {
    "H264": ["avc", "h264", "h.264", "h264", "avc"],
    "H265": ["h265", "hevc", "h.265", "hevc"],
    "AV1": ["av1"]
}

def detect_language(lang_code):
    return LANGUAGE_MAP.get(lang_code.lower(), "unknown")


def normalize_codec(codec):
    codec_lower = codec.lower() if codec else ""

    for normalized_codec, synonyms in CODEC_MAP.items():
        if codec_lower in map(str.lower, synonyms):
            return normalized_codec

    return "Unknown"
