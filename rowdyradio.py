import requests
import time
import os
import subprocess
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, SubmitField
from wtforms.validators import DataRequired
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read the API key from environment variables
API_KEY = os.getenv('API_KEY')
BASE_URL = 'https://api.sunoaiapi.com/api/v1/'

# Define headers for the API requests
headers = {
    'api-key': API_KEY,
    'Content-Type': 'application/json'
}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with your secret key
app.config['DEBUG'] = True

# Form class for the web interface
class SongForm(FlaskForm):
    method = RadioField('Generation Method', choices=[('prompt', 'Prompt'), ('title_tags', 'Title and Tags')], validators=[DataRequired()])
    title = StringField('Title')
    tags = StringField('Tags')
    prompt = StringField('Prompt')
    submit = SubmitField('Generate Song')

# Function to generate music using Suno AI API (GPT description)
def generate_music_gpt_desc(prompt, model='chirp-v3-5'):
    url = f'{BASE_URL}gateway/generate/gpt_desc'
    data = {
        'gpt_description_prompt': prompt,
        'mv': model
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        app.logger.info(f"Response from Suno AI API: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Request failed: {e}")
        return None

# Function to generate music using Suno AI API (Title and Tags)
def generate_music_title_tags(title, tags, model='chirp-v3-5'):
    url = f'{BASE_URL}gateway/generate/music'
    data = {
        'title': title,
        'tags': tags,
        'mv': model
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        app.logger.info(f"Response from Suno AI API: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Request failed: {e}")
        return None

# Function to check the generation result from Suno AI API
def check_result(song_id):
    url = f'{BASE_URL}gateway/feed/{song_id}'
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        app.logger.info(f"Check result response: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Request failed: {e}")
        return None

# Function to stream audio using ffmpeg
def stream_audio(audio_url):
    try:
        app.logger.info(f"Attempting to stream audio from {audio_url}")
        # Using ffmpeg to stream audio
        process = subprocess.Popen(
            ['ffplay', '-nodisp', '-autoexit', audio_url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        app.logger.info(f"ffplay stdout: {stdout}")
        app.logger.info(f"ffplay stderr: {stderr}")

        if process.returncode == 0:
            app.logger.info("Audio streaming finished")
        else:
            app.logger.error(f"ffplay error: {stderr}")
    except Exception as e:
        app.logger.error(f"Failed to stream audio: {e}")

# API endpoint to generate music
@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    method = data['method']
    
    if method == 'prompt':
        prompt = data['prompt']
        response = generate_music_gpt_desc(prompt)
    else:
        title = data['title']
        tags = data['tags']
        response = generate_music_title_tags(title, tags)
    
    if response and 'code' in response and response['code'] == 0:
        song_id = response['data'][0]['song_id']
        app.logger.info(f'Song generation submitted. Song ID: {song_id}')
        
        # Provide feedback to the user
        return jsonify({'message': 'Song generation started', 'song_id': song_id}), 202
    else:
        error_message = response.get('msg', 'Unknown error') if response else 'Failed to get a valid response from Suno AI API'
        app.logger.error(f"Error generating song: {error_message}")
        return jsonify({'error': error_message}), 500

# Web interface route
@app.route('/', methods=['GET', 'POST'])
def index():
    form = SongForm()
    if form.validate_on_submit():
        method = form.method.data
        if method == 'prompt':
            prompt = form.prompt.data
            response = generate_music_gpt_desc(prompt)
        else:
            title = form.title.data
            tags = form.tags.data
            response = generate_music_title_tags(title, tags)

        if response and 'code' in response and response['code'] == 0:
            song_id = response['data'][0]['song_id']
            app.logger.info(f'Song generation submitted. Song ID: {song_id}')
            flash('Song generation started. It will begin playing soon...', 'info')

            # Poll for the result every few seconds
            while True:
                result = check_result(song_id)
                if result and 'data' in result:
                    if result['data']['status'] == 'streaming':
                        audio_url = f"https://audiopipe.suno.ai/?item_id={song_id}"
                        app.logger.info(f'Song is streaming. Audio URL: {audio_url}')
                        
                        # Start streaming the audio
                        stream_audio(audio_url)
                        flash('Song is now playing!', 'success')
                        return redirect(url_for('index'))
                    elif result['data']['status'] == 'complete':
                        audio_url = result['data']['audio_url']
                        app.logger.info(f'Song generation complete. Audio URL: {audio_url}')
                        
                        # Stream the complete audio file
                        stream_audio(audio_url)
                        flash('Song generated and played successfully!', 'success')
                        return redirect(url_for('index'))
                    elif result['data']['status'] == 'error':
                        flash('Error during song generation.', 'danger')
                        return redirect(url_for('index'))
                    else:
                        app.logger.info('Song generation in progress. Checking again in a few seconds...')
                        time.sleep(5)
                else:
                    flash('Failed to get a valid response from Suno AI API.', 'danger')
                    return redirect(url_for('index'))
        else:
            error_message = response.get('msg', 'Unknown error') if response else 'Failed to get a valid response from Suno AI API'
            app.logger.error(f"Error generating song: {error_message}")
            flash(f"Error generating song: {error_message}", 'danger')
            return redirect(url_for('index'))
    
    return render_template('index.html', form=form)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
