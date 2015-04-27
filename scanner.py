from hurry.filesize import size
import threading
import sqlite3 as lite
from os import listdir, path, walk
from pdfinfo import getFileInfo


class FT(threading.Thread):
    def __init__(self, target, *args):
        self._target = target
        self._args = args
        threading.Thread.__init__(self)
    
    def run(self):
        self._target(*self._args)

def scanFiles(dbpath, pathtoscan, liststore, recursive = False):
    conn = lite.connect(path.join(dbpath, 'biblioteca.db'))
    files = dict()
    if recursive:
        dirtree = walk(pathtoscan)
        for entry in dirtree:
            files[entry[0]] = [i for i in entry[2] if i.endswith('.pdf')]
    else:
        files[pathtoscan] = [f for f in listdir(pathtoscan) if f.endswith('.pdf') ]
    for fpath in files.keys():
        for f in files[fpath]:
            print "opening " + f
            filepath = path.join(fpath, f)
            sizeinbytes = path.getsize(filepath)
            filesize = size(sizeinbytes)
            info = getFileInfo(filepath)
            templist = [info.get('Title',''), f, info.get('Author',''), int(info['Pages']), filepath, filesize, None, None, 0, sizeinbytes]
            #templist = [unicode(info.get('Title','')), unicode(f), unicode(info.get('Author','')), int(info['Pages']), unicode(filepath), filesize, None, None, 0, sizeinbytes]
            #templist = [unicode(a) if type(a)=='str' else a for a in templist]
            print templist
            liststore.append(templist)
            cmd = "insert into catalog values('{0}','{1}','{2}',{3},'{4}','{5}','{6}','{7}',{8}, {9})" .format(*tuple(i if i != None else '' for i in templist))
            try:
                cur = conn.execute(cmd)
            except lite.Error, e:
                print "Sqlite Error" + e.message
    conn.commit()