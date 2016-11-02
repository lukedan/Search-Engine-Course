import web, search, os, json
from index_settings import *

_SERVER_PREFIX = 'SS'
_SERVER_ANY_PREFIX = 'SA'
_SEARCH_PARAMS = {
	'site': 'domain'
}
_USE_FILESYSTEM_MAPPING = True
_FSMAP_URL = '/files/'
_FSMAP_DIRECTORY = './mapping/'

_USE_CLIENTSIDE_FX = False
_USE_SHADOWS = False
_LEFT_MARGIN = '50px'
_BOTTOM_PAGEMARKER_WIDTH = '40px'
_REGION_WIDTH = '45%'

renderer = web.template.render('./templates/')

def to_json(resultset, page, window = 100):
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

class SS_:
	def GET(self):
		return renderer.mainpage({
			'no_prebaked_fx': _USE_CLIENTSIDE_FX,
			'use_shadow': _USE_SHADOWS,
			'left_margin': _LEFT_MARGIN,
			'bottom_pagemarker_width': _BOTTOM_PAGEMARKER_WIDTH,
			'region_width': _REGION_WIDTH
		})

class SS_search:
	def GET(self):
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
				tsr = search.search_newthread(searchstr, FOLDER_INDEXED, _SEARCH_PARAMS, 'contents', page)
		return to_json(tsr, page)


if _USE_FILESYSTEM_MAPPING:
	class SA_files:
		def GET(self, name):
			if name[0] == '/':
				name = name[1:]
			with open(os.path.join(_FSMAP_DIRECTORY, name), 'r') as fin: # no checkings! attack all you want
				return fin.read()

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
