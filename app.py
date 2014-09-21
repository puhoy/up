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
                filelist.append(filething(os.path.join(root, f)))
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
            return jsonify(name=file.filename,
                       size=os.path.getsize(filepath),
                       url=url_for('download', filename=filepath)
            )
            #return redirect(url_for('index'))
        else:
            return jsonify(error='ext name error')


@app.route('/dl/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    return send_from_directory(directory='', filename=filename)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def isImage(filename):
    imgExt=['jpg', 'jpeg', 'gif', 'svg']
    if '.' in filename and filename.rsplit('.', 1)[1] in imgExt:
        return True
    else:
        return False

'''
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        # we are expected to return a list of dicts with infos about the already available files:
        file_infos = []
        for file_name in list_files():
            file_url = url_for('download', file_name=file_name)
            file_size = get_file_size(file_name)
            file_infos.append(dict(name=file_name,
                                   size=file_size,
                                   url=file_url))
        return jsonify(files=file_infos)

    if request.method == 'POST':
        # we are expected to save the uploaded file and return some infos about it:
        #                              vvvvvvvvv   this is the name for input type=file
        data_file = request.files.get('data_file')
        file_name = data_file.filename
        save_file(data_file, file_name)
        file_size = get_file_size(file_name)
        file_url = url_for('download', file_name=file_name)
        # providing the thumbnail url is optional
        thumbnail_url = url_for('thumbnail', file_name=file_name)
        return jsonify(name=file_name,
                       size=file_size,
                       url=file_url,
                       thumbnail=thumbnail_url)
'''

if __name__ == "__main__":
    app.run(debug=True)
