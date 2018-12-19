import requests
import json
from bs4 import BeautifulSoup
from jinja2 import BaseLoader, Template, Environment

import IPython
fuck = IPython.embed

def get_blog_list():
    s = requests.Session()
    sites = 'https://eduhack.eu/wp-admin/network/sites.php'
    login = 'https://eduhack.eu/wp-login.php'

    s.post(login, data={'log': 'me@francescomecca.eu', 'pwd':'provaprova2'})
    sitesHtml = s.get(sites).text

    b = BeautifulSoup(sitesHtml)

    tlist = b.find_all(id='the-list')[0] 
    children = list(tlist.children)
    blogs = set()
    toRemove = set(['eduhack.eu', 'eduhack.eu/wall'])
    for child in children:
        try:
            link = child.a.contents[0]
            blogs.add(link)
        except:
            pass
    blogs = blogs - toRemove

    print(blogs)
    return blogs

def get_username(url):
    endpoint = '/wp-json/wp/v2/users'
    jposts = requests.get(url+endpoint).text
    d = json.loads(jposts)
    return d[0]['name']
    

def get_posts(url):
    if 'http' != url[:4]:
        url = 'https://' + url
    api = '/wp-json/wp/v2/posts'
    author = get_username(url)
    jposts = requests.get(url+api).text
    restPosts = json.loads(jposts)
    schema = ['link', 'date', 'title', 'jetpack_featured_media_url']
    posts = list()
    for p in restPosts:
       res = {}
       for key in schema:
           res[key] = p[key]
       res['title'] = res['title']['rendered']
       res['author'] = author
       posts.append(res)
    return posts
            
def render_template(lst):
    with open('template.html', 'r') as fp: 
        st = fp.read() 
    template = Environment(loader=BaseLoader).from_string(st) 
    result = template.render({'posts': lst})
    with open("index.html", "w") as fp:
        fp.write(result)



all = list()
for b in get_blog_list():
    all.extend(get_posts(b))
render_template(all)
     
