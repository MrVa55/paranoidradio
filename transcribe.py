# transcribe.py

import sounddevice as sd
import numpy as np
import queue
import soundfile as sf
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

q = queue.Queue()

def callback(indata, frames, time, status):
    q.put(indata.copy())

def record_audio(duration, samplerate=96000, device=1):  # Use Device ID 1
    device_info = sd.query_devices(device, 'input')
    channels = device_info['max_input_channels']
    with sd.InputStream(samplerate=samplerate, channels=channels, callback=callback, device=device):
        sd.sleep(duration * 1000)
        data = []
        while not q.empty():
            data.append(q.get())
        return np.concatenate(data)

def transcribe_audio(audio_data, samplerate=96000):
    # Save audio data to a file
    sf.write('recorded_audio.wav', audio_data, samplerate)
    
    # Transcribe audio using Whisper
    with open('recorded_audio.wav', 'rb') as audio_file:
        transcription = client.audio.transcriptions.create(file=audio_file, model="whisper-1")
    
    transcribed_text = transcription.text
    
    # Save the transcribed text to a file for inspection
    with open('transcribed_text.txt', 'w') as f:
        f.write(transcribed_text)
    
    return transcribed_text

if __name__ == '__main__':
    duration = 30  # Duration in seconds
    samplerate = 96000  # Supported sample rate
    audio_data = record_audio(duration, samplerate=samplerate, device=1)  # Use Device ID 1
    transcribed_text = transcribe_audio(audio_data, samplerate=samplerate)
    print(transcribed_text)
