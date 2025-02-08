import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from .audio import Audio
from .content import Content
from .media import Media
from .source import Source
from .subtitle import Subtitle

ALL_MODELS = [
    Source,
    Content,
    Media,
    Audio,
    Subtitle
]