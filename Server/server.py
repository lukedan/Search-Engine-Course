import web, search, os, json, sys, urlparse, urllib2
sys.path.append('..')
from settings import *
from common import *

_SERVER_PREFIX = 'SS'
_SERVER_ANY_PREFIX = 'SA'
_SEARCH_PARAMS = {
	'site': 'domain'
}
_FSMAP_URL = '/files/'
_FSMAP_DIRECTORY = './mapping/'
_DOCS_PER_PAGE = 20
_IMGS_PER_PAGE = 10

renderer = web.template.render('./templates/')

def pack_json_text(resultset, page, window = 100):
	result = {'hits': resultset[1], 'page': page}
	reslst = []
	for x in resultset[2]:
		brief = search.get_summary(x, resultset[0], window)
		startpos = brief[1]
		curitm = {
			'ellbef': startpos > 0,
			'ellaft': brief[1] + len(brief[3]) < brief[2],
			'titletext': web.net.websafe(x.get('title')),
			'url': x.get('url'),
			'urltext': web.net.websafe(x.get('url'))
		}
		curlst = []
		cpos = 0
		i = 0
		while i < len(brief[4]):
			cs, ce = brief[4][i][0] - startpos, brief[4][i][1] - startpos
			if cs < cpos or ce > len(brief[3]):
				i += 1
			else:
				curlst.append(web.net.websafe(brief[3][cpos:cs]))
				curlst.append(web.net.websafe(brief[3][cs:ce]))
				i += 1
				cpos = ce
		curlst.append(web.net.websafe(brief[3][cpos:len(brief[3])]))
		curitm['lst'] = curlst
		reslst.append(curitm)
	result['lst'] = reslst
	return json.dumps(result)

def pack_json_img(resultset, page):
	result = {'hits': resultset[1], 'page': page}
	reslst = []
	for x in resultset[2]:
		reslst.append({
			'url': x.get('url'),
			'pageurl': x.get('page'),
			'title': x.get('title'),
			'pagetitle': x.get('pagetitle')
		})
	result['lst'] = reslst
	return json.dumps(result)

class SS_:
	def GET(self):
		with open('page_config.json', 'r') as fin:
			settings = json.loads(fin.read())
		return renderer.mainpage(settings)

def _do_search(gettsr, getret):
	user_data = web.input()
	tsr = ((), 0, ())
	page = 0
	if 'page' in user_data.keys():
		try:
			page = int(user_data.page)
		except:
			page = 0
	if 'target' in user_data.keys():
		searchstr = user_data.target
		if len(searchstr) > 0:
			tsr = gettsr(searchstr, page)
	return getret(tsr, searchstr, page)

class SS_search:
	def GET(self):
		return _do_search(
			(lambda ss, pg: search.search_newthread(ss, _SEARCH_PARAMS, 'contents', FOLDER_INDEXED, pg, _DOCS_PER_PAGE)),
			(lambda tsr, ss, pg: pack_json_text(tsr, pg))
		)

class SS_searchimg:
	def GET(self):
		return _do_search(
			(lambda ss, pg: search.search_newthread(ss, _SEARCH_PARAMS, 'info', FOLDER_INDEXED_IMAGES, pg, _IMGS_PER_PAGE)),
			(lambda tsr, ss, pg: pack_json_img(tsr, pg))
		)

class SS_getimg:
	def GET(self):
		user_data = web.input()
		if 'url' in user_data.keys() and 'ref' in user_data.keys():
			return urllib2.urlopen(urllib2.Request(url = normalize_url(user_data.url), headers = {
				'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6',
				'Referer': normalize_url(user_data.ref)
			})).read()

def generate_url_list():
	res = []
	for k in globals().keys():
		if k.startswith(_SERVER_PREFIX):
			res.append(k[len(_SERVER_PREFIX):].replace('_', '/').lower())
			res.append(k)
		elif k.startswith(_SERVER_ANY_PREFIX):
			res.append(k[len(_SERVER_ANY_PREFIX):].replace('_', '/').lower() + '(.*)')
			res.append(k)
	return res

def main():
	web.application(generate_url_list(), globals()).run()

if __name__ == '__main__':
	main()
