import lucene, jieba, os, sys
sys.path.append('..')
from settings import *
from java.io import File
from org.apache.lucene.analysis.core import WhitespaceAnalyzer
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.search import IndexSearcher, BooleanQuery, BooleanClause

if __name__ != '__main__':
	_vm = lucene.initVM(vmargs = ['-Djava.awt.headless=true'])
	jieba.initialize()

def get_content(file):
	with open(os.path.join(FOLDER_RAWCONTENTS, file), 'r') as fin:
		return fin.read().decode('utf8')

def get_summary(doc, cut_search, window = 100):
	content = get_content(doc.get('path'))
	tokres = jieba.tokenize(content, mode='search')
	search_words = {}
	for i in range(len(cut_search)):
		search_words[cut_search[i]] = i
	kaps = []
	for x in tokres:
		if x[0] in search_words.keys():
			kaps.append((x[1], x[2], search_words[x[0]]))
	kaps.sort(key = (lambda x: x[0]))
	nextitem = 0
	maxv, s, e = 0, 0, 0
	for i in range(len(kaps)):
		end = kaps[i][0] + window
		while nextitem < len(kaps) and kaps[nextitem][1] <= end:
			nextitem += 1
		exc, rni = nextitem - i, nextitem
		while rni < len(kaps) and kaps[rni][0] < end:
			if kaps[rni][1] <= end:
				exc += 1
			rni += 1
		if exc > maxv:
			maxv, s, e = exc, i, rni
	lens = kaps[s][0]
	kaps = kaps[s:e]
	maxk = max((x[1] for x in kaps if x[1] <= lens + window))
	lens -= (lens + window - maxk) / 2
	if lens + window > len(content):
		lens = len(content) - window
	if lens < 0:
		lens = 0
	return maxv, lens, len(content), content[lens:lens + window], kaps

MAX_PAGE_NAV = 10

# TODO not implemented
# class result_cache:
# 	def __init__(query_words):
# 		self.query = query_words
# 		self.page_start = 1
# 		self.cached_docs = []

# 	def query(page, query, searcher):
# 		if page >= self.page_start and page <

def query_page(page, query, searcher, pagesize):
	if page == 0:
		sres = searcher.search(query, pagesize)
		return (sres.scoreDocs, sres.totalHits)
	spn = min(page, MAX_PAGE_NAV)
	cres = searcher.search(query, spn * pagesize)
	if cres.totalHits <= page * pagesize:
		return ([], cres.totalHits)
	page -= spn
	while page > 0:
		spn = min(page, MAX_PAGE_NAV)
		cres = searcher.searchAfter(cres.scoreDocs[-1], query, spn * pagesize)
		page -= spn
	res = searcher.searchAfter(cres.scoreDocs[-1], query, pagesize)
	return (res.scoreDocs, res.totalHits)

def search_newthread(command, params, contentstr, folder, page, pagesize):
	def split_parameters(userinput):
		res = []
		dic = {}
		for x in userinput.split():
			sd = x.split(':')
			sd[0] = sd[0].lower()
			if len(sd) > 1 and sd[0] in params.keys():
				dic[sd[0]] = ':'.join(sd[1:])
			else:
				res.append(x)
		return ' '.join(res), dic

	global _vm

	_vm.attachCurrentThread()
	searcher = IndexSearcher(DirectoryReader.open(SimpleFSDirectory(File(folder))))
	analyzer = WhitespaceAnalyzer()

	command, paramdic = split_parameters(command.lower())
	cutwords = []
	for x in command.split():
		cutwords += jieba.lcut(x)
	command = ' '.join(cutwords)
	querys = BooleanQuery()
	querys.add(QueryParser(contentstr, analyzer).parse(command), BooleanClause.Occur.MUST)
	for k, v in paramdic.items():
		querys.add(QueryParser(params[k], analyzer).parse(v), BooleanClause.Occur.MUST)
	docs, hits = query_page(page, querys, searcher, pagesize)
	return cutwords, hits, (searcher.doc(x.doc) for x in docs)
