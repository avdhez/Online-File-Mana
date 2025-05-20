import os
import zipfile
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this for production

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Simple user system (for demo only - use proper auth in production)
class User(UserMixin):
    def __init__(self, id):
        self.id = id

users = {'admin': {'password': 'password'}}  # Change for production

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
@login_required
def index():
    path = request.args.get('path', '')
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], path)
    
    if not os.path.exists(full_path):
        flash('Path does not exist', 'error')
        return redirect(url_for('index'))
    
    files = []
    directories = []
    
    for item in os.listdir(full_path):
        item_path = os.path.join(full_path, item)
        if os.path.isdir(item_path):
            directories.append({
                'name': item,
                'path': os.path.join(path, item)
            })
        else:
            files.append({
                'name': item,
                'size': os.path.getsize(item_path),
                'modified': os.path.getmtime(item_path)
            })
    
    parent_path = os.path.dirname(path) if path else None
    return render_template('index.html', 
                         files=files, 
                         directories=directories,
                         current_path=path,
                         parent_path=parent_path)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    path = request.form.get('path', '')
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], path)
    
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('index', path=path))
    
    files = request.files.getlist('file')
    
    for file in files:
        if file.filename == '':
            flash('No selected file', 'error')
            continue
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(full_path, filename))
        else:
            flash(f'File type not allowed: {file.filename}', 'error')
    
    return redirect(url_for('index', path=path))

@app.route('/download/<path:filename>')
@login_required
def download_file(filename):
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(full_path):
        flash('File not found', 'error')
        return redirect(url_for('index'))
    
    return send_file(full_path, as_attachment=True)

@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_file():
    path = request.args.get('path', '')
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], path)
    
    if not os.path.exists(full_path):
        flash('File not found', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        content = request.form.get('content', '')
        with open(full_path, 'w') as f:
            f.write(content)
        flash('File saved successfully', 'success')
        return redirect(url_for('index', path=os.path.dirname(path)))
    
    try:
        with open(full_path, 'r') as f:
            content = f.read()
    except UnicodeDecodeError:
        flash('File is not editable (binary file)', 'error')
        return redirect(url_for('index', path=os.path.dirname(path))))
    
    return render_template('edit.html', 
                         content=content, 
                         filename=os.path.basename(path),
                         path=path)

@app.route('/create_dir', methods=['POST'])
@login_required
def create_dir():
    path = request.form.get('path', '')
    dirname = request.form.get('dirname', '')
    
    if not dirname:
        flash('Directory name cannot be empty', 'error')
        return redirect(url_for('index', path=path))
    
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], path, dirname)
    
    try:
        os.makedirs(full_path, exist_ok=True)
        flash('Directory created successfully', 'success')
    except OSError as e:
        flash(f'Error creating directory: {str(e)}', 'error')
    
    return redirect(url_for('index', path=path))

@app.route('/delete', methods=['POST'])
@login_required
def delete():
    path = request.form.get('path', '')
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], path)
    
    if not os.path.exists(full_path):
        flash('Path does not exist', 'error')
        return redirect(url_for('index'))
    
    try:
        if os.path.isdir(full_path):
            os.rmdir(full_path)
            flash('Directory deleted successfully', 'success')
        else:
            os.remove(full_path)
            flash('File deleted successfully', 'success')
    except OSError as e:
        flash(f'Error deleting: {str(e)}', 'error')
    
    return redirect(url_for('index', path=os.path.dirname(path))))

@app.route('/zip', methods=['POST'])
@login_required
def zip_files():
    path = request.form.get('path', '')
    items = request.form.getlist('items')
    
    if not items:
        flash('No items selected', 'error')
        return redirect(url_for('index', path=path))
    
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], path)
    zip_filename = request.form.get('zipname', 'archive.zip')
    
    if not zip_filename.endswith('.zip'):
        zip_filename += '.zip'
    
    zip_path = os.path.join(full_path, zip_filename)
    
    try:
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for item in items:
                item_path = os.path.join(full_path, item)
                if os.path.isdir(item_path):
                    for root, dirs, files in os.walk(item_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, full_path)
                            zipf.write(file_path, arcname)
                else:
                    zipf.write(item_path, item)
        
        flash('Zip file created successfully', 'success')
    except Exception as e:
        flash(f'Error creating zip file: {str(e)}', 'error')
    
    return redirect(url_for('index', path=path))

@app.route('/unzip', methods=['POST'])
@login_required
def unzip_file():
    path = request.form.get('path', '')
    zip_item = request.form.get('zip_item')
    
    if not zip_item:
        flash('No zip file selected', 'error')
        return redirect(url_for('index', path=path))
    
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], path)
    zip_path = os.path.join(full_path, zip_item)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(full_path)
        flash('File unzipped successfully', 'success')
    except Exception as e:
        flash(f'Error unzipping file: {str(e)}', 'error')
    
    return redirect(url_for('index', path=path))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
