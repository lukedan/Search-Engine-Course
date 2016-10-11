import traceback, sys, urllib, urllib2, time, urlparse, subprocess

C_INIT = 'i'
C_PENDING = 'n'
C_SUCCESS = 's'
C_FAILED = 'f'
C_QUIT = 'q'  # TODO

S_NEWURL = 'N'
S_RETRY = 'R'
S_PEND = 'P'
S_SHUTDOWN = 'S'  # TODO

SESSION_ID_DELIMETER = '$'

SAVE_FOLDER = './downloaded/'

BROADCAST_DEST = ('<broadcast>', 1238)
BROADCAST_CONTENT = 'CRAWLER_FIND_SERVER'
SERVER_PORT = 1237
USER_AGENT = 'YYTZCrawler'

def on_exception(e, msg = 'Exception {type} caught at\n{tb}\n{msg}'):
	print('\n##########')
	print(msg.format(type = str(type(e)), tb = ''.join(traceback.format_tb(sys.exc_info()[2])), msg = str(e)))
	print('##########')

DEFAULT_REQUEST_HEADERS = {
	'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'
}

def get_page_rawhtml(url, headers = DEFAULT_REQUEST_HEADERS, **kwargs):
	html = urllib2.urlopen(urllib2.Request(url = url, headers = headers), **kwargs).read()
	try:
		html = html.decode('utf8')
	except:
		html = html.decode('GBK')
	return html

def normalize_url(url):
	def to_ascii(ustr):
		return urllib.unquote_plus(urllib.quote_plus(ustr.encode('utf8'))).replace('\n', '%0d')

	url = urlparse.urlsplit(url)
	nlofurl = url.hostname.encode('idna').lower()
	if not url.port is None:
		nlofurl += ':' + str(url.port)
	pathofurl = to_ascii(url.path).lower()
	if pathofurl.endswith('/'):
		pathofurl = pathofurl[:-1]
	return urlparse.urlunsplit((to_ascii(url.scheme).lower(), nlofurl, pathofurl, to_ascii(url.query), ''))

class phased_timer:
	def __init__(self):
		self._ps = []
		self._lt = 0.0
		self._ln = ''

	def start(self, name):
		self._lt = time.clock()
		self._ln = name

	def tick(self, name):
		ct = time.clock()
		self._ps.append((self._ln, ct - self._lt))
		self._lt = ct
		self._ln = name

	def stop(self):
		self._ps.append((self._ln, time.clock() - self._lt))
		x = self._ps
		self._ps = []
		return x

	@staticmethod
	def format_table(tbl, mid = ': '):
		fms = '%' + str(max((len(x[0]) for x in tbl))) + 's' + mid + '%.04f'
		res = []
		for x in tbl:
			res.append(fms % (x[0], x[1]))
		return '\n'.join(res)

	@staticmethod
	def format_message(tbl):
		res = []
		for x in tbl:
			res.append('%s: %.02f' % (x[0], x[1]))
		return '  '.join(res) + '\n'

class null_logger:
	def __init__(self):
		pass

	def write(self, dummy):
		pass

class common_logger:
	def __init__(self, f = sys.stdout):
		self.file = f

	def write(self, s):
		self.file.write(s)
		self.file.flush()

class external_console_logger:
	def __init__(self, logfile, mode = 'w'):
		self._file = open(logfile, mode)
		self._disp = subprocess.Popen(['gnome-terminal', '-x', 'tail', '-f', logfile])

	def write(self, s):
		self._file.write(s)
		self._file.flush()

def execute_commands_until(target_cmd, prefix, lup_tbl):
	while True:
		cmd = list(raw_input('> ').split())
		if len(cmd) == 0:
			continue
		cmd[0] = cmd[0].lower()
		if cmd[0] == target_cmd:
			break
		cmdn = prefix + cmd[0]
		if cmdn in lup_tbl.keys():
			try:
				lup_tbl[cmdn](*cmd[1:])
			except Exception as e:
				print('Exception thrown during the execution of command: ' + str(e))
		else:
			print('Unrecognized command: ' + cmd[0])
