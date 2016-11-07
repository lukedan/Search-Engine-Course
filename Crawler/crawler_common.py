import traceback, sys, urllib, urllib2, time, urlparse, subprocess
sys.path.append('..')
from common import *

C_INIT = 'i'
C_PENDING = 'n'
C_SUCCESS = 's'
C_FAILED = 'f'
C_QUIT = 'q'

S_NEWURL = 'N'
S_RETRY = 'R'
S_PEND = 'P'
S_SHUTDOWN = 'S'

UNKNOWN_SESSION = '<UNK>'
SESSION_ID_DELIMETER = '$'

SAVE_FOLDER = './downloaded/'

BROADCAST_DEST = ('<broadcast>', 1238)
BROADCAST_CONTENT = 'CRAWLER_FIND_SERVER'
SERVER_PORT = 1237
USER_AGENT = 'YYTZCrawler'

NO_JAVASCRIPT = True

def on_exception(e, msg = 'Exception {type} caught at\n{tb}\n{msg}'):
	print('\n##########')
	print(msg.format(type = str(type(e)), tb = ''.join(traceback.format_tb(sys.exc_info()[2])), msg = str(e)))
	print('##########')

DEFAULT_REQUEST_HEADERS = {
	'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'
}

def get_page_rawhtml(url, headers = DEFAULT_REQUEST_HEADERS, **kwargs):
	response = urllib2.urlopen(urllib2.Request(url = url, headers = headers), **kwargs)
	msg = response.info()
	if msg.getmaintype() != 'text':
		raise TypeError('content is not text')
	coding = msg.getencoding()
	html = response.read()
	if coding == '7bit':
		coding = 'utf8'
	try:
		html = html.decode(coding)
	except:
		html = html.decode('utf8')
	return html
