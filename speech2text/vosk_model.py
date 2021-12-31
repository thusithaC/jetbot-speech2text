import vosk
from aioify import aioify
import json
from config import(
    MODEL,
    SAMPLE_RATE,
    logger
)


def get_recognizer():
    model = vosk.Model(MODEL)
    recognizer = vosk.KaldiRecognizer(model, SAMPLE_RATE)
    return recognizer


@aioify
def speech_to_text(recognizer, data):
    if recognizer.AcceptWaveform(data):
        result = recognizer.Result()
    else:
        result = recognizer.PartialResult()
    if result:
        res_parsed = json.loads(result)
        text = res_parsed.get("partial", "") if "partial" in res_parsed else res_parsed.get("text", "") if "text" in res_parsed else ""
        logger.debug(f"Parsed Text: {text}")
    return text
