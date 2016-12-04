import os, sys, re, threading, time, urlparse, collections
sys.path.append('..')
from settings import *
from common import *
from bs4 import BeautifulSoup
import jieba, lucene
from java.io import File
from org.apache.lucene.analysis.core import WhitespaceAnalyzer
from org.apache.lucene.document import Document, Field, FieldType, StringField, TextField
from org.apache.lucene.index import FieldInfo, IndexWriter, IndexWriterConfig
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.util import Version

def join_strings(lst, spl = ''):
	res = ''
	for o in lst:
		if len(res) == 0:
			res = o
		else:
			res += spl + o
	return res

def clean_soup(soup):
	for x in soup.find_all(re.compile('^(script|noscript|style|object)$', re.IGNORECASE)):
		x.decompose()

class progressbar:
	def __init__(self, length = 30):
		self.text_left = ''
		self.text_right = ''
		self.block_char = '#'
		self.empty_char = '-'
		self.length = length
		self._blks = 0

	def show(self, newline = True):
		if newline:
			sys.stdout.write('\n')
		else:
			sys.stdout.write('\r')
		sys.stdout.write(self.text_left)
		sys.stdout.write(self.block_char * self._blks)
		sys.stdout.write(self.empty_char * (self.length - self._blks))
		sys.stdout.write(self.text_right)
		sys.stdout.flush()

	def on_progress_changed(self, prog, forcerefresh = False):
		newblk = int(prog * self.length)
		if forcerefresh or newblk != self._blks:
			self._blks = newblk
			self.show(False)

	def on_done(self, donestr):
		sys.stdout.write('\r')
		sys.stdout.write(self.text_left)
		sys.stdout.write(donestr)
		sys.stdout.write(self.text_right)
		if len(donestr) < self.length:
			sys.stdout.write(' ' * (self.length - len(donestr)))
		sys.stdout.write('\n')
		sys.stdout.flush()

imgsgot = 0
imgsf = 0
totpgn = 0
images_got = set()
file_writer = None
image_writer = None

def extract_image_related_text(node, maxlen = 50):
	lastcontent = ''
	while not node.parent is None:
		node = node.parent
		ccn = node.get_text(' ', strip = True)
		if len(ccn) > maxlen:
			break
		lastcontent = ccn
	return lastcontent

def ensure_relative_folder_exists(folder):
	if not os.path.exists(folder):
		os.mkdir(folder)

def process_single_file(iv, jv, kv, filename, url):
	global imgsgot, imgsf, totpgn, images_got, file_writer, image_writer

	domain = urlparse.urlsplit(url)
	spdm = domain.hostname.split('.')
	domain = []
	for i in range(len(spdm)):
		domain.append('.'.join(spdm[i:]))
	domain = ' '.join(domain)  # hack it!
	with open(filename, 'r') as pagereader:
		contents = pagereader.read().decode('utf8')
	soup = BeautifulSoup(contents, 'html.parser')
	# index page
	clean_soup(soup)
	contents = soup.get_text(' ', strip = True).lower()
	clean_path = '/'.join((str(iv), str(jv), str(kv)))
	with open(os.path.join(FOLDER_RAWCONTENTS, clean_path), 'w') as ccsaver:
		ccsaver.write(contents.encode('utf8'))
	contents = join_strings(jieba.cut_for_search(contents), ' ')
	title = ''
	tgen = soup.find_all('title')
	if len(tgen) > 0:
		title = join_strings((x.strip() for x in tgen[0].strings)).replace('\n', '')
	doc = Document()
	doc.add(StringField('name', filename, Field.Store.YES))
	doc.add(Field('path', clean_path, Field.Store.YES, Field.Index.NOT_ANALYZED))
	doc.add(TextField('title', title, Field.Store.YES))
	doc.add(Field('url', url, Field.Store.YES, Field.Index.NOT_ANALYZED))
	doc.add(TextField('contents', contents, Field.Store.NO))
	doc.add(TextField('domain', domain, Field.Store.YES))
	file_writer.addDocument(doc)
	# index images
	imgs = soup.find_all('img')
	for x in imgs:
		try:
			img = normalize_url(urlparse.urljoin(url, x.get('src', '')))
			if not img in images_got:
				images_got.add(img)
				img_title = x.get('title', '').lower()
				alt = x.get('alt', '').lower()
				info = join_strings(jieba.cut_for_search(' '.join(
					(img_title, alt, extract_image_related_text(x))
				).lower()), ' ')

				doc = Document()
				doc.add(Field('url', img, Field.Store.YES, Field.Index.NOT_ANALYZED))
				doc.add(Field('page', url, Field.Store.YES, Field.Index.NOT_ANALYZED))
				doc.add(StringField('domain', domain, Field.Store.YES))
				doc.add(TextField('pagetitle', title, Field.Store.YES))
				doc.add(Field('title', img_title, Field.Store.YES, Field.Index.NOT_ANALYZED))
				doc.add(Field('alt', alt, Field.Store.YES, Field.Index.NOT_ANALYZED))
				doc.add(TextField('info', info, Field.Store.YES))  # for debug
				image_writer.addDocument(doc)
				imgsgot += 1
		except:
			imgsf += 1
	# done
	sys.stdout.write('\rpages: {0}  img: {1} ({2} failed)     '.format(totpgn, imgsgot, imgsf))
	sys.stdout.flush()
	totpgn += 1

def main():
	global file_writer, image_writer

	lucene.initVM(vmargs=['-Djava.awt.headless=true'])
	jieba.initialize()
	ensure_relative_folder_exists(FOLDER_INDEXED)
	ensure_relative_folder_exists(FOLDER_INDEXED_IMAGES)
	ensure_relative_folder_exists(FOLDER_RAWCONTENTS)
	file_cfg = IndexWriterConfig(Version.LUCENE_CURRENT, WhitespaceAnalyzer())
	file_cfg.setOpenMode(IndexWriterConfig.OpenMode.CREATE_OR_APPEND)
	file_writer = IndexWriter(SimpleFSDirectory(File(FOLDER_INDEXED)), file_cfg)
	img_cfg = IndexWriterConfig(Version.LUCENE_CURRENT, WhitespaceAnalyzer())
	img_cfg.setOpenMode(IndexWriterConfig.OpenMode.CREATE_OR_APPEND)
	image_writer = IndexWriter(SimpleFSDirectory(File(FOLDER_INDEXED_IMAGES)), img_cfg)

	walk_stashed_pages(
		FOLDER_TO_INDEX,
		process_single_file,
		lambda x, y: ensure_relative_folder_exists(os.path.join(FOLDER_RAWCONTENTS, str(x))),
		lambda x, y, z: ensure_relative_folder_exists(os.path.join(FOLDER_RAWCONTENTS, str(x), str(y)))
	)
	sys.stdout.write('\n')
	sys.stdout.write('Commiting... ')
	sys.stdout.flush()
	file_writer.commit()
	file_writer.close()
	image_writer.commit()
	image_writer.close()
	sys.stdout.write('done\n')
	sys.stdout.flush()

if __name__ == '__main__':
	main()
