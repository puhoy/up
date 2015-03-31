# Up


![Screenshot](screenshot.png?raw=true)

##Installation
### Requirements
- python3 (+virtualenv) and pip :)

###with venv
    # cloning
    git clone https://github.com/puhoy/up.git
    cd up
    # create a virtualenv
    pyvenv-3.4 venv
    source venv/bin/activate
    # install requirements
    pip install -r requirements.txt
    

##running
    python3 up.py --path=/path/to/serve

###Options
    '-p', "--path", default=os.getcwd()
    '-f', '--filesize', default=pow(1000, 3)  # 1GB
    '-F', '--foldersize', default=pow(1000, 3)*10  # 10GB


Note that the oldest files will be deleted if a new upload doesnt fit!
