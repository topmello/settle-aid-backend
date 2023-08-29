import json
import os
from pathlib import Path
from google.cloud import translate


def get_code(source):
    parent_path = Path(__file__).parent.parent
    file_path = parent_path / "data" / "lang_to_code.json"
    with open(file_path, 'r') as f:
        codes = json.load(f)

    for i in codes:
        if i == source:

            return codes[i]


def translate_text(text, source, project_id="fleet-fortress-395004"):
    parent_path = Path(__file__).parent
    credential_path = str(parent_path / "google_application_credentials.json")
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

    client = translate.TranslationServiceClient()
    location = "global"
    parent = f"projects/{project_id}/locations/{location}"

    lang_code = get_code(source)

    response = client.translate_text(
        request={
            "parent": parent,
            "contents": [text],
            "mime_type": "text/plain",
            "source_language_code": lang_code,
            "target_language_code": "en",
        }
    )


    return response.translations[0].translated_text
    



#translate_text("你好", "Chinese (Simplified)")
