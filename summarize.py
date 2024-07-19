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
            {"role": "system", "content": "You are part of a radio that listens to conversations and writes songs about it. You will get a transcript of the conversation and will need to make a prompt for a songwriting AI. This prompt should be 150 charachters. You will want to ask for titles that are built on central sentences quoted verbatim, so you cannot miss that the conversation is being repeated even if you dont know. The style should be jazz"},
            {"role": "user", "content": f"Here is the latest conversation: {transcribed_text}"}
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
