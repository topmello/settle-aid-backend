import os
from google.cloud import translate


def translate_text(text, project_id="fleet-fortress-395004"):
    credential_path = "./google_application_credentials.json"
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

    client = translate.TranslationServiceClient()
    location = "global"
    parent = f"projects/{project_id}/locations/{location}"

    response = client.translate_text(
        request={
            "parent": parent,
            "contents": [text],
            "mime_type": "text/plain",
            "source_language_code": "en-US",
            "target_language_code": "zh",
        }
    )

    for translation in response.translations:
        print("Translated text: {}".format(translation.translated_text))


translate_text("hi")
