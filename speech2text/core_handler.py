import asyncio
from collections import deque
import numpy as np
import sounddevice as sd
from speech2text.vosk_model import speech_to_text, get_recognizer

from config import (
    logger, 
    OUT_LENGTH,
    DEVICE,
    BLOCKSIZE
)


def get_output_queue():
    return asyncio.Queue()


async def stream_generator(dtype='int16', channels=1):
    """Generator that yields blocks of input/output data as NumPy arrays.
    The output blocks are uninitialized and have to be filled with
    appropriate audio signals.
    """
    logger.info("setting up stream generator")
    q_in = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def callback(indata, frame_count, time_info, status):
        loop.call_soon_threadsafe(q_in.put_nowait, (indata.copy(), status))

    stream = sd.InputStream(blocksize=BLOCKSIZE, callback=callback, dtype=dtype, channels=channels, device=DEVICE)
    with stream:
        while True:
            indata, status = await q_in.get()
            yield indata, status
            

async def listen_stream(text_queue: asyncio.Queue):
    """
    listens to the stream and convert to text. 

    Asynchronously iterates over a stream generator and for each block
    simply copies the input data into the output block.

    """
    recognizer = get_recognizer()

    temp_buffer = deque(maxlen = OUT_LENGTH)
    async for indata, status in stream_generator():
        if status:
            logger.debug(f"status {status}")
        temp_buffer.append(indata.tobytes())
        data = b"".join(list(temp_buffer))
        temp_buffer.pop()
        text = await speech_to_text(recognizer, data)
        await text_queue.put(text)
