#!/usr/bin/env python3.8

# pythonn  tests/test_microphone.py --filename tests/data/test_record.wav --model models/vosk-model-small-en-us --device "hw:2,0" --samplerate 44100 --rectime 10

import argparse
import os
import queue
import sounddevice as sd
import vosk
import sys
from collections import deque

BLOCKS_TO_PARSE = 10

q = queue.Queue()
parse_q = deque(maxlen=BLOCKS_TO_PARSE)

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    '-l', '--list-devices', action='store_true',
    help='show list of audio devices and exit')
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    '-f', '--filename', type=str, metavar='FILENAME',
    help='audio file to store recording to')
parser.add_argument(
    '-m', '--model', type=str, metavar='MODEL_PATH',
    help='Path to the model')
parser.add_argument(
    '-d', '--device', type=int_or_str,
    help='input device (numeric ID or substring)')
parser.add_argument(
    '-r', '--samplerate', type=int, help='sampling rate', default=44100)
parser.add_argument(
    '-t', '--rectime', type=int, help='number seconds to record', default=5)
args = parser.parse_args(remaining)


def consume_stream(args, concat = False):
    model = vosk.Model(args.model)

    if args.filename:
        dump_fn = open(args.filename, "wb")
    else:
        dump_fn = None

    with sd.RawInputStream(samplerate=args.samplerate, blocksize = 5000, device=args.device, dtype='int16',
                            channels=1, callback=callback):
            print('#' * 80)
            print('Press Ctrl+C to stop the recording')
            print('#' * 80)

            rec = vosk.KaldiRecognizer(model, args.samplerate)
            while True:
                
                data = q.get()
                parse_q.append(data)
                if concat:
                    data = b"".join(list(parse_q))

                if rec.AcceptWaveform(data):
                    print(rec.Result())
                else:
                    print(rec.PartialResult())
                if dump_fn is not None:
                    dump_fn.write(data)


def consume_recording(args):
    model = vosk.Model(args.model)

    if args.filename:
        dump_fn = open(args.filename, "wb")
    else:
        dump_fn = None

    duration = 5  # seconds
    recording = sd.rec(int(duration * args.samplerate), samplerate=args.samplerate, channels=1, dtype = 'int16')
    print('#' * 80)
    print('Press Ctrl+C to stop the recording')
    print('#' * 80)
    sd.wait()
    data = recording.tobytes()
    rec = vosk.KaldiRecognizer(model, args.samplerate)
    if rec.AcceptWaveform(data):
        print(rec.Result())
    else:
        print(rec.PartialResult())
    if dump_fn is not None:
        dump_fn.write(data)



try:
    if args.model is None:
        args.model = "model"
    if not os.path.exists(args.model):
        print ("Please download a model for your language from https://alphacephei.com/vosk/models")
        print ("and unpack as 'model' in the current folder.")
        parser.exit(0)
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, 'input')
        # soundfile expects an int, sounddevice provides a float:
        args.samplerate = int(device_info['default_samplerate'])

    consume_recording(args)

except KeyboardInterrupt:
    print('\nDone')
    parser.exit(0)
except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))
