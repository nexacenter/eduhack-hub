import requests
from bs4 import BeautifulSoup
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
		# shitty code
		link = child.a.contents[0]
		blogs.add(link)
	    except:
		pass
	blogs = blogs - toRemove

	print(blogs)
        return blogs

