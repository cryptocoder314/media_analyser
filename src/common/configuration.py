import os
import platform
from dotenv import load_dotenv
from pathlib import Path


def get_configuration(key):
    env_path = Path(__file__).resolve().parent.parent.parent / 'config.env'
    load_dotenv(dotenv_path=env_path)
    value = os.getenv(key.upper())

    if "localhost" in value:
        if platform.system() == "Windows":
            return value
        elif platform.system() == "Darwin":
            instance = os.getenv("INSTANCE")
            return value.replace("localhost", instance)

    return value