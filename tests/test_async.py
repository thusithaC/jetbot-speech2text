import asyncio
import queue
import sys
from collections import deque
import numpy as np
import sounddevice as sd
import vosk
from aioify import aioify

OUT_LENGTH = 20
MODEL = "models/vosk-model-small-en-us"


async def inputstream_generator(channels=1, **kwargs):
    """Generator that yields blocks of input data as NumPy arrays.
        Just using for debug in print info at the start   
    """
    q_in = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def callback(indata, frame_count, time_info, status):
        loop.call_soon_threadsafe(q_in.put_nowait, (indata.copy(), status))

    stream = sd.InputStream(callback=callback, channels=channels, **kwargs)
    with stream:
        while True:
            indata, status = await q_in.get()
            yield indata, status



async def stream_generator(blocksize, *, channels=1, dtype='int16',
                           **kwargs):
    """Generator that yields blocks of input/output data as NumPy arrays.

    The output blocks are uninitialized and have to be filled with
    appropriate audio signals.

    """
    assert blocksize != 0
    q_in = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def callback(indata, frame_count, time_info, status):
        loop.call_soon_threadsafe(q_in.put_nowait, (indata.copy(), status))

    stream = sd.InputStream(blocksize=blocksize, callback=callback, dtype=dtype, channels=channels, **kwargs)
    with stream:
        while True:
            indata, status = await q_in.get()
            yield indata, status
            


async def print_input_infos(**kwargs):
    """Show minimum and maximum value of each incoming audio block."""
    async for indata, status in inputstream_generator(**kwargs):
        if status:
            print(status)
        print('min:', indata.min(), '\t', 'max:', indata.max())


@aioify
def speech_to_text(recognizer, data):
    if recognizer.AcceptWaveform(data):
        text = recognizer.Result()
    else:
        text = recognizer.PartialResult()
    return text


async def wire_coro(**kwargs):
    """Create a connection between audio inputs and outputs.

    Asynchronously iterates over a stream generator and for each block
    simply copies the input data into the output block.

    """
    print("opeining model")
    model = vosk.Model(MODEL)
    rec = vosk.KaldiRecognizer(model, kwargs.get("samplerate"))

    out_q = deque(maxlen = OUT_LENGTH)
    async for indata, status in stream_generator(**kwargs):
        if status:
            print(status)
        out_q.append(indata.tobytes())
        out_data = b"".join(list(out_q))
        out_q.pop()

        text = await speech_to_text(rec, out_data)
        print(f"Parsed {text}")
        

async def main(**kwargs):
    print("creating audio task")
    audio_task = asyncio.create_task(wire_coro(**kwargs))
    for i in range(10, 0, -1):
        print(i)
        await asyncio.sleep(1)
    audio_task.cancel()
    try:
        await audio_task
    except asyncio.CancelledError:
        print('\nwire was cancelled')


if __name__ == "__main__":
    params = {
        "samplerate": 44100,
        "device": "hw:2,0",
        "blocksize": 1024
    }
    
    try:
        asyncio.run(main(**params))
    except KeyboardInterrupt:
        sys.exit('\nInterrupted by user')