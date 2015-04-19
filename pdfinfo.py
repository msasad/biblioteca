import sys
from subprocess import call, Popen, PIPE
from os import listdir, path

def toDict(string):
    temp = string.split(':')
    return (temp[0],temp[1])

def getFileInfo(filename):
    info = Popen('pdfinfo "' + filename + '"', shell=True, stdout=PIPE).stdout.read().splitlines()
    return dict(map(toDict, info))

def getFileInfoFromDir(location):
    l = list()
    for i in listdir(location):
        if i.endswith('.pdf'):
            l.append(getFileInfo(path.join(location, i)))
    return l

if __name__ == '__main__':
    location = sys.argv[1]
    print getFileInfoFromDir(location)
