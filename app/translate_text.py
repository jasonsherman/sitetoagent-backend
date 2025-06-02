import os
import json
from google.cloud import translate_v2 as translate
from langdetect import detect, LangDetectException
# Initialize the client
translate_client = translate.Client()

def is_english(text):
    """Detect if text is in English (or at least, not Japanese)."""
    try:
        lang = detect(text)
        return lang == 'en'
    except LangDetectException:
        # For numbers, short strings, etc.
        return False

def translate_large_text_if_japanese(text, target_lang='en'):
    # Check the language first!
    lang = detect(text)
    print(f"Detected language: {lang}")
    if lang != 'ja':
        print("Content is not Japanese, returning original.")
        return text 
    # return text
    # Now translate
    CHUNK_SIZE = 30000
    translated_chunks = []
    for start in range(0, len(text), CHUNK_SIZE):
        chunk = text[start:start+CHUNK_SIZE]
        result = translate_client.translate(chunk, target_language=target_lang, source_language=lang)
        translated_chunks.append(result['translatedText'])
    return ''.join(translated_chunks)

def translate_large_text(text, source_language='en', target_lang='ja'):
    # Google API supports up to 30,000 characters per request
    CHUNK_SIZE = 30000
    translated_chunks = []
    for start in range(0, len(text), CHUNK_SIZE):
        chunk = text[start:start+CHUNK_SIZE]
        result = translate_client.translate(chunk, target_language=target_lang, source_language=source_language)
        translated_chunks.append(result['translatedText'])
    return ''.join(translated_chunks)


def translate_text(text, target='ja'):
    """Translate a string to the target language (Japanese)."""
    # Safety: Only translate if text is detected as English
    if not text or not isinstance(text, str):
        return text
    result = translate_client.translate(text, target_language=target)
    return result['translatedText']


def translate_data_to_japanese(data):
    """Recursively traverse and translate all English strings to Japanese."""
    if isinstance(data, dict):
        return {k: translate_data_to_japanese(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [translate_data_to_japanese(item) for item in data]
    elif isinstance(data, str):
        return translate_text(data, target='ja')
    else:
        # int, float, bool, None, etc.
        return data