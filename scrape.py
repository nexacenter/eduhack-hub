import requests
import json
from bs4 import BeautifulSoup
from jinja2 import BaseLoader, Template, Environment
import logging
from database import *
import config as CONFIG
from dateutil import parser as dateparser
import datetime

import IPython
fuck = IPython.embed

def get_blog_list():
    logging.info('getting sites list with auth')
    s = requests.Session()
    sites = 'https://eduhack.eu/wp-admin/network/sites.php'
    login = 'https://eduhack.eu/wp-login.php'

    s.post(login, data={'log': CONFIG.email, 'pwd':CONFIG.wp_pwd})
    sitesHtml = s.get(sites).text

    b = BeautifulSoup(sitesHtml, features='lxml')

    tlist = b.find_all(id='the-list')[0] 
    children = list(tlist.children)
    blogs = set()
    toRemove = set(['eduhack.eu'])
    for child in children:
        try:
            link = child.a.contents[0]
                # yield link # can't yield because of session duration
            blogs.add(link)
        except:
            pass
    blogs = blogs - toRemove
    return blogs

def get_username(url):
    endpoint = '/wp-json/wp/v2/users?per_page=100'
    jposts = requests.get(url+endpoint).text
    d = json.loads(jposts)
    if not d:
        logging.error(url + ' has no posts')
        return None
    if d[0]['name'] == 'admin':
        return 'Anonymous' # wall writer
    return d[0]['name']
    
def get_tags(url):
    endpoint = '/wp-json/wp/v2/tags?per_page=100'
    jposts = requests.get(url+endpoint).text
    d = json.loads(jposts)
    res = {}
    for tag in d:
       res[tag['id']] = tag['name']
    return res

def get_cat(url):
    endpoint = '/wp-json/wp/v2/categories?per_page=100'
    jposts = requests.get(url+endpoint).text
    d = json.loads(jposts)
    res = {}
    for cat in d:
       res[cat['id']] = cat['name']
    if 'Uncategorized' in res:
        res.remove('Uncategorized')
    return res

def fill_tags(post, tags, key='tags'):
    logging.debug(tags)
    assert type(tags) is dict
    assert type(post) is dict
    assert type(key) is str
    tagnames = list()
    for tid in post[key]:
        if tid in tags:
            tagnames.append(tags[tid]) # fill with tag names
        else:
            logging.error(' '.join(['no', str(tid), 'for', post['link']]))
    return sorted(tagnames)

def get_posts(url):
    logging.info('getting posts for: ' +url)
    if 'http' != url[:4]:
        url = 'https://' + url
    tags = get_tags(url)
    categories = get_cat(url)
    api = '/wp-json/wp/v2/posts'
    author = get_username(url)
    if author is None:
        raise StopIteration
    jposts = requests.get(url+api).text
    restPosts = json.loads(jposts)
    schema = ['link', 'title', 'jetpack_featured_media_url']
    posts = list()
    for p in restPosts:
       res = {}
       for key in schema:
           res[key] = p[key]
       res['title'] = res['title']['rendered']
       res['author'] = author
       res['blogurl'] = url
       res['tags'] = fill_tags(p, tags)
       res['categories'] = fill_tags(p, categories, 'categories')
       res['date'] = dateparser.parse(p['date'])
       yield(res)
       #posts.append(res)
    #return posts
            
def add_author_todb(name, link, session=None):
    author = session.query(Author).filter(Author.name == name).first()
    if author:
       return author
    author = Author(name = name, link=link)
    session.add(author)
    logging.debug(author)
    return author

def already_in_db(p, session=None):
    return session.query(Post).filter(Post.link == p['link']).first()

def add_post_todb(p, author, session=None):
    assert type(p['date']) is datetime.datetime, type(p['date'])
    post = Post(title = p['title'], link=p['link'],
                        date=p['date'], thumb=p['jetpack_featured_media_url'], author=author)
    session.add(post)
    return post

def add_category_todb(cat, session=None, type=None):
    assert type is not None
    category = session.query(Category).filter(Category.name == cat).first()
    if category:
       return category
    c = Category(name=cat, type=type)
    session.add(c)
    return c

def add_cat_post_rel_todb(c=None, p=None, type=None, session=None):
    rel = PostHasCategory(post=p, category=c, type=type) 
    session.add(rel)
    return rel

def should_ignore(domain=None, url=None):
    assert domain is not None and url is not None
    domains = set()
    urls = set()
    with open('domains_blacklist', 'r') as f:
        domains = set([l.strip() for l in f.readlines()]) 
    with open('urls_blacklist', 'r') as f:
        urls = set([l.strip() for l in f.readlines()]) 
    for var in ['', 'http://', 'https://']:
        # check multiple combinations
        if var + url in urls:
             return True
        if var + domain in domains:
             return True
    return False

def add_to_db(post):
    '''
    Generate different database objects from a dictionary
    and populate the DB
    If already in db, return
    '''
    link = post['link'] 
    domain = post['blogurl']
    if should_ignore(domain=domain, url=link):
        return
    session = Session()
    if already_in_db(post, session=session):
        return
    author = post['author']
    authorTable = add_author_todb(author, post['blogurl'], session=session) # table is wrong naming
    postTable = add_post_todb(post, authorTable, session=session)
    for cat in post['categories']:
        c = add_category_todb(cat, type='Categories', session=session)
        add_cat_post_rel_todb(c=c, p=postTable, type='Category', session=session)
    for tag in post['tags']: # horrible
        c = add_category_todb(tag, type='Tag', session=session)
        add_cat_post_rel_todb(c=c, p=postTable, type='Tag', session=session)
    logging.info('Added to db: ' + post['title'])
    session.commit()

if __name__ == '__main__':
    all = list()
    for b in get_blog_list():
        for post in get_posts(b):
            add_to_db(post)
