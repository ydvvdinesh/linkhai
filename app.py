from flask import Flask, render_template, request, jsonify, send_from_directory
import yt_dlp
import os
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Setup the download directory
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def sanitize_filename(title):
    """Remove invalid characters and extra spaces from the filename."""
    title = re.sub(r'[\\/*?:"<>|]', "", title)  # Remove forbidden characters
    title = re.sub(r'\s+', " ", title).strip()  # Remove extra spaces
    return title

def download_video(url, resolution="best"):
    """Download YouTube video in the specified resolution."""
    ydl_opts = {
        'format': f'bestvideo[height<={resolution}]+bestaudio/best' if resolution != "best" else "best",
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'merge_output_format': 'mp4',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = sanitize_filename(info['title']) + ".mp4"
            final_path = os.path.join(DOWNLOAD_FOLDER, filename)
            os.rename(info['requested_downloads'][0]['filepath'], final_path)
            return filename
    except Exception as e:
        print(f"❌ Video Download Error: {str(e)}")
        return None

def download_audio(url):
    """Download only the audio as an MP3 file."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = sanitize_filename(info['title']) + ".mp3"
            final_path = os.path.join(DOWNLOAD_FOLDER, filename)
            os.rename(info['requested_downloads'][0]['filepath'], final_path)
            return filename
    except Exception as e:
        print(f"❌ Audio Download Error: {str(e)}")
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    """Handle download requests from frontend."""
    data = request.json
    url = data.get("url")
    file_type = data.get("type")

    if not url or not file_type:
        return jsonify({"error": "Missing URL or type"}), 400

    try:
        filename = None
        if file_type == "video":
            resolution = data.get("resolution", "best")
            filename = download_video(url, resolution)
        else:
            filename = download_audio(url)

        if filename:
            return jsonify({"status": "success", "filename": filename})
        else:
            return jsonify({"error": "Failed to download file"}), 500

    except Exception as e:
        print(f"❌ Backend Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/download-file')
def download_file():
    """Serve the downloaded file."""
    filename = request.args.get("filename")
    if not filename:
        return jsonify({"error": "Filename not provided"}), 400

    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return jsonify({"error": "File not found"}), 404

    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))  # Automatically detect the port for Render
    app.run(host='0.0.0.0', port=port, debug=True)
