#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from datetime import datetime
from flask import Flask, render_template, jsonify, redirect, url_for, request, send_from_directory
from flask_bootstrap import Bootstrap
import time
import tempfile

app = Flask(__name__)
app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = os.path.normpath('/home/meatpuppet/Daten/Up/')
tmp_prefix='.tmp_'

Bootstrap(app)

ALLOWED_EXTENSIONS = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'svg', 'zip', 'mp3', 'rar', 'tar', 'gz', 'deb', 'avi',
        'mpg', 'mkv']


class filething():
    def __init__(self, path):
        realpath = os.path.join(app.config['UPLOAD_FOLDER'], path)
        self.path=path
        self.dirname = os.path.dirname(path)
        self.filename = os.path.basename(path)
        self.time = time.strftime('%m/%d/%Y', time.gmtime(os.path.getmtime(realpath)))
        self.isImage = isImage(self.filename)

        self.filesize=os.path.getsize(realpath)

        pass

    def __repr__(self):
        return self.path

@app.route("/")
def index():
    filelist = []
    for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER']):
        dirs.sort(reverse=True)
        for f in files:
            if not f.startswith('.'):
                path = os.path.normpath(os.path.join(root[len(app.config['UPLOAD_FOLDER'])+1:]))
                print path
                filelist.append(filething(os.path.join(path, f)))
    return render_template("index.html", files=filelist, extensions=ALLOWED_EXTENSIONS)


def mvToUploadDir(filename):
    now = datetime.now()
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], "%s" % (now.strftime("%Y-%m-%d-%H-%M-%S-%f")))
    os.mkdir(filepath)
    newpath=os.path.join(filepath, filename)
    os.rename(os.path.join(app.config['UPLOAD_FOLDER'], tmp_prefix + filename), newpath )
    return newpath


@app.route('/upload', methods=['POST'])
def upload():

    if request.method == 'POST':
        files = request.files

        # assuming only one file is passed in the request
        key = files.keys()[0]
        value = files[key] # this is a Werkzeug FileStorage object
        filename = value.filename

        if 'Content-Range' in request.headers:
            # extract starting byte from Content-Range header string
            range_str = request.headers['Content-Range']
            start_bytes = int(range_str.split(' ')[1].split('-')[0])
            end_bytes= int(range_str.split(' ')[1].split('-')[1].split('/')[0])
            fsize = int(range_str.split(' ')[1].split('-')[1].split('/')[1])
            # append chunk to the file on disk, or create new
            with open(os.path.join(app.config['UPLOAD_FOLDER'], tmp_prefix + filename), 'a') as f:
                f.seek(start_bytes)
                f.write(value.stream.read())

            if (fsize - end_bytes) == 1:
                filename=mvToUploadDir(filename)



        else:
            # this is not a chunked request, so just save the whole file
            value.save(filename)
            filename=mvToUploadDir(filename)

            # send response with appropriate mime type header
        return jsonify({"name": value.filename,
                    "size": os.path.getsize(filename),
                    "url": 'uploads/' + value.filename,
                    "thumbnail_url": None,
                    "delete_url": None,
                    "delete_type": None,})




'''
        print tempfile.gettempdir()
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
'''

@app.route('/downloads/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    return send_from_directory(directory=app.config['UPLOAD_FOLDER'], filename=filename)


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
    app.run(debug=True, host='0.0.0.0', port=8080)
