from database import *
import config as CONFIG
import IPython
import logging
import os
import validators
fuck = IPython.embed

from flask import Flask, render_template, request, url_for, redirect, session
import flask
from flask_login import LoginManager, login_user, logout_user, current_user, login_required, UserMixin
app = Flask(__name__)
app.secret_key = CONFIG.secret

logger=logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler('app.log')
logger.addHandler(handler)

@app.template_filter('title')
def pretty_print(s):
    ''' unescape then sanitize strings '''
    # there may be a better way
    import html
    import bleach
    return bleach.clean(html.unescape(s))

### login boilerplate
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

nathan = User('nathan')

@login_manager.user_loader
def load_user(userid):
    if userid == 'nathan':
        return nathan
    else:
        return None
### end of login boilerplate


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        passwd = request.form['password']
        if passwd != CONFIG.password:
            return flask.abort(400)
        else:
            login_user(nathan, remember=True)

        return flask.redirect(request.args.get("next") or url_for('admin'))
    return flask.render_template('login.html')

@app.route('/blogs')
def blogs(): 
    query = Session().query(Author)
    for author in CONFIG.do_not_list:
         query = query.filter(Author.name != author)
    objs = query.all()
    blogs = sorted([(b.link, b.name) for b in objs])
    return flask.render_template('blogs.html',blogs=sorted(blogs))

@app.route('/admin')
@login_required
def admin(): 
    return render_template('admin.html')
    
@app.route('/<int:index>')
def index_page(index): 
    index = int(index) if index >= 0 else 0 # shitty sql inj avoidance
    ppp = 100 # posts per page
    min = index*ppp
    session = Session()
    query = 'select *, author.link blogurl from author, post  where post.authorid = author.id order by post.date DESC;'
    results = session.execute(query).fetchall()
    results_for_page = results[min:min+ppp+1]
    posts = [make_post(p, session) for p in results_for_page] # could have been done using sql, don't care
    
    if len(posts)>ppp:
        next=True
    else:
        next=False
    if not posts and request.url not in request.url_root:
        return redirect(request.url_root)
    return render_template('index.html', posts=posts[:ppp], index=index, next=next)

@app.route('/')
def index():
    return index_page(0)
    
def is_valid_img(path):
    if path[-4:] != '.jpg' or path[-4:] !=  '.png':
        return False
    r = requests.head(path)
    return r.status_code == requests.codes.ok

def validate(form):
   error = ''
   if form['link'] == '' and len(form['link']) < 5 and not 'http' in form['link'][:4]:
       error = 'Insert a valid link for your post'
   if not validators.url(form['link']) or not validators.url(form['blogurl']) or not validators.url(form['thumb']):
       error = 'Please insert a valid link'
   if form['thumb'] == '' and len(form['thumb']) < 5 and not is_valid_img(form['thumb']):
      error = 'please insert a valid image for your blogpost'
   if form['title'] == '': 
      error = 'Please insert a valid title'
   if form['author'] == '': 
      error = 'Please insert a valid author name'
   if form['blogurl'] == '' and len(form['blogurl']) < 5 and not 'http' in form['blogurl'][:4]:
      error = 'Please insert a valid link for your blog'
   # very weak checks
   return error

def save_in_db(form):
    import datetime
    from scrape import add_to_db
    date = datetime.datetime.now()
    post = {}
    logger.info(str(form))
    post['author'] = form['author']
    #post['categories'] = form['categories'].split(',')
    post['categories']=[]
    post['tags'] = form['tags'].split(',')
    post['date'] = date
    post['title'] = form['title']
    post['link'] = form['link']
    post['blogurl'] = form['blogurl']
    post['jetpack_featured_media_url'] = form['thumb']
    add_to_db(post)

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    success = ''
    if request.method == 'GET':
        error = ''
    else:
        error =  validate(request.form)
        if error == '':
            save_in_db(request.form)
            success='Thank you for submitting your post.'
    return render_template('submit.html', error=error, success=success)

def make_post(post, session):
    '''
    Could have done a join,
    instead make other two queries to the db
    and build a dictionary that represents a post
    '''
    p = {}
    catq = 'select c.id cid, c.name cname, c.type type from  posthascategory pc, category c  where pc.cid = c.id and pc.pid = %s and pc.type = "Category";' %post.id  
    tagq= 'select c.id cid, c.name cname, c.type type from  posthascategory pc, category c  where pc.cid = c.id and pc.pid = %s and pc.type = "Tag";' %post.id 
    tags = session.execute(tagq).fetchall()
    categories = session.execute(catq).fetchall()
    p['thumb'] = post.thumb
    p['title'] = post.title
    p['link'] = post.link
    p['author'] = post.name
    p['blogurl'] = post.blogurl if 'http' == post.blogurl[:4] else 'http://' + post.blogurl
    p['tags'] = [(t.cid, t.cname) for t in tags]
    p['categories'] = [(t.cid, t.cname) for t in categories]
    p['date'] = post.date
    return p

def get_tag_cat(tagid, ttype):
    '''
    Commond code for getting posts tagged with tags or categories
    '''
    session = Session()
    tagq= 'select p.id, c.name cname, c.type type from  posthascategory pc, category c, post p where pc.cid = c.id and pc.pid = p.id and c.type = "%s" and c.id = %s order by p.date desc;' % (ttype, tagid)
    # here get only posts id.
    # then gather every info needed from multiple queries
    logger.error(tagq)
    posts = session.execute(tagq).fetchall()
    res = []
    for p in posts:
        query = 'select *, author.link blogurl from author, post  where post.authorid = author.id and post.id = %s;' % p.id
        pa = session.execute(query).first() # could have been done using sql, don't care
        res.append(make_post(pa, session))
    return res

def get_tag_name(tagid):
   '''
   Given a tagid, returns the name of the category/tag corresponding to this tagid
   '''
   session = Session()
   query = 'select c.name cname from category c where c.id = %s' % (tagid)
   tag_name = session.execute(query).fetchall()
   tag_name = tag_name[0][0]
   return tag_name

@app.route('/tag/<int:tagid>')
def get_tagged_posts(tagid):
    '''
    Given a tag id return all the posts that are tagged with that tag.
    '''
    tagid = 0 if tagid < 0 else int(tagid)
    return render_template('filtered_posts.html', posts=get_tag_cat(tagid, 'Tag'), tagid=get_tag_name(tagid))

@app.route('/categories/<int:tagid>')
def get_tagged_postsc(tagid):
    '''
    Given a tag id return all the posts that are tagged with that tag.
    '''
    tagid = 0 if tagid < 0 else int(tagid)
    return render_template('filtered_posts.html', posts=get_tag_cat(tagid, 'Categories'), tagid=get_tag_name(tagid))

@app.route('/category/<string:name>')
def filter_by_category_name(name):
    session = Session()
    name = name.replace('_', ' ')
    logger.error(name)
    logger.error(categorymap)

    if name in categorymap:
        name = categorymap[name]
    result = session.query(Category).filter(func.lower(Category.name)==func.lower(name)).filter(Category.type == 'Categories').first()
    if result:
        return redirect(request.url_root+'categories/'+str(result.id))
    return render_template('search.html', posts=[], error='No post belonging to the selected category.', show_search=True)


def search(queries, target=70):
    from sqlalchemy import func
    from fuzzywuzzy import fuzz
    posts = []
    track_posts = set()
    assert type(queries) is list # and comma divided
    session = Session()
    alltags = list(session.query(Category).all())
    tags = list() # the tags that match
    for q in queries:
        for s in alltags:
            ratio = fuzz.ratio(s.name.lower(), q.lower())
            if ratio > target:
                tags.append((s.id, s.type, s.name, ratio))
                #logger.error('Type: '+s.type)
                #logger.error(s.name+' - '+ str(q) + ': ' + str(ratio))
    for tag in sorted(tags, key=lambda t: t[-1], reverse=True):
        logger.error(tag)
        iid, ttype, name, ratio = tag
        new = get_tag_cat(iid, ttype)
        logger.error(str(new))
        for n in new:
            if n['title'] not in track_posts:
                track_posts.add(n['title'])
                posts.append(n)
    posts = sorted(posts, key=(lambda k:k['date']), reverse=True)
    return posts

def append_author(posts, session):
    matching=[]

    for post in posts:
        matching.append(session.query(Post.id,Post.thumb,Post.title,Post.link,Author.name,Author.link.label('blogurl')).filter(Post.authorid==Author.id).filter(Post.id==post.id).first())
    return matching

def search_category(query):

    session=Session()
    posts=[]

    cid=session.query(Category.id).filter(Category.name==query).first()
    if cid is None:
        return posts
    pid=session.query(PostHasCategory.pid).filter(PostHasCategory.cid==cid[0]).all()
    pid=[t[0] for t in pid]
    matching=session.query(Post).filter(Post.id.in_(pid)).all()
    matching=append_author(matching,session)

    for post in matching:
        posts.append(make_post(post,session))
    return posts

@app.route('/search', methods=['GET', 'POST'])
def searchroute():
    error = ''
    posts = []
    if request.method == 'POST':
       queries = request.form['search'].split(',')
       posts = search(queries)
       if len(posts) == 0:
               error = 'Nothing found. Try to refine your query.'
    return render_template('search.html', posts=posts, error=error, show_search=True)

@app.route('/course', methods=['GET'])
def course():
    ''' Display posts related to the course'''
    queries = ['activity', 'course', 'area']
    posts = search(queries, target=40)
    return render_template('search.html', posts=posts, error='', show_search=True)

@app.route('/area/<string:number>', methods=['GET'])
def area(number):
    ''' ditto '''
    #query = 'Area '+number
    #posts = search_category(query)
    error = ''
    posts = ''
    #if len(posts) == 0:
    #           error = 'Nothing found.'
    area = 'area-'+number+'.html'
    return render_template(area, posts=posts, error=error)

#@app.route('/activity/<string:number>', methods=['GET'])
#def activity(number):
#    ''' ditto '''
#    number=number.replace('-','.')
#    query = 'Activity '+number
#    posts = search_category(query)
#    error = ''
#    if len(posts) == 0:
#        error = 'Nothing found.'
#    return render_template('search.html', posts=posts, error=error)

@app.route('/remove_title', methods=['GET', 'POST'])
@login_required
def remove_title():
    success = ''
    error=''
    if request.method == 'GET':
        error = ''
    
    else:
        title = request.form['title'] 
        link = request.form['link']
        if link == '' and title == '':
            error = 'Insert a title or a link.'
        else:
            session = Session()
            post = None
            if link != '':
                post = session.query(Post).filter(Post.link == link).first()
            elif title != '':
                post = session.query(Post).filter(Post.title == title).first()
            if not post:
                error = 'Invalid title'
            else:
                posthascategory = session.query(PostHasCategory).filter(PostHasCategory.pid == post.id).delete()
                author = session.query(Author).filter(Author.id == post.authorid).delete()
                session.delete(post)
                session.commit()
                success = 'Post removed.'
                with open('urls_blacklist', 'a+') as f:
                    f.write("\n%s\n" %post.link)
    return render_template('remove_title.html', error=error, success=success)

@app.route('/filter', methods=['GET', 'POST'])
@login_required
# very bad naming
def filter_uurl():
    success = ''
    error = ''
   
    #Create blacklist files if they do not exist
    if not os.path.isfile('domains_blacklist'):
        open('domains_blacklist', 'a+').close()
    if not os.path.isfile('urls_blacklist'):
        open('urls_blacklist', 'a+').close()
   
    with open('domains_blacklist', 'r') as f:
         domains = set([l.strip() for l in f.readlines()])
    with open('urls_blacklist', 'r') as f:
         urls = set([l.strip() for l in f.readlines()])
    if '' in domains:
        domains.remove('')
    if '' in urls:
        urls.remove('')
    if request.method == 'GET':
        error = ''
    else:
       action = int(request.form['action'][0])
       entry = request.form['entry']
       if entry == '':
             error = 'Please insert a domain or a URL'
       elif action == 1: # blacklist domain
             with open('domains_blacklist', 'a+') as f:
                          f.write("\n%s\n" %entry)
       elif action == 2: # blacklist url
             with open('urls_blacklist', 'a+') as f:
                          f.write("\n%s\n" %entry)
       elif action == 3: # remove domain
             if entry not in domains:
                  error = 'You entered a domain that is not in the blacklist.'
             else:
                  domains.remove(entry)
                  with open('domains_blacklist', 'w+') as f:
                      for d in domains:
                          f.write("%s\n" %d)
       elif action == 4: # remove url
             if entry not in urls:
                  error = 'You entered a url that is not in the blacklist.'
             else:
                  urls.remove(entry)
                  with open('urls_blacklist', 'w+') as f:
                      for d in urls:
                          f.write("%s\n" %d)

       success = 'Action completed.'

    return render_template('filter_url.html', error=error, success=success, urls=enumerate(urls), domains=enumerate(domains))
    
@app.route('/lang/<string:lang>')
def change_lang(lang):
    if lang=='es' or lang=='it':
        session['lang'] = lang
    else:
        session['lang'] = 'en'
    return redirect(request.referrer)


if __name__ == '__main__':
    app.run()
