#!/usr/bin/env python

#import cgi
import sort
from hurry.filesize import size
from subprocess import call
from gi.repository import Gtk
from os import listdir, path, system, getcwd, getenv
from gi.repository import Gdk
import PyPDF2
import sqlite3 as lite
import threading
from ConfigParser import SafeConfigParser

class LibraryApp:
    def __init__(self):
        appdir = path.realpath(__file__)
        self.appdir = appdir.rstrip(path.basename(appdir))
        self.modstate = 4
        self.initUI()
        self.initDB()
        Gtk.main()

    class scanfiles(threading.Thread):
        def __init__(self, app, fpath):
            threading.Thread.__init__(self)
            self.a = app
            self.fpath = fpath
        def run(self):
            self.a.findfiles(self.fpath)

    def initUI(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(path.join(self.appdir, 'main.glade'))
        parser = SafeConfigParser()
        parser.read(path.join(self.appdir,'config.ini'))
        colwidths = parser.get('ui','colwidths').split(',')
        col = self.builder.get_object('treeviewcolumn1')
        col.set_fixed_width(int(colwidths[0]))
        col = self.builder.get_object('treeviewcolumn2')
        col.set_fixed_width(int(colwidths[1]))
        self.widgets = dict()
        self.widgets['window']      = self.builder.get_object('applicationwindow1')
        self.widgets['searchbox']   = self.builder.get_object('entry3')
        self.liststore              = self.builder.get_object('liststore1')
        self.widgets['tree']        = self.builder.get_object('treeview2')
        self.widgets['filechooser'] = self.builder.get_object('filechooserdialog1')
        self.widgets['filechooser'].set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        mnuquit = self.builder.get_object('mnuquit')
 
        self.modelfilter = self.liststore.filter_new()
        btnopen = self.builder.get_object('tbtnopen')        
        self.modelsort = Gtk.TreeModelSort(self.modelfilter)
        self.modelfilter.set_visible_func(self.filter_all)
        self.widgets['tree'].set_model(self.modelsort)
        
        #connect handlers
        btnopen.connect('clicked', self.showfilechooser)
        mnuquit.connect('activate', Gtk.main_quit)
        self.widgets['tree'].connect("row-activated", self.tree_dblclick)
        self.widgets['window'].connect('destroy', Gtk.main_quit)
        self.widgets['searchbox'].connect("changed", self.do_filter_all)
        self.widgets['searchbox'].connect("key-press-event", self.do_filter)
        self.widgets['searchbox'].connect("icon_press", self.do_clear)
        self.widgets['window'].show_all()

    def do_clear(self, entry, position, event):
        print position
        if position == position.SECONDARY:
            entry.set_text('')

    def filter_all(self, model, eter, data):
        collist = [(0,), (7,), (2,), (1,), (0,1,2,4,6,7)]
        row = model.get(eter, *collist[self.modstate])
        data = self.widgets['searchbox'].get_text().lower()
        for a in row:
            if data in a.lower():
                return True
        else:
            return False

    def do_filter(self, entry, key):
        val_names = key.get_state().value_names
        if key.get_keycode()[1] == 9:
            self.widgets['searchbox'].set_text('')
            pass
        if key.get_keycode()[1] == 36:
            if set(['GDK_SHIFT_MASK', 'GDK_CONTROL_MASK']).issubset(val_names):
                self.modstate = 3
            elif 'GDK_SHIFT_MASK' in val_names:
                self.modstate = 1
            elif 'GDK_CONTROL_MASK' in val_names:
                self.modstate = 2
            else:
                self.modstate = 0
        else:
            self.modstate = 4
        self.modelfilter.refilter()

    def do_filter_all(self, obj):
        self.modelfilter.refilter()

    def initDB(self):
        self.conn = lite.connect(path.join(self.appdir, 'biblioteca.db'))
        with self.conn:
            try:
                cur = self.conn.execute("""create table catalog (
                    title text,
                    filename text not null,
                    author text, pages int not null,
                    filepath text not null unique,
                    filesize text,
                    comments text,
                    keywords text,
                    favorite int(1),
                    sizeinbytes int
                )""")

            except lite.OperationalError, e:
                print e
                if e.message == 'table catalog already exists':
                    cur = self.conn.execute('select * from catalog')
                    self.data = cur.fetchall()
                    for i in self.data:
                        self.liststore.append(list(i))


    def showfilechooser(self, obj):
        response = self.widgets['filechooser'].run()
        self.widgets['filechooser'].hide()
        fpath = self.widgets['filechooser'].get_filename()
        pathlist = None
        if response == 1: 
            #self.findfiles(fpath)
            th = self.scanfiles(self, fpath)
            th.daemon = True
            th.start()

    def tree_dblclick(self, obj, treepath, second):
        #filename = self.liststore.get_value(self.liststore.get_iter(treepath), 4)
        (model, path) = self.widgets['tree'].get_selection().get_selected_rows()
        filename = model.get_value(model.get_iter(path), 4)
        call(['gnome-open', filename])

    def findfiles(self, fpath):
        #self.liststore.clear()
        self.path = fpath
        conn = lite.connect(path.join(self.appdir, 'biblioteca.db'))
        files = [f  for f in listdir(fpath) if f.endswith('.pdf') ]
        for f in files:
            print "opening " + f
            filepath = path.join(fpath, f)
            sizeinbytes = path.getsize(filepath)
            filesize = size(sizeinbytes)
            pdf = PyPDF2.PdfFileReader(open(filepath, 'rb'))
            templist = [pdf.documentInfo.title, f, pdf.documentInfo.author, pdf.numPages, filepath, filesize, None, None, 0, sizeinbytes]
            self.liststore.append(templist)
            cmd = unicode("insert into catalog values('{0}','{1}','{2}',{3},'{4}','{5}','{6}','{7}',{8}, {9})") .format(*tuple(i if i != None else '' for i in templist))
            try:
                cur = conn.execute(cmd)
            except lite.Error, e:
                print e.message
        conn.commit()


def main():
    app = LibraryApp()

if __name__ == '__main__':
    main()
