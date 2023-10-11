import os
from pathlib import Path
from google.cloud import translate_v2 as translate
# https://cloud.google.com/translate/docs/basic/translating-text#translate_translate_text-python

parent_path = Path(__file__).parent.parent
credential_path = str(parent_path / "data" /
                      "google_application_credentials.json")
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

translate_client = translate.Client()

DEFAULT_LANG = "en-AU"
LANG_DICT = {
    "en-AU": "en",
    "zh-CN": "zh",
    "hi-IN": "hi"
}


def translate_text(text: str, target_language: str = DEFAULT_LANG) -> dict:

    if isinstance(text, bytes):
        text = text.decode("utf-8")

    target = LANG_DICT[target_language]

    print(target)

    result = translate_client.translate(text, target_language=target)

    return result["translatedText"]
