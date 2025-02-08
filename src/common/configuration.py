import os
import platform
from dotenv import load_dotenv


def get_configuration(key):
    load_dotenv('config.env')
    value = os.getenv(key.upper())

    if "localhost" in value:
        if platform.system() == "Windows":
            return value
        elif platform.system() == "Darwin":
            #instance = os.getenv("INSTANCE")
            #return value.replace("localhost", instance)
            return value

    return value