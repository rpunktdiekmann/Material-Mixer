import os 
import shutil
DELETE_UNZIPPED = True
IGNORE_SELF_FILE = True
BLACKLIST= ['__pycache__', '.git', '.gitignore', '.vscode', 'doku', 'README.md']

NAME = 'MaterialMixer_1_2_1'
LOC = r'D:\test_ship_python'
POST_FIX ='_release'

os.makedirs(os.path.join(LOC, NAME), exist_ok=True)
current_dir = os.path.dirname(__file__)
created_dirs = {}
for root, dirs, files in os.walk(current_dir, topdown=True):
    dirs[:] = [d for d in dirs if d not in BLACKLIST]
    for file in files:
        if IGNORE_SELF_FILE and file == os.path.basename(__file__):
            continue
        if file in BLACKLIST:
            continue
        
        a=os.path.relpath(root, current_dir)

        #shutil.copyfile(src, dst)
        if a != '.' and a not in created_dirs:
            os.makedirs(os.path.join(LOC,NAME, a), exist_ok=True)
        src = os.path.join(root, file)
        dst = os.path.join(LOC,NAME, a, file)
        shutil.copyfile(src, dst)



shutil.make_archive(NAME+POST_FIX, 'zip', os.path.join(LOC,NAME))
if DELETE_UNZIPPED:
    shutil.rmtree(os.path.join(LOC,NAME))