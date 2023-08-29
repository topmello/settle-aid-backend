import json
import os
from google.cloud import translate

def get_code(source):
    f = open('../data/lang_to_code.json')
    codes = json.load(f)

    for i in codes:
        if i == source:
            print(codes[i])
            return codes[i]


def translate_text(text, source, project_id="fleet-fortress-395004"):
    credential_path = "./google_application_credentials.json"
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

    client = translate.TranslationServiceClient()
    location = "global"
    parent = f"projects/{project_id}/locations/{location}"

    lang_code = get_code(source)
    print(lang_code)

    response = client.translate_text(
        request={
            "parent": parent,
            "contents": [text],
            "mime_type": "text/plain",
            "source_language_code": lang_code,
            "target_language_code": "en",
        }
    )

    for translation in response.translations:
        print("Translated text: {}".format(translation.translated_text))



translate_text("你好", "Chinese (Simplified)")
