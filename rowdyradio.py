import requests
import time
import os
import subprocess
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, SubmitField
from wtforms.validators import DataRequired
from dotenv import load_dotenv
from threading import Thread, Lock
import signal
import sys

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

current_song = None
next_song = None
song_lock = Lock()

# Ensure the directory for saved songs exists
os.makedirs('saved_songs', exist_ok=True)

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
        response = requests.post(url, headers=headers, json=data)  # Fixed the closing parenthesis
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

# Function to download and save audio using requests
def download_audio(audio_url, song_id):
    try:
        response = requests.get(audio_url, stream=True)
        response.raise_for_status()
        file_path = f'saved_songs/{song_id}.mp3'
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return file_path
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Failed to download audio: {e}")
        return None

# Function to stream audio using ffmpeg
def stream_audio(audio_url):
    try:
        app.logger.info(f"Attempting to stream audio from {audio_url}")
        # Use ffmpeg to stream audio, specifying the ALSA device
        process = subprocess.Popen(
            ['ffmpeg', '-re', '-i', audio_url, '-f', 'alsa', '-ac', '2', 'hw:0,0'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        app.logger.info(f"ffmpeg stdout: {stdout}")
        app.logger.info(f"ffmpeg stderr: {stderr}")

        if process.returncode == 0:
            app.logger.info("Audio streaming finished")
        else:
            app.logger.error(f"ffmpeg error: {stderr}")
    except Exception as e:
        app.logger.error(f"Failed to stream audio: {e}")



# Background task to poll song status and manage queue
def poll_song_status():
    global current_song, next_song
    while True:
        with song_lock:
            if current_song:
                app.logger.info(f"Checking status of current song: {current_song['song_id']}")
                result = check_result(current_song['song_id'])
                if result and 'data' in result:
                    status = result['data']['status']
                    app.logger.info(f"Current song status: {status}")
                    if status == 'streaming':
                        audio_url = f"https://audiopipe.suno.ai/?item_id={current_song['song_id']}"
                        app.logger.info(f'Song is {status}. Audio URL: {audio_url}')
                        Thread(target=download_audio, args=(audio_url, current_song['song_id']), daemon=True).start()  # Download the song in the background
                        stream_audio(audio_url)
                        current_song = None  # Mark current song as played
                    elif status == 'complete':
                        audio_url = result['data']['audio_url']
                        app.logger.info(f'Song generation complete. Audio URL: {audio_url}')
                        Thread(target=download_audio, args=(audio_url, current_song['song_id']), daemon=True).start()  # Download the song in the background
                        stream_audio(audio_url)
                        current_song = None  # Mark current song as played
                    elif status == 'error':
                        app.logger.error(f'Error during song generation: {result["data"]["meta_error_msg"]}')
                        current_song = None  # Mark current song as played

            if not current_song and next_song:
                app.logger.info(f"Setting next song as current: {next_song['song_id']}")
                current_song = next_song
                next_song = None

        time.sleep(5)

# API endpoint to generate music
@app.route('/generate', methods=['POST'])
def generate():
    global current_song, next_song
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
        with song_lock:
            if not current_song:
                current_song = {'song_id': song_id, 'prompt': data['prompt']}
            else:
                next_song = {'song_id': song_id, 'prompt': data['prompt']}
        return jsonify({'message': 'Song generation started', 'song_id': song_id}), 202
    else:
        error_message = response.get('msg', 'Unknown error') if response else 'Failed to get a valid response from Suno AI API'
        app.logger.error(f"Error generating song: {error_message}")
        return jsonify({'error': error_message}), 500

# Web interface route
@app.route('/', methods=['GET', 'POST'])
def index():
    global current_song, next_song
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
            with song_lock:
                if not current_song:
                    current_song = {'song_id': song_id, 'prompt': form.prompt.data}
                else:
                    next_song = {'song_id': song_id, 'prompt': form.prompt.data}
        else:
            error_message = response.get('msg', 'Unknown error') if response else 'Failed to get a valid response from Suno AI API'
            app.logger.error(f"Error generating song: {error_message}")
            flash(f"Error generating song: {error_message}", 'danger')
            return redirect(url_for('index'))
    
    return render_template('index.html', form=form)

# Cleanup function to release resources
def cleanup():
    app.logger.info("Cleaning up before exit...")
    sys.exit(0)

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    cleanup()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    poll_thread = Thread(target=poll_song_status, daemon=True)
    poll_thread.start()
    app.run(host='0.0.0.0', port=5001)
