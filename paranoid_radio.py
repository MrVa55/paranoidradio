# paranoid_radio.py

import time
import requests
from transcribe import record_audio, transcribe_audio
from summarize import summarize_text

def main():
    while True:
        # Record audio
        duration = 30  # Duration in seconds
        samplerate = 96000  # Supported sample rate
        audio_data = record_audio(duration, samplerate=samplerate, device=1)  # Use Device ID 1
        
        # Transcribe audio
        transcribed_text = transcribe_audio(audio_data, samplerate=samplerate)
        
        # Save the transcribed text to a file for inspection
        with open('transcribed_text.txt', 'w') as f:
            f.write(transcribed_text)
        
        # Summarize text
        summary = summarize_text(transcribed_text)
        
        # Save the summary text to a file for inspection
        with open('summary_text.txt', 'w') as f:
            f.write(summary)
        
        # Generate prompt
        radio_prompt = f"The next song should be about the following topic: {summary[:1000]}"  # Ensure prompt is not too long
        
        # Send prompt to rowdyradio
        response = requests.post('http://localhost:5001/generate', json={'method': 'prompt', 'prompt': radio_prompt})
        print(response.json())
        
        # Wait before recording again
        time.sleep(60)

if __name__ == '__main__':
    main()
