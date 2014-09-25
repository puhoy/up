#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from datetime import datetime
from flask import Flask, render_template, jsonify, redirect, url_for, request, send_from_directory, flash
from flask_bootstrap import Bootstrap
import time
import forms
import json

app = Flask(__name__)
app.config.from_object(__name__)
Bootstrap(app)
CSRF_ENABLED = True
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['UPLOAD_FOLDER'] = os.path.normpath('/home/meatpuppet/Daten/Up/')
app.config['SECRET_KEY'] = 'IAMASUPERSECRETKEY'
tmp_prefix = '.tmp_'
ALLOWED_EXTENSIONS = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'svg', 'zip', 'mp3', 'flac', 'rar', 'tar', 'gz', 'tgz',
                      'avi', 'mpg', 'mkv']
# 1024^3 = 1073741824 = 1GB
MAX_FILE = pow(1000, 3)
MAX_FOLDER = 1073741824*10

class filething():
    def __init__(self, path):
        self.realpath = os.path.join(app.config['UPLOAD_FOLDER'], path)
        self.path=path
        self.dirname = os.path.dirname(path)
        self.filename = os.path.basename(path)
        self.time = time.strftime('%m/%d/%Y', time.gmtime(os.path.getmtime(self.realpath)))
        self.isImage = isImage(self.filename)

        self.filesize=os.path.getsize(self.realpath)

        pass

    def delete(self):
        print "deleting " + self.realpath
        print 'deleting ' + os.path.dirname(self.realpath)
        os.remove(self.realpath)
        os.removedirs(os.path.dirname(self.realpath))
        del(self)

    def __repr__(self):
        return self.path

    def __getitem__(self, item):
        if item == 'filesize':
            return self.filesize
        else:
            return None


def getFileList():
    filelist = []
    for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER']):
        dirs.sort(reverse=True)
        for f in files:
            if not f.startswith('.'):
                path = os.path.normpath(os.path.join(root[len(app.config['UPLOAD_FOLDER'])+1:]))
                filelist.append(filething(os.path.join(path, f)))
    return filelist

def getUsedSpace():
    sz=0
    for item in getFileList():
        sz+=item.filesize
    return sz

def delTillFit(size):
    used = getUsedSpace()
    files = getFileList()
    while used+size > MAX_FOLDER:
        used = used - files[-1].filesize
        files[-1].delete()

def getComments():
    with open("comments.json") as json_file:
        try:
            comments = json.load(json_file)
        except ValueError:
            comments = []
    return comments

def addComment(name, comment):
    now = datetime.now()
    c={}
    c['text']=comment
    c['time']=now.strftime("%Y-%m-%d-%H-%M-%S-%f")
    c['username'] = name
    allComments = getComments()
    allComments.append(c)
    with open('comments.json', 'w') as outfile:
        json.dump(allComments, outfile)
    return allComments

@app.route("/comment", methods=['POST'])
def comment():
    addComment(request.form['username'], request.form['text'])
    return jsonify({'status': "success"})

@app.route("/getcomments", methods=['POST'])
def getComment():
    allComments = getComments()
    allComments.reverse()
    print allComments
    return jsonify({'all': allComments})

@app.route("/")
def index():
    commentform = forms.CommentForm()
    return render_template("index.html", files=getFileList(), extensions=ALLOWED_EXTENSIONS, max_fs=MAX_FILE, sz=MAX_FOLDER, cform=commentform )

def mvToUploadDir(filename):
    now = datetime.now()
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], "%s" % (now.strftime("%Y-%m-%d-%H-%M-%S-%f")))
    os.mkdir(filepath)
    newpath=os.path.join(filepath, filename)
    os.rename(os.path.join(app.config['UPLOAD_FOLDER'], tmp_prefix + filename), newpath)
    return newpath

@app.route('/upload', methods=['POST'])
def upload():

    if request.method == 'POST':
        files = request.files

        # assuming only one file is passed in the request
        for key in files.keys():
            value = files[key] # this is a Werkzeug FileStorage object
            filename = value.filename

            if 'Content-Range' in request.headers:
                # extract starting byte from Content-Range header string
                range_str = request.headers['Content-Range']
                start_bytes = int(range_str.split(' ')[1].split('-')[0])
                end_bytes = int(range_str.split(' ')[1].split('-')[1].split('/')[0])
                fsize = int(range_str.split(' ')[1].split('-')[1].split('/')[1])
                if fsize > MAX_FILE:
                    print "too large!"
                    flash('too large!')
                    return jsonify({'status': 'error'})
                if fsize + MAX_FOLDER > MAX_FOLDER:
                    delTillFit(fsize)

                # append chunk to the file on disk, or create new
                with open(os.path.join(app.config['UPLOAD_FOLDER'], tmp_prefix + filename), 'a') as f:
                    f.seek(start_bytes)
                    f.write(value.stream.read())

                if (fsize - end_bytes) == 1:
                    filename=mvToUploadDir(filename)
                else:
                    filename=os.path.join(app.config['UPLOAD_FOLDER'], tmp_prefix + filename)

            else:
                range_str = request.headers['Content-Length']
                print range_str
                fsize = int(range_str)
                print fsize
                if fsize + MAX_FOLDER > MAX_FOLDER:
                    delTillFit(fsize)
                # this is not a chunked request, so just save the whole file
                value.save(os.path.join(app.config['UPLOAD_FOLDER'], tmp_prefix + filename))
                filename=mvToUploadDir(filename)

                # send response with appropriate mime type header
        return jsonify({"name": value.filename,
                    "size": os.path.getsize(filename),
                    "url": 'uploads/' + value.filename,
                    "thumbnail_url": None,
                    "delete_url": None,
                    "delete_type": None,})

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

if __name__ == "__main__":
    if not os.path.isfile('comments'):
        open('comments.json', 'a').close()
    app.run(debug=True, host='0.0.0.0', port=8080)
