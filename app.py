from database import *
import config as CONFIG


from flask import Flask, render_template, request, url_for
import flask
from flask_login import LoginManager, login_user, logout_user, current_user, login_required, UserMixin
app = Flask(__name__)
app.secret_key = CONFIG.secret

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

@app.route('/admin')
def admin(): 
    return render_template('admin.html')
    
@app.route('/<int:index>')
def index_page(index): 
    index = index if index >= 0 else 0
    session = Session()
    query = 'select * from author, post  where post.authorid = author.id and post.id > %s order by post.id DESC limit 10;' % index
    posts = [make_post(p, session) for p in session.execute(query).fetchall()] # could have been done using sql, don't care
    return render_template('template.html', posts= posts, index=index)

@app.route('/')
def index():
    return index_page(0)
    
def is_valid_img(path):
    if path[-4:] != '.jpg' or path[-4:] !=  '.png':
        return False
    r = requests.head(path)
    return r.status_code == requests.codes.ok

def validate(form):
   print(form)
   error = ''
   if form['link'] == '' and len(form['link']) < 5 and not 'http' in form['link'][:4]:
       error = 'Insert a valid link for your post'
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
    date = datetime.datetime.now().strftime("%b %d %Y %H:%M:%S")
    post = {}
    post['author'] = form['author']
    post['categories'] = form['categories'].split(',')
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
    p = {}
    catq = 'select c.name cname, c.type type from  posthascategory pc, category c  where pc.cid = c.id and pc.pid = %s and pc.type = "Category";' %post.id  
    tagq= 'select c.name cname, c.type type from  posthascategory pc, category c  where pc.cid = c.id and pc.pid = %s and pc.type = "Tag";' %post.id 
    tags = session.execute(tagq).fetchall()
    categories = session.execute(catq).fetchall()
    p['thumb'] = post.thumb
    p['title'] = post.title
    p['link'] = post.link
    p['author'] = post.name
    p['tags'] = [t.cname for t in tags]
    p['categories'] = [t.cname for t in categories]
    return p

@app.route('/remove_title', methods=['GET', 'POST'])
@login_required
def remove_title():
    success = ''
    if request.method == 'GET':
        error = ''
    else:
        title = form['title'] 
        link = form['link'] 
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
                 session.delete(post)
                 session.commit()
                 success = 'Title removed.'
    return render_template('remove_title.html', error=error, success=success)

@app.route('/filter', methods=['GET', 'POST'])
def filter_uurl():
    success = ''
    error = ''
    print(request.form)
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
             with open('domains_blacklist', 'a') as f:
                          f.write("\n%s\n" %entry)
       elif action == 2: # blacklist url
             with open('urls_blacklist', 'a') as f:
                          f.write("\n%s\n" %entry)
       elif action == 3: # remove domain
             if entry not in domains:
                  error = 'You entered a domain that is not in the blacklist.'
             else:
                  domains.remove(entry)
                  with open('domains_blacklist', 'w') as f:
                      for d in domains:
                          f.write("%s\n" %d)
       elif action == 4: # remove url
             if entry not in urls:
                  error = 'You entered a url that is not in the blacklist.'
             else:
                  urls.remove(entry)
                  with open('urls_blacklist', 'w') as f:
                      for d in urls:
                          f.write("%s\n" %d)
                  

       success = 'Action completed.'
    print(urls, domains, success)
    return render_template('filter_url.html', error=error, success=success, urls=enumerate(urls), domains=enumerate(domains))
    


if __name__ == '__main__':
    app.run()
