#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from datetime import datetime
from flask import Flask, render_template, jsonify, redirect, url_for, request, send_from_directory, flash
from flask_bootstrap import Bootstrap
import time
import forms
import json
import humanize

import argparse


app = Flask(__name__)
app.config['CSRF_ENABLED'] = True
app.secret_key = os.urandom(24)
app.config.from_object(__name__)
Bootstrap(app)


basedir = os.path.abspath(os.path.dirname(__file__))
commentsfile='.comments.json'
tmp_prefix = '.tmp_'
ALLOWED_EXTENSIONS = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'svg', 'zip', 'mp3', 'flac', 'rar', 'tar', 'gz', 'tgz',
                      'avi', 'mpg', 'mkv']
MAXCOMMENTS = 15

parser = argparse.ArgumentParser()
parser.add_argument('-p', "--path", default=os.getcwd(), help='path to serve (if not given, current path will be served)')
# 1024^3 = 1073741824 = 1GB
parser.add_argument('-f', '--filesize', default=pow(1000, 3), help='default: '+str(pow(1000, 3)) )
parser.add_argument('-F', '--foldersize', default=pow(1000, 3)*10, help='default: '+str(pow(1000, 3)*10))
parser.add_argument('-e', '--extensions', default='')  # TODO
args = parser.parse_args()

if not os.path.isdir(args.path):
    print('no directory %s' % args.path)
    quit()

print('serving path: %s' % args.path)
print('max filesize: %s' % humanize.naturalsize(args.filesize))
print('max foldersize: %s' % humanize.naturalsize(args.foldersize))

app.config['UPLOAD_FOLDER'] = args.path
MAX_FILE = args.filesize
MAX_FOLDER = args.foldersize

if not os.path.isfile(commentsfile):
    open(commentsfile, 'a').close()

class filething():
    def __init__(self, path):
        self.realpath = os.path.join(app.config['UPLOAD_FOLDER'], path)
        self.path = path
        self.dirname = os.path.dirname(path)
        self.filename = os.path.basename(path)
        self.time = os.path.getmtime(self.realpath)
        self.humantime = time.strftime('%m/%d/%Y', time.gmtime(os.path.getmtime(self.realpath)))
        self.isImage = self.isImage()
        self.filesize = os.path.getsize(self.realpath)
        pass

    def delete(self):
        print("deleting " + self.realpath)
        print('deleting ' + os.path.dirname(self.realpath))
        os.remove(self.realpath)
        os.removedirs(os.path.dirname(self.realpath))
        del self

    def __repr__(self):
        return self.path

    def __getitem__(self, item):
        if item == 'filesize':
            return self.filesize
        else:
            return None

    def isImage(self):
        imgExt = ['jpg', 'jpeg', 'gif', 'svg', 'png']
        if '.' in self.filename and self.filename.split('.')[-1] in imgExt:
            return True
        else:
            return False



def getFileList():
    filelist = []
    for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER']):
        dirs.sort(reverse=True)

        path = os.path.normpath(os.path.join(root[len(app.config['UPLOAD_FOLDER'])+1:]))
        for f in files:
            if not f.startswith('.'):
                filelist.append(filething(os.path.join(path, f)))
            else:
                tdiff = datetime.today() - datetime.fromtimestamp(os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], path, f)))
                if tdiff.days > 2:
                    print("removing temp upload: " + str(os.path.join(app.config['UPLOAD_FOLDER'], path, f)) + " (" + str(tdiff.days) + " old)")
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], path, f))

    filelist.sort(key=lambda ft: ft.time, reverse=True)
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
    with open(commentsfile) as json_file:
        try:
            comments = json.load(json_file)
        except ValueError:
            comments = []
    return comments

def addComment(name, comment):
    now = datetime.now()
    c={}
    c['text'] = comment
    c['time'] = now.strftime("%Y-%m-%d-%H-%M-%S-%f")
    c['username'] = name
    allComments = getComments()
    while len(allComments) > MAXCOMMENTS:
        allComments.pop(0)
    allComments.append(c)
    with open(commentsfile, 'w') as outfile:
        json.dump(allComments, outfile)
    return allComments

@app.route("/comment", methods=['POST'])
def comment():
    if request.form['text'] != "":
        addComment(request.form['username'], request.form['text'])
    return jsonify({'status': "success"})

@app.route("/getcomments", methods=['POST'])
def getComment():
    allComments = getComments()
    allComments.reverse()
    #print(allComments)
    return jsonify({'all': allComments})

@app.route("/")
def index():
    commentform = forms.CommentForm()
    return render_template("index.html", files=getFileList(), extensions=ALLOWED_EXTENSIONS, max_fs=MAX_FILE, sz=MAX_FOLDER, cform=commentform )


def mvToUploadDir(filename):
    filepath = app.config['UPLOAD_FOLDER']
    newpath = os.path.join(filepath, filename)
    if os.path.isfile(newpath):
        cnt = 0
        while os.path.isfile(os.path.join(filepath, str(cnt) + '_' + filename)):
            cnt += 1
        newpath = os.path.join(filepath, str(cnt) + '_' + filename)
    os.rename(os.path.join(app.config['UPLOAD_FOLDER'], tmp_prefix + request.remote_addr + filename), newpath)
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
                if (fsize > MAX_FILE or fsize > MAX_FOLDER) \
                        and MAX_FILE is not 0:
                    flash('too large!')
                    return jsonify({'status': 'error'})
                if fsize + MAX_FOLDER > MAX_FOLDER:
                    delTillFit(fsize)

                # append chunk to the file on disk, or create new
                with open(os.path.join(app.config['UPLOAD_FOLDER'], tmp_prefix + request.remote_addr + filename), 'ab') as f:
                    f.seek(start_bytes)
                    str=value.stream.read()
                    f.write(str)

                if (fsize - end_bytes) == 1:
                    filename = mvToUploadDir(filename)
                else:
                    filename = os.path.join(app.config['UPLOAD_FOLDER'], tmp_prefix + request.remote_addr + filename)

            else:
                range_str = request.headers['Content-Length']
                fsize = int(range_str)
                if fsize + MAX_FOLDER > MAX_FOLDER:
                    delTillFit(fsize)
                # this is not a chunked request, so just save the whole file
                value.save(os.path.join(app.config['UPLOAD_FOLDER'], tmp_prefix + request.remote_addr + filename))
                filename = mvToUploadDir(filename)

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

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catchall(path):
    return redirect(url_for('index'))

def allowed_file(filename):
    return '.' in filename and filename.split('.')[-1] in ALLOWED_EXTENSIONS


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
