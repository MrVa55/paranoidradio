from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def summarize_text(transcribed_text):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Please summarize the following conversation in 3 sentences: {transcribed_text}"}
        ]
    )
    summary = response.choices[0].message.content
    
    # Save the summary to a file for inspection
    with open('summary_text.txt', 'w') as f:
        f.write(summary)
    
    return summary

if __name__ == '__main__':
    transcribed_text = "Your transcribed text here"
    summary = summarize_text(transcribed_text)
    print(summary)
