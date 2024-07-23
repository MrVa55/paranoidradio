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
            {"role": "system", "content": "You are part of a radio that listens to conversations and writes songs about it at the Borderland. The point is that the speakers should be surprised that the content of their conversation is in the lyrics. You will get a transcript of the conversation and need to summarize what is about as accurately as possible as a prompt for a songwriting AI. The prompt you return should be less than 200 charachters. Try to match closely the content of the conversation into the prompt, while including the context that it is happening at The Borderland. "},
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
