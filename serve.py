from flask import Flask, request, jsonify, render_template, send_file
import os
import io
import whisper
import subprocess
import requests
import time
import datetime
import json
import signal
import numpy as np
import soundfile as sf
import re
import threading

app = Flask(__name__)

GENTLE_SERVER_URL = "http://localhost:8765/transcriptions"

# Global variables to store state
AUDIO_STREAM = io.BytesIO()  # Use an in-memory stream to store audio
VIDEO_PATH = ""  # Store the original video path
OUTPUT_VIDEO_PATH = ""  # Store the path for the output video
PROGRESS = {"status": 0}  # Global variable to track progress

# Ensure the uploads directory exists
os.makedirs('uploads', exist_ok=True)

def start_gentle_container():
    # Check if a container with the name 'gentle' exists (running or stopped)
    check_command = ["docker", "ps", "-a", "--filter", "name=gentle", "--format", "{{.ID}}"]
    result = subprocess.run(check_command, stdout=subprocess.PIPE, text=True)
    container_id = result.stdout.strip()
    
    # If a container with the name 'gentle' exists, remove it
    if container_id:
        print(f"Removing existing container with ID: {container_id}")
        remove_command = ["sudo", "docker", "rm", "-f", container_id]
        subprocess.run(remove_command, check=True)

    # Start a new 'gentle' container
    print("Starting Gentle Docker container...")
    start_command = [
        "sudo", "docker", "run", "-d", "-p", "8765:8765",
        "-v", f"{os.getcwd()}/gentle_data:/gentle/data",
        "--name", "gentle",
        "-it", "lowerquality/gentle"
    ]
    subprocess.run(start_command, check=True)
    print("Gentle Docker container started.")

def stop_gentle_container():
    print("Stopping Gentle Docker container...")
    stop_command = ["sudo", "docker", "stop", "gentle"]
    subprocess.run(stop_command, check=True)
    print("Gentle Docker container stopped.")

def handle_exit(sig, frame):
    # Handle ^C (SIGINT)
    print("Interrupt received, stopping Gentle Docker container...")
    stop_gentle_container()
    exit(0)

# Register the signal handler for SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, handle_exit)

def run_gentle():
    # Run the start_gentle_container function before Flask starts
    start_gentle_container()

# Route for the home page to serve the HTML file
@app.route('/')
def index():
    return render_template('index.html')  # Make sure 'index.html' is in the 'templates' folder

@app.route('/transcribe', methods=['POST'])
def transcribe():
    global VIDEO_PATH, AUDIO_STREAM, PROGRESS
    PROGRESS['status'] = 0

    video_file = request.files['video']
    VIDEO_PATH = os.path.join('uploads', video_file.filename)
    video_file.save(VIDEO_PATH)
    PROGRESS['status'] = 20  # Update after saving video

    # Extract audio to an in-memory stream using ffmpeg
    AUDIO_STREAM = io.BytesIO()
    ffmpeg_command = [
        'ffmpeg', '-i', VIDEO_PATH, '-ar', '16000', '-ac', '1', '-q:a', '0', '-map', 'a', '-f', 'wav', 'pipe:1'
    ]
    
    process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    audio_data, _ = process.communicate()
    AUDIO_STREAM.write(audio_data)
    AUDIO_STREAM.seek(0)
    PROGRESS['status'] = 50  # Update after extracting audio

    # Convert AUDIO_STREAM to a NumPy array for Whisper
    audio_np, _ = sf.read(AUDIO_STREAM)
    audio_np = audio_np.astype(np.float32)

    model = whisper.load_model("base")
    result = model.transcribe(audio_np)
    transcription_text = result['text']
    PROGRESS['status'] = 80  # Update after transcription

    PROGRESS['status'] = 100  # Transcription complete
    return jsonify({"status": "Transcription complete", "transcription": transcription_text})

@app.route('/align', methods=['POST'])
def align():
    global VIDEO_PATH, OUTPUT_VIDEO_PATH, PROGRESS
    PROGRESS['status'] = 0

    data = request.get_json()
    transcription_text = data.get('transcription', '')
    word_count = int(data.get('word_count', 5))  # Default to 5 words per subtitle if not specified
    font = data.get('font', 'Arial')
    font_size = int(data.get('font_size', 24))
    font_color = data.get('font_color', '#ffffff')
    subtitle_position = data.get('subtitle_position', 'bottom')

    if not VIDEO_PATH or not transcription_text:
        return jsonify({"error": "No transcription available. Please generate or edit the transcription before alignment."})

    alignment_result = align_with_gentle(AUDIO_STREAM, transcription_text)
    PROGRESS['status'] = 50  # Update after alignment is complete

    if alignment_result:
        srt_file_path = os.path.join('uploads', 'output.srt')
        create_srt_file(alignment_result, srt_file_path, word_count)

        if not os.path.exists(srt_file_path):
            return jsonify({"error": "Subtitle file could not be created."})

        if not VIDEO_PATH.endswith('.mp4'):
            converted_video_path = VIDEO_PATH.rsplit('.', 1)[0] + '.mp4'
            convert_command = [
                'ffmpeg', '-i', VIDEO_PATH, '-c:v', 'libx264', '-crf', '23', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '192k', converted_video_path
            ]
            try:
                subprocess.run(convert_command, check=True)
                VIDEO_PATH = converted_video_path
            except subprocess.CalledProcessError as e:
                return jsonify({"error": f"Error converting video: {e}"})

        OUTPUT_VIDEO_PATH = VIDEO_PATH.replace('.mp4', '_with_subs.mp4')
        try:
            overlay_subtitles_on_video(VIDEO_PATH, srt_file_path, OUTPUT_VIDEO_PATH, font, font_size, font_color, subtitle_position)
            PROGRESS['status'] = 100
            return jsonify({"status": "Alignment complete", "video_with_subs": OUTPUT_VIDEO_PATH})
        except subprocess.CalledProcessError as e:
            return jsonify({"error": f"Error adding subtitles: {e}"})
    else:
        return jsonify({"error": "Error processing the alignment. Please check the Gentle server or try again."})

@app.route('/download', methods=['GET'])
def download():
    global OUTPUT_VIDEO_PATH
    if OUTPUT_VIDEO_PATH and os.path.exists(OUTPUT_VIDEO_PATH):
        return send_file(OUTPUT_VIDEO_PATH, as_attachment=True)
    else:
        return jsonify({"error": "No video available for download."})

@app.route('/progress', methods=['GET'])
def progress():
    global PROGRESS
    return jsonify(PROGRESS)

if __name__ == '__main__':
    run_gentle()  # Start the Gentle container
    app.run(host='0.0.0.0', port=5000, debug=True)

