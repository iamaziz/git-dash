"""
    Generate Dash docset for Git
    http://git-scm.com/docs
"""
import sqlite3
import os
import urllib
from bs4 import BeautifulSoup as bs
import requests


# CONFIGURATION
docset_name = 'Git.docset'
output = docset_name + '/Contents/Resources/Documents'
root_url = 'http://git-scm.com/docs'

# create directory
docpath = output + '/'
if not os.path.exists(docpath): os.makedirs(docpath)
icon = 'http://blog.novatec-gmbh.de/wp-content/uploads/2013/07/logo-git.png'

# soup
data = requests.get(root_url).text    # for online page
soup = bs(data)
index = str(soup.find(id='main'))
open(os.path.join(output, 'index.html'), 'wb').write(index)
# add icon
urllib.urlretrieve(icon, docset_name + "/icon.png")


def update_db(name, path):
    typ = 'func'
    cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?,?,?)', (name, typ, path))
    print 'DB add >> name: %s, path: %s' % (name, path)


def add_docs():
    sections = []
    titles = []
    for i, link in enumerate(soup.findAll('a')):
        name = link.text.strip()
        path = link.get('href')

        if path.startswith('/docs/'):
            sections.append(path)
            titles.append(name)

    # download and update db
    for path, name in zip(sections, titles):
        # create subdir
        folder = os.path.join(output)
        for i in range(len(path.split("/")) - 1):
            folder += path.split("/")[i] + "/"
        if not os.path.exists(folder): os.makedirs(folder)

        print name, path
        try:
            # download docs
            page = path.split('/')[-1]
            url = root_url + '/' + page

            data1 = requests.get(url).text
            soup1 = bs(data1)
            div = str(soup1.find(id='main'))
            open(os.path.join(folder, page + '.html'), 'wb').write(div)
            print "downloaded doc: ", path
            print " V"

            # update db
            path += '.html'
            update_db(name, path)
            #y += 1
        except:
            print " X"
            pass


def add_infoplist():
    name = docset_name.split('.')[0]
    info = " <?xml version=\"1.0\" encoding=\"UTF-8\"?>" \
           "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> " \
           "<plist version=\"1.0\"> " \
           "<dict> " \
           "    <key>CFBundleIdentifier</key> " \
           "    <string>{0}</string> " \
           "    <key>CFBundleName</key> " \
           "    <string>{1}</string>" \
           "    <key>DocSetPlatformFamily</key>" \
           "    <string>{2}</string>" \
           "    <key>isDashDocset</key>" \
           "    <true/>" \
           "    <key>dashIndexFilePath</key>" \
           "    <string>index.html</string>" \
           "</dict>" \
           "</plist>".format(name, name, name)
    open(docset_name + '/Contents/info.plist', 'wb').write(info)


if __name__ == '__main__':

    db = sqlite3.connect(docset_name + '/Contents/Resources/docSet.dsidx')
    cur = db.cursor()
    try:
        cur.execute('DROP TABLE searchIndex;')
    except:
        pass
    cur.execute('CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);')
    cur.execute('CREATE UNIQUE INDEX anchor ON searchIndex (name, type, path);')

    # start
    add_docs()
    add_infoplist()

    # commit and close db
    db.commit()
    db.close()