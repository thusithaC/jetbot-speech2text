import vosk
from aioify import aioify
from config import(
    MODEL,
    SAMPLE_RATE
)


def get_recognizer():
    model = vosk.Model(MODEL)
    recognizer = vosk.KaldiRecognizer(model, SAMPLE_RATE)
    return recognizer


@aioify
def speech_to_text(recognizer, data):
    if recognizer.AcceptWaveform(data):
        text = recognizer.Result()
    else:
        text = recognizer.PartialResult()
    return text
