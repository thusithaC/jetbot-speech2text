import logging
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logger = logging.getLogger()

HOSTNAME = '127.0.0.1'
PORT = 9001

VERBOSE = 1
OUT_LENGTH = 20
MODEL = "models/vosk-model-small-en-us"

SAMPLE_RATE = 44100
DEVICE = "hw:2,0"
BLOCKSIZE = 1024