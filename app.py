#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from datetime import datetime
from flask import Flask, render_template, jsonify, redirect, url_for, request, send_from_directory
from flask_bootstrap import Bootstrap
import time

app = Flask(__name__)
app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
Bootstrap(app)

ALLOWED_EXTENSIONS = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'svg', 'zip', 'mp3', 'rar']

class filething():
    def __init__(self, path):
        self.path = path
        self.dirname = os.path.dirname(path)
        self.filename = os.path.basename(path)
        self.time = time.strftime('%m/%d/%Y', time.gmtime(os.path.getmtime(path)))
        self.isImage = isImage(self.filename)
        pass

    def __repr__(self):
        return self.path



@app.route("/")
def index():
    filelist = []
    for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER']):
        dirs.sort(reverse=True)
        for f in files:
            print f
            if not f.startswith('.'):
                print 'mhm'
                filelist.append(filething(os.path.join(root, f)))
    print filelist
    return render_template("index.html", files=filelist)

@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            now = datetime.now()
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], "%s" % (now.strftime("%Y-%m-%d-%H-%M-%S-%f")))
            os.mkdir(filepath)
            filename = os.path.join(filepath, file.filename)
            file.save(filename)
            return redirect(url_for('index'))
        else:
            return jsonify(error='ext name error')


@app.route('/dl/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    print filename
    return send_from_directory(directory='', filename=filename)



'''
@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        files = request.files.getlist('file[]')
        for f in files:
            if f and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                updir = os.path.join(basedir, 'upload/')
                f.save(os.path.join(updir, filename))
                file_size = os.path.getsize(os.path.join(updir, filename))
            else:
                app.logger.info('ext name error')
                return jsonify(error='ext name error')
        return jsonify(name=filename, size=file_size)
'''

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def isImage(filename):
    imgExt=['jpg', 'jpeg', 'gif', 'svg']
    if '.' in filename and filename.rsplit('.', 1)[1] in imgExt:
        return True
    else:
        return False

if __name__ == "__main__":
    app.run(debug=True)
