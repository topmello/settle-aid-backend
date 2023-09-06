import json
import os
from pathlib import Path
from google.cloud import translate_v2 as translate
# https://cloud.google.com/translate/docs/basic/translating-text#translate_translate_text-python

parent_path = Path(__file__).parent.parent
credential_path = str(parent_path / "data" /
                      "google_application_credentials.json")
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

translate_client = translate.Client()

TARGET_LANG = "en"


def translate_text(text: str) -> dict:

    if isinstance(text, bytes):
        text = text.decode("utf-8")

    result = translate_client.translate(text, target_language=TARGET_LANG)

    return result["translatedText"]


def translate_list(text_list: list[str]) -> list[str]:
    results = [translate_text(result) for result in text_list]

    return results
