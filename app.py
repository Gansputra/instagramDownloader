from flask import Flask, render_template, request, send_file, redirect, url_for, after_this_request
import instaloader
import os
import shutil
import zipfile

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "static", "downloads")

@app.route('/reset')
def cleanup_and_home():
    try:
        if os.path.exists(DOWNLOAD_DIR):
            shutil.rmtree(DOWNLOAD_DIR)
            os.makedirs(DOWNLOAD_DIR)
    except Exception as e:
        print(f"Error reset cleanup: {e}")
    
    return redirect(url_for('index'))

@app.route('/', methods=['GET', 'POST'])
def index():
    media = []
    error = None
    
    if request.method == 'POST':
        url = request.form.get('url')
        if not url:
            return render_template('index.html', error="URL tidak boleh kosong")

        try:
            if os.path.exists(DOWNLOAD_DIR):
                shutil.rmtree(DOWNLOAD_DIR)
            os.makedirs(DOWNLOAD_DIR)

            L = instaloader.Instaloader(
                dirname_pattern=DOWNLOAD_DIR,
                save_metadata=False,
                quiet=True
            )

            clean_url = url.split('?')[0]          
            clean_url = clean_url.strip('/')            
            shortcode = clean_url.split('/')[-1]
            print(f"Mencoba download shortcode: {shortcode}") 

            post = instaloader.Post.from_shortcode(L.context, shortcode)
            L.download_post(post, target="")

            for file in sorted(os.listdir(DOWNLOAD_DIR)):
                if file.endswith('.jpg'):
                    media.append({'type': 'image', 'file': file})
                elif file.endswith('.mp4'):
                    media.append({'type': 'video', 'file': file})

            if not media:
                error = "Media tidak ditemukan atau akun private."
                return render_template('index.html', error=error)

            return render_template('preview.html', media=media)
            
        except Exception as e:
            print(f"Error: {e}")
            return render_template('index.html', error="Gagal fetch preview. Pastikan link benar/akun publik.")

    return render_template('index.html')

@app.route('/download', methods=['GET', 'POST'])
def download_zip():
    if request.method == 'GET':
        return redirect(url_for('index'))

    custom_name = request.form.get('zipname')
    if not custom_name:
        custom_name = "instagram_media"
    
    if not custom_name.endswith('.zip'):
        custom_name += '.zip'

    zip_path = os.path.join(BASE_DIR, custom_name)

    try:
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(DOWNLOAD_DIR):
                for file in files:
                    if file.endswith(('.jpg', '.mp4')):
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, arcname=file)

        @after_this_request
        def cleanup(response):
            try:
                if os.path.exists(DOWNLOAD_DIR):
                    shutil.rmtree(DOWNLOAD_DIR)
                    os.makedirs(DOWNLOAD_DIR) 
                
                if os.path.exists(zip_path):
                    os.remove(zip_path)
            except Exception as e:
                print(f"Error cleanup: {e}")
            return response

        return send_file(zip_path, as_attachment=True, download_name=custom_name)

    except Exception as e:
        print(f"Zip Error: {e}")
        return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
    app.run(debug=True)