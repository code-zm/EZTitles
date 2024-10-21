2024-10-21 12:17

Tags: [[projects]], [[programming]], [[Klipped]]

# README.md

## EZTitles

EZ Titles is a Flask-based web application that allows users to automatically add aligned subtitles to videos with custom styling options. With this tool, you can upload videos, extract and transcribe audio, fine-tune subtitle appearance, and download the final video with embedded subtitles.

#### Features:
- Video Upload: Upload videos directly from your local system.
- Audio Transcription: Automatically transcribe the audio using Whisper AI.
- Subtitle Customization: Customize font, size, color, position, and word count for subtitles.
- Gentle Docker Integration: Use the Gentle tool for accurate alignment.
- TTS Option: Optionally generate a text-to-speech (TTS) version of the audio. (In development)

#### Folder Structure:
- `serve.py`: Main Python script for running the Flask application.
- `templates/index.html`: HTML interface for uploading videos and displaying results.
- `static/`: Directory for static files like Bootstrap and custom fonts.
- `uploads/`: Directory for storing uploaded videos and subtitle files.
- `gentle/`: Docker setup for Gentle alignment tool.
- `gentle_data/`: Directory for Gentle’s data (linked to Docker).
#### Prerequisites: 
- Python 3.8+ installed
- Docker ([Install Docker](https://docs.docker.com/get-docker/))
- ffmpeg installed: `sudo apt-get install ffmpeg`
- Gentle Docker Setup: Pull the Gentle Docker image from Docker Hub: 
`sudo docker pull lowerquality/gentle `

#### Installation and Setup:
  1. Clone the repository:
     ```bash
     git clone https://github.com/code-zm/EZTitles
     cd EZTitles
     ```
  2. Install Python dependencies:
     ```bash
     pip install -r requirements.txt
     ```
  3. Start the Gentle Docker container:
     ```bash
     sudo docker run -d -p 8765:8765 \
       -v $(pwd)/gentle_data:/gentle/data \
       --name gentle lowerquality/gentle
     ```
  4. Start the Flask server:
     ```bash
     python serve.py
     ```
  5. Access the app at: `http://localhost:5000`

#### Usage:
  1. Upload your MP4 video using the web interface.
  2. Generate subtitles and customize their appearance.
  3. Download the video with embedded subtitles.

#### Troubleshooting:
  - Gentle Docker Container: 
    If the Gentle container stops or fails, restart it with:
    ```bash
    sudo docker start gentle
    ```

  - Stopping the Container:  
    To stop the Gentle container when not in use:
    ```bash
    sudo docker stop gentle
    ```

#### Contributing:
  Feel free to fork the repository and submit pull requests.

#### License:
  This project is licensed under the MIT License.

