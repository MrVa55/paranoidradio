import requests
import time
from transcribe import record_audio, transcribe_audio
from summarize import summarize_text
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

ROWDYRADIO_URL = 'http://localhost:5001/generate'

def main():
    while True:
        # Record audio
        print("Listening...")
        duration = 45  # Duration in seconds
        samplerate = 96000  # Supported sample rate
        audio_data = record_audio(duration, samplerate=samplerate)
        
        # Transcribe audio
        transcribed_text = transcribe_audio(audio_data, samplerate=samplerate)
       

        # Save the transcribed text to a file for inspection
        with open('transcribed_text.txt', 'w') as f:
            f.write(transcribed_text)
        print("transcription ready")
        
        # Summarize text
        summary = summarize_text(transcribed_text)
        
        # Save the summary text to a file for inspection
        with open('summary_text.txt', 'w') as f:
            f.write(summary)
        
        # Generate prompt
        radio_prompt = f"A bluegrass jazz song about: {summary[:900]}"  # Ensure prompt is not too long
        
        # Send prompt to rowdyradio
        response = requests.post(ROWDYRADIO_URL, json={'method': 'prompt', 'prompt': radio_prompt})
        print(response.json())
        
        # Wait before recording again
        time.sleep(60)

if __name__ == '__main__':
    main()
