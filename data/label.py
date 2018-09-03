import os
from os import listdir, getcwd
from os.path import join

f=open('train.txt', 'w')
#wd = getwd()
tmp = 'data/obj/'
for jpgfile in os.listdir('./obj'):
    if 'jpg' in jpgfile:
        f.write(tmp+jpgfile+'\n')
print("complete")
f.close
