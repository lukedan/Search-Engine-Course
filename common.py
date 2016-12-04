import traceback, sys, urllib, urllib2, time, urlparse, subprocess, os, re
from bs4 import BeautifulSoup

def normalize_url(url):
	def to_ascii(ustr):
		return urllib.quote_plus(urllib.unquote_plus(ustr.encode('utf8')))

	url = urlparse.urlsplit(url)
	nlofurl = url.hostname.encode('idna')
	if ':' in nlofurl:
		raise NameError('invalid hostname')
	if not url.port is None:
		nlofurl += ':' + str(url.port)
	pathlist = url.path.split('/')
	pathofurl = ''
	for x in pathlist:
		if len(x) > 0:
			pathofurl += '/' + to_ascii(x.lower())
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
	def has_critical(tbl, ctt = 0.5, ign = ()):
		for x in tbl:
			if x[0] not in ign and x[1] > ctt:
				return True
		return False

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

def exec_in_new_console(cmd):
	return subprocess.Popen(('gnome-terminal', '-x') + cmd)

class external_console_logger:
	def __init__(self, logfile, mode = 'w'):
		self._file = open(logfile, mode)
		self._disp = exec_in_new_console(('tail', '-f', logfile))

	def write(self, s):
		self._file.write(s)
		self._file.flush()

def list_commands(prefix, lup_tbl):
	for x in lup_tbl.keys():
		if x.startswith(prefix):
			sys.stdout.write('%15s' % x[4:])
	sys.stdout.write('\n')
	sys.stdout.flush()

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

def get_all_links(curpage, pgdata):
		# for x in re.findall('<\s*[Aa]\s(?:"(?:\\\\|\\"|[^"])*"|[^>])*?\s[Hh][Rr][Ee][Ff]\s*=\s*"((?:http|/)(?:\\\\|\\"|[^"])*)', pgdata):
		# 	print x
		soup = BeautifulSoup(pgdata, 'html.parser')
		res = []
		for x in soup.find_all('a', {'href': re.compile('^(http|/)')}):
			try:
				url = normalize_url(urlparse.urljoin(curpage, x['href'].strip()))
				res.append(url)
			except:
				pass
		return res

def walk_stashed_pages(directory, callback, on_fdr = None, on_thd = None):
	fdr = 0
	fdrp = os.path.join(directory, str(fdr))
	while os.path.exists(fdrp):
		thd = 0
		thdp = os.path.join(fdrp, str(thd))
		if on_fdr:
			on_fdr(fdr, fdrp)
		while os.path.exists(thdp):
			if on_thd:
				on_thd(fdr, thd, thdp)
			with open(os.path.join(thdp, 'index'), 'r') as fin:
				for x in fin.readlines():
					r = x.strip().split('\t')
					if len(r) < 2:
						continue
					callback(fdr, thd, int(r[0]), os.path.join(thdp, r[0]), '\t'.join(r[1:]))
			thd += 1
			thdp = os.path.join(fdrp, str(thd))
		fdr += 1
		fdrp = os.path.join(directory, str(fdr))
