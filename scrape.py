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

#logger=logging.getLogger(__name__)
#logger.setLevel(logging.INFO)

#handler = logging.FileHandler('scrapedebug.log')
#logger.addHandler(handler)

categorymap = {
    "Activity 1.1":"Activity 1.1 - Search for Open Educational Resources (OER)",
    "Activity 1.2":"Activity 1.2 - Modify existing digital content by using Wikis",
    "Activity 1.3":"Activity 1.3 - Create digital educational resources",
    "Activity 1.4":"Activity 1.4 - Curate and organise digital resources",
    "Activity 1.5":"Activity 1.5 - Apply open licenses to your resources",
    "Activity 2.1":"Activity 2.1 - Design your own eLearning intervention",
    "Activity 2.2":"Activity 2.2 - Implement ICT-supported collaborative learning",
    "Activity 2.3":"Activity 2.3 - Guide and support students through e-moderation",
    "Activity 2.4":"Activity 2.4 - Foster knowledge co-creation among students",
    "Activity 2.5":"Activity 2.5 - Create and select video resources for your teaching",
    "Activity 2.6":"Activity 2.6 - Use games to improve learners engagement",
    "Activity 3.1":"Activity 3.1 - Explore digitally supported assessment strategies",
    "Activity 3.2":"Activity 3.2 - Experiment with different technologies for formative assessment",
    "Activity 3.3":"Activity 3.3 - Analyse evidence on learning activity, performance and progress",
    "Activity 3.4":"Activity 3.4 - Use digital technologies to provide targeted feedback to learners",
    "Activity 4.1":"Activity 4.1 - Critically evaluate online tools",
    "Activity 4.2":'Activity 4.2 - Discover the cost of "free" commercial social media platforms',
    "Activity 4.3":"Activity 4.3 - Appreciate opportunities and risks of personalization in learning",
    "Activity 4.4":"Activity 4.4 - Check technical accessibility of platforms and resources",
    "A1.1 Search for Open Educational Resources (OER)":"Activity 1.1 - Search for Open Educational Resources (OER)",
    "A1.2 Modify existing digital content by using Wikis":"Activity 1.2 - Modify existing digital content by using Wikis",
    "A1.3 Create digital educational resources":"Activity 1.3 - Create digital educational resources",
    "A1.4 Curate and organise digital resources":"Activity 1.4 - Curate and organise digital resources",
    "A1.5 Apply open licenses to your resources":"Activity 1.5 - Apply open licenses to your resources",
    "A2.1 Design your own eLearning intervention":"Activity 2.1 - Design your own eLearning intervention",
    "A2.2 Implement ICT-supported collaborative learning":"Activity 2.2 - Implement ICT-supported collaborative learning",
    "A2.3 Guide and support students through e-moderation":"Activity 2.3 - Guide and support students through e-moderation",
    "A2.4 Foster knowledge co-creation among students":"Activity 2.4 - Foster knowledge co-creation among students",
    "A2.5 Create and select video resources for your teaching":"Activity 2.5 - Create and select video resources for your teaching",
    "A2.6 Use games to improve learners engagement":"Activity 2.6 - Use games to improve learners engagement",
    "A3.1 Explore digitally supported assessment strategies":"Activity 3.1 - Explore digitally supported assessment strategies",
    "A3.2 Experiment with different technologies for formative assessment":"Activity 3.2 - Experiment with different technologies for formative assessment",
    "A3.3 Analyse evidence on learning activity, performance and progress":"Activity 3.3 - Analyse evidence on learning activity, performance and progress",
    "A3.4 Use digital technologies to provide targeted feedback to learners":"Activity 3.4 - Use digital technologies to provide targeted feedback to learners",
    "A4.1 Critically evaluate online tools":"Activity 4.1 - Critically evaluate online tools",
    "A4.2 Discover the cost of \"free\" commercial social media platforms":'Activity 4.2 - Discover the cost of "free" commercial social media platforms',
    "A4.3 Appreciate opportunities and risks of personalization in learning":"Activity 4.3 - Appreciate opportunities and risks of personalization in learning",
    "A4.4 Check technical accessibility of platforms and resources":"Activity 4.4 - Check technical accessibility of platforms and resources",
    "Area 1":"Area 1 - Digital Resources",
    "Area 2":"Area 2 - Teaching",
    "Area 3":"Area 3: Assessment",
    "Area 4":"Area 4: Empowering students",
    "Digital Resources":"",
    "Teaching":"",
    "Assessment":"",
    "Empowering students":""
}

def get_blog_list():
    logging.info('getting sites list with auth')
    s = requests.Session()
    page_num = 1
    blogs = set()
    sites = 'https://eduhack.eu/wp-admin/network/sites.php?paged='
    login = 'https://eduhack.eu/wp-login.php'
    toRemove = set(['eduhack.eu'])

    s.post(login, data={'log': CONFIG.email, 'pwd':CONFIG.wp_pwd})
    sitesHtml = s.get(sites+str(page_num)).text

    b = BeautifulSoup(sitesHtml, features='lxml')
    max_pages = int(b.find_all(class_='displaying-num')[0].contents[0].split(' ')[0])//20+1 # Gets the number of websites in the multisite and computes the number of pages to scrape
    logging.info(str(max_pages))
    while True:
        tlist = b.find_all(id='the-list')[0] 
        children = list(tlist.children)
        for child in children:
            try:
                link = child.a.contents[0]
                    # yield link # can't yield because of session duration
                blogs.add(link)
            except:
                pass

        page_num = page_num+1
        if page_num > max_pages:
            break
        sitesHtml = s.get(sites+str(page_num)).text
        b = BeautifulSoup(sitesHtml, features='lxml')

    blogs = blogs - toRemove
    logging.error(str(blogs))
    return blogs

def get_username(url):
    endpoint = '/wp-json/wp/v2/users?per_page=100'
    jposts = requests.get(url+endpoint).text
    d = json.loads(jposts)
    if not d:
        logging.error(url + ' has no posts')
        return None

    if '/wall.' in d[0]['link']:
        name = 'EduHack Wall'
    elif '/polito.' in d[0]['link']:
        name = 'PoliTo EduHackathon'
    elif '/coventry.' in d[0]['link']:
        name = 'Coventry EduHackathon'
    elif '/unir.' in d[0]['link']:
        name = 'UNIR EduHackathon'
    else:
        name = d[0]['name']
    # del d[0] # when taking the user from the wall remove the first one (admin) and return the second

    return name
    
def get_tags(url):
    i=1
    endpoint = '/wp-json/wp/v2/tags?per_page=100&page='
    jposts = requests.get(url+endpoint+str(i)).text
    d = json.loads(jposts)
    res = {}
    while d:
        for tag in d:
           res[tag['id']] = tag['name']
        i=i+1
        jposts=requests.get(url+endpoint+str(i)).text
        d=json.loads(jposts)
    return res

def get_cat(url):
    endpoint = '/wp-json/wp/v2/categories?per_page=100'
    jposts = requests.get(url+endpoint).text
    d = json.loads(jposts)
    res = {}
    for cat in d:
       if cat['name'] in categorymap:
           res[cat['id']] = categorymap[cat['name']]
       else:
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
            #logger.info('Cat: '+tags[tid]+'\n')
            tagnames.append(tags[tid]) # fill with tag names
        else:
            logging.error(' '.join(['no', str(tid), 'for', post['link']]))
    if '/polito.' in post['link']:
        tagnames.append('PoliTo EduHackathon')
    elif '/coventry.' in post['link']:
        tagnames.append('Coventry EduHackathon')
    elif '/unir.' in post['link']:
        tagnames.append('UNIR EduHackathon')
    
    return sorted(tagnames)

def get_posts(url):
    logging.info('getting posts for: ' +url)
    if 'http' != url[:4]:
        url = 'https://' + url

    api = '/wp-json/wp/v2/posts?per_page=100'

    try:
        tags = get_tags(url)
        categories = get_cat(url)
        author = get_username(url)
    except:
        tags=[]
        categories=[]
        author=None

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
    import time
    start_time=time.time()
    logging.basicConfig(level=logging.ERROR)
    count=1
    all = list()
    for b in get_blog_list():
        for post in get_posts(b):
            add_to_db(post)
        logging.error('Completed '+str(count))
        count=count+1
    logging.error('--- %s seconds ---' % (time.time()-start_time))
