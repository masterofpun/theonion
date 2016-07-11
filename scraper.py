import time, requests, random, dateutil.parser
from random import shuffle
##from bs4 import BeautifulSoup as Soup, SoupStrainer
##from fuzzywuzzy import fuzz

import sqlite3
DB_FILE = 'data.sqlite'

##rex = re.compile(r'\s+')
##numb = re.compile(r'[^0-9]')
##rdate = re.compile(r'[^a-z0-9]')
##const = re.compile(r'[^a-z0-9\-]')

headers = {'User-Agent':'Gathering metadata for all Onion articles using morph.io, contact at: reddit.com/u/hypd09', 'Accept-Encoding': 'gzip'}

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute('drop table IF EXISTS data') ###debug
c.execute('create table data (title,section,date,issue,tags,description,image_url,article_url)')

def num(s):
    s = numb.sub(' ',s)
    s = clean(s)
    if s is None:
        return 0
    return int(s)

def clean(s):
    return rex.sub(' ',s).strip()

def getTags(aId, article):
    tags = []
    tags_ = article.split('tag/')
    if len(tags_)<3:
        return tags
    tags_ = tags_[1:-1]
    for i in range(0,len(tags_),2):
        tags.append(tags_[i].split('"')[0].strip())

    return tags        
            

session = requests.Session()
##strainer = SoupStrainer([('div',class_='share-tools share-widget'),])

lastId = 53187

baseUrl = 'http://www.theonion.com/r/'
ids = [x for x in range(1,lastId+1)]

print(len(ids))

shuffle(ids)

size = len(ids)
for i in range(size+1):
    
    aId = ids[i]
    print(aId,i,'of',size)
    fullUrl = None
    req = session.head(baseUrl+str(aId),headers=headers)
    try:
        if req.status_code == 301 or req.status_code == 302:
            fullUrl = req.headers['Location']
        elif req.status_code==404:
            continue
        else:
            print(aId, req.status_code)
    except KeyError:
        print(aId,req.headers)

    if fullUrl is None:
        print('failed',aId)
        continue
    
    if 'theonion.com/article/' not in fullUrl:
        continue
    
    fullResp = session.get(fullUrl+'?partial=true')
    
    article = None
    if fullResp.status_code == 200:
        article = fullResp.text
    else:
        print('failed',aId,fullResp.status_code)
        continue
    
    a_title = None
    if '<h1>' in article:
        a_title = article.split('<h1>')[1].split('<')[0].strip()
        
    a_section = None
    if 'search?tags=">' in article:
        a_section = article.split('search?tags=">')[1].split('<')[0].strip()

    a_date = None
    if 'content-published">' in article:
        a_date = dateutil.parser.parse(article.split('content-published">')[1].split('<')[0].strip())
        
    a_issue = None
    if 'issue/' in article:
        a_issue = int(article.split('issue/')[1].split('/')[0].strip())

    a_tags = ','.join(getTags(aId, article))

    a_desc = None
    if 'data-share-description="' in article:
        a_desc = article.split('data-share-description="')[1].split('"')[0].strip().encode('utf-8')
        
    a_image = None
    if 'data-share-image="' in article:
        a_image = article.split('data-share-image="')[1].split('"')[0].strip()
        
    a_url = fullUrl
    
    data = [a_title,a_section,a_date,a_issue,a_tags,a_desc,a_image,a_url]
    
    # title,section,date,issue,tags,description,image_url,article_url
    c.execute('insert into data values (?,?,?,?,?,?,?,?)',data)
    time.sleep(0.150)
    conn.commit()
c.close()
