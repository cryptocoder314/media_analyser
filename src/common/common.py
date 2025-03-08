import subprocess
import json


LANGUAGES = {
    "english": ["english", "ingles", "ingles-us", "en", "eng"],
    "portuguese": ["portuguese", "portugues", "pt", "br", "pt-br", "pt_br", "ptbr", "por"],
    "japanese": ["japanese", "japones", "jp", "ja", "jpn"],
    "chinese": ["chinese (mainland china)", "zh", "chi", "zho"],
    "spanish": ["spa"],
    "french": ["fra"],
    "german": ["ger"],
    "italian": ["ita"],
    "korean": ["kor"],
    "russian": ["rus"],
    "dutch": ["dut", "nld"],
    "arabic": ["ara", "ar"],
    "turkish": ["tur"],
    "hindi": ["hin"]
}
ISO_639_2 = {
    "english": ["eng"],
    "portuguese": ["por"],
    "spanish": ["spa"],
    "french": ["fra"],
    "german": ["ger"],
    "italian": ["ita"],
    "japanese": ["jpn"],
    "korean": ["kor"],
    "chinese": ["chi", "zho"],
    "russian": ["rus"],
    "dutch": ["dut", "nld"],
    "arabic": ["ara"],
    "turkish": ["tur"],
    "hindi": ["hin"]
}
LANGUAGE_MAP = {alias.lower(): lang for lang, aliases in LANGUAGES.items() for alias in aliases}
ISO_639_2_MAP = {lang.lower(): codes[0] for lang, codes in ISO_639_2.items()}

CODEC_MAP = {
    "H264": ["avc", "h264", "h.264", "h264", "avc"],
    "H265": ["h265", "hevc", "h.265", "hevc"],
    "AV1": ["av1"]
}

def detect_iso_language_code(language):
    return ISO_639_2_MAP.get(language.lower(), "und")



def detect_language(lang_code):
    return LANGUAGE_MAP.get(lang_code.lower(), "remove")


def normalize_codec(codec):
    codec_lower = codec.lower() if codec else ""

    for normalized_codec, synonyms in CODEC_MAP.items():
        if codec_lower in map(str.lower, synonyms):
            return normalized_codec

    return "Unknown"


def run_media_info(file_path):
    result = subprocess.run([
        "mediainfo", "--Language=raw", "--Output=JSON", file_path
    ], capture_output=True, text=True)

    json_result = json.loads(result.stdout) if result.stdout else {}

    return json_result
