import sys

try:
    import pyaudio
    print("PyAudio imported successfully!")
except ImportError:
    print("PyAudio NOT installed or import failed!", file=sys.stderr)

try:
    import vosk
    print("Vosk imported successfully!")
except ImportError:
    print("Vosk NOT installed or import failed!", file=sys.stderr) 