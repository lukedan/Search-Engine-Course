from crawler_common import *
import socket, SocketServer, collections, threading, sys, urlparse, robotparser, Queue

LOGFILE_PATH = '/tmp/server_log.txt'
log = external_console_logger(LOGFILE_PATH)

class trie:
	class node:
		def __init__(self, cont = 0):
			self.content = cont
			self.outf = {}
			self.tag = None
			self.lock = None

	def __init__(self):
		self._root = trie.node()
		self._lock = threading.Lock()

	def get_node(self, cont):
		self._lock.acquire()
		try:
			cur_node = self._root
			for x in cont:
				k = ord(x)
				if k not in cur_node.outf.keys():
					nex = trie.node(k)
					cur_node.outf[k] = nex
					cur_node = nex
				else:
					cur_node = cur_node.outf[k]
			if cur_node.lock is None:
				cur_node.lock = threading.Lock()
		finally:
			self._lock.release()
		return cur_node

class hash_table:
	_HASH_TABLE_SIZE = 1000007

	def __init__(self):
		self._h = []
		for i in range(hash_table._HASH_TABLE_SIZE):
			self._h.append([])
		self.hash_func = hash
		self._lock = threading.Lock()

	def put(self, obj):
		hv = self.hash_func(obj) % hash_table._HASH_TABLE_SIZE
		self._lock.acquire()
		try:
			if obj not in self._h[hv]:
				self._h[hv].append(obj)
				return True
			return False
		finally:
			self._lock.release()

	def has(self, obj):
		self._lock.acquire()
		try:
			return obj in self._h[self.hash_func(obj) % hash_table._HASH_TABLE_SIZE]
		finally:
			self._lock.release()

class bloom_filter:
	_BLOOM_FILTER_SIZE = 1000007

	@staticmethod
	def test_bit(lng, b):
		return (lng >> b) % 2 == 0

	@staticmethod
	def set_bit(lng, b):
		return lng | (long(1) << b)

	def __init__(self):
		self._ba = long(0)
		self.hash_funcs = []
		self._lock = threading.Lock()

	def _get_hv_list(self, obj):
		res = []
		for x in self.hash_funcs:
			res.append(x(obj) % bloom_filter._BLOOM_FILTER_SIZE)
		return res

	def put_nocheck(self, obj):
		hvl = self._get_hv_list(obj)
		self._lock.acquire()
		try:
			for x in hvl:
				self._ba = bloom_filter.set_bit(self._ba, x)
		finally:
			self._lock.release()

	def put(self, obj):
		dosth = False
		hvl = self._get_hv_list(obj)
		self._lock.acquire()
		try:
			for x in hvl:
				if not bloom_filter.test_bit(self._ba, x):
					dosth = True
					self._ba = bloom_filter.set_bit(self._ba, x)
			return dosth
		finally:
			self._lock.release()

	def has(self, obj):
		hvl = self._get_hv_list(obj)
		self._lock.acquire()
		try:
			for x in hvl:
				if not bloom_filter.test_bit(self._ba, x):
					return False
			return True
		finally:
			self._lock.release()

class hash_table_donelist:
	@staticmethod
	def hash_func(url):
		res = 0
		for x in url:
			res = (res * 131 + ord(x))
		return res

	def __init__(self):
		self._ht = hash_table()
		self._ht.hash_func = hash_table_donelist.hash_func

	def put(self, url):
		return self._ht.put(url)

	def has(self, url):
		return self._ht.has(url)

class bloom_filter_donelist:
	@staticmethod
	def hash_func_1(url):
		res = 0
		for x in url:
			res = (res * 131 + ord(x))
		return res

	@staticmethod
	def hash_func_2(url):
		res = 0
		for x in url:
			res = (res * 13131 + ord(x))
		return res

	def __init__(self):
		self._bf = bloom_filter()
		self._bf.hash_funcs = [bloom_filter_donelist.hash_func_1, bloom_filter_donelist.hash_func_2]

	def put(self, url):
		return self._bf.put(url)

	def has(self, url):
		return self._bf.has(url)

class test_bloom_filter_donelist:
	def __init__(self):
		self._ht = hash_table()
		self._ht.hash_func = hash_table_donelist.hash_func
		self._bf = bloom_filter()
		self._bf.hash_funcs = [bloom_filter_donelist.hash_func_1, bloom_filter_donelist.hash_func_2]
		self._htc = 0
		self._bfc = 0
		self._l = threading.Lock()

	def put(self, url):
		self._l.acquire()
		try:
			if self._ht.put(url):
				self._htc += 1
				if self._bf.put(url):
					self._bfc += 1
				return True
			return False
		finally:
			self._l.release()

	def has(self, url):
		self._l.acquire()
		try:
			return self._ht.has(url)
		finally:
			self._l.release()

	def get_bloom_filter_false_positive_ratio(self):
		if self._htc == 0:
			return 0
		return (self._htc - self._bfc) / self._htc

class advanced_url_storage:
	@staticmethod
	def get_host_url(pdurl):
		if len(pdurl.scheme) > 0:
			scheme = pdurl.scheme + ':'
		else:
			scheme = ''
		return scheme + '//' + pdurl.netloc

	@staticmethod
	def encode_host_url(pdurl):
		try:
			urlandscheme = pdurl.hostname[::-1] + '/' + pdurl.scheme
			if not pdurl.port is None:
				return urlandscheme + ':' + str(pdurl.port)
			return urlandscheme
		except:
			print str(pdurl)
			raise

	@staticmethod
	def decode_host_url(upurl):
		postfx = ''
		if ':' in upurl:
			ns = upurl.split(':')
			upurl = ns[0]
			postfx = ':' + ns[1]
		upurl = upurl.split('/')
		if len(upurl[1]) > 0:
			upurl[1] += ':'
		return ''.join((upurl[1], '//', upurl[0][::-1], postfx))

	class host_data:
		def __init__(self, pdurl):
			self.url = pdurl
			self.q = collections.deque()
			self.active = False
			self.robot = robotparser.RobotFileParser()
			self.ready = False

		def get_url(self):
			return urlparse.urlunsplit(self.url)

		def get_robot(self):
			rburl = advanced_url_storage.get_host_url(self.url) + '/robots.txt'
			try:
				self.robot.parse(get_page_rawhtml(rburl, timeout = 10.0))
			except Exception, e:
				log.write('Failed to get robots.txt at ' + rburl + ': ' + str(e) + '\n')
				self.robot = None

		def can_fetch(self, url):
			if self.robot is None:
				return True
			return self.robot.can_fetch(USER_AGENT, url)

	class crawl_stats:
		def __init__(self):
			self.popped_urls = 0
			self.urls = 0
			self.hosts = 0
			self.active_hosts = 0
			self._lock = threading.Lock()

		def lock(self):
			self._lock.acquire()

		def unlock(self):
			self._lock.release()

		def to_str(self):
			res = []
			for k, v in vars(self).items():
				if k[0] != '_':
					res.append(k)
					res.append(':\t')
					res.append(str(v))
					res.append('\n')
			return ''.join(res)

	def __init__(self):
		self._hsts = trie()
		self._hstq = Queue.Queue()
		self._dl = test_bloom_filter_donelist()
		# stuff for robots.txt
		self._waitq = Queue.Queue()
		t = threading.Thread(target = self._update_robots)
		t.setDaemon(True)
		t.start()
		# statistics
		self.stats = advanced_url_storage.crawl_stats()

	def size(self):
		return self.stats.urls - self.stats.popped_urls  # may not be accurate

	def empty(self):
		return self.size() == 0

	def _update_robots(self):
		while True:
			if self._waitq.qsize() > 0:
				host = self._waitq.get()
				host.tag.get_robot()
				newq = collections.deque()
				szdiff = 0
				host.lock.acquire()
				try:
					# filter the already-added URLs
					while len(host.tag.q) > 0:
						x = host.tag.q.popleft()
						if host.tag.can_fetch(x[0]):
							newq.append(x)
						else:
							szdiff += 1
					host.tag.q = newq
					host.tag.ready = True
					host.tag.active = True
				finally:
					host.lock.release()
				self.stats.lock()
				try:
					self.stats.urls -= szdiff
					self.stats.active_hosts += 1
				finally:
					self.stats.unlock()
				self._hstq.put(host)

	def _do_put(self, url, putfunc):
		parsed = urlparse.urlsplit(url[0])
		encoded = advanced_url_storage.encode_host_url(parsed)
		node = self._hsts.get_node(encoded)
		new_host = False
		actived_host = False
		node.lock.acquire()
		try:
			if node.tag is None:
				new_host = True
				node.tag = advanced_url_storage.host_data(parsed)
				self._waitq.put(node)
			if not node.tag.ready:
				can_add = True
			else:
				can_add = node.tag.can_fetch(url[0])
			if can_add:
				putfunc(node.tag.q, url)
				if node.tag.ready and not node.tag.active:
					actived_host = True
					node.tag.active = True
					self._hstq.put(node)
		finally:
			node.lock.release()
		self.stats.lock()
		try:
			if new_host:
				self.stats.hosts += 1
			if actived_host:
				self.stats.active_hosts += 1
			if can_add:
				self.stats.urls += 1
		finally:
			self.stats.unlock()

	def put(self, url):
		if self._dl.put(url[0]):
			self._do_put(url, collections.deque.append)

	def putback(self, url):
		self._do_put(url, collections.deque.appendleft)

	def get(self):
		curnode = self._hstq.get()
		curnode.lock.acquire()
		host_deactivated = False
		try:
			result = curnode.tag.q.popleft()
			if len(curnode.tag.q) == 0:
				host_deactivated = True
				curnode.tag.active = False
			else:
				self._hstq.put(curnode)
		finally:
			curnode.lock.release()
		self.stats.lock()
		try:
			self.stats.popped_urls += 1
			if host_deactivated:
				self.stats.active_hosts -= 1
		finally:
			self.stats.unlock()
		return result

class session_info:
	def __init__(self, sid):
		self.session_id = sid
		self._st_accum = 0.0
		self._st_up = None
		self.num_pages = 0

	def on_up(self):
		self._st_up = time.time()

	def on_down(self):
		self._st_accum += time.time() - self._st_up
		self._st_up = None

	def is_down(self):
		return self._st_up is None

	def get_uptime(self):
		if self._st_up is None:
			return self._st_accum
		return self._st_accum + time.time() - self._st_up

sto = advanced_url_storage()
paused = False
stopped = False
session_num = 0
session_rec = {}
session_rec_lock = threading.Lock()

class cralwer_tcp_handler(SocketServer.ThreadingMixIn, SocketServer.StreamRequestHandler):
	def handle(self):
		def receive_crawler_data(rf):
			def split_session_name(rfi):
				res = []
				while True:
					c = rfi.read(1)
					if c == SESSION_ID_DELIMETER:
						return ''.join(res)
					res.append(c)

			global session_num, sto, paused, stopped, session_rec, session_rec_lock
			info = rf.read(1)
			resp_pre = ''
			session_addpage = False
			ses_quit = stopped
			if info == C_INIT:
				session_rec_lock.acquire()
				try:
					cur_session_name = str(session_num)
					resp_pre = cur_session_name + SESSION_ID_DELIMETER
					session_rec[cur_session_name] = session_info(cur_session_name)
					session_num += 1
				finally:
					session_rec_lock.release()
			else:
				if info == C_QUIT:
					ses_quit = True
					info = rf.read(1)
				cur_session_name = split_session_name(rf)
				if info == C_SUCCESS:
					session_addpage = True
					numlines = int(rf.readline())
					for i in range(numlines):
						x = rf.readline().strip()
						if len(x) > 0:
							sto.put((x, S_NEWURL))
				elif info == C_FAILED:
					pg = rf.readline().strip()
					log.write('FAILED TO LOAD PAGE: ' + pg + '\n')
				# sto.putback((pg, S_RETRY))  # TODO maybe something can be done...
			session_down = (paused or ses_quit or sto.empty())
			if session_down:
				rawres = None
				respond = resp_pre + S_PEND
			else:
				rawres = sto.get()
				respond = resp_pre + rawres[1] + rawres[0]
			# update status
			session_rec_lock.acquire()
			try:
				cur_session = session_rec[cur_session_name]
				if session_addpage:
					cur_session.num_pages += 1
				if session_down != cur_session.is_down():
					if session_down:
						cur_session.on_down()
					else:
						cur_session.on_up()
				if ses_quit:
					del session_rec[cur_session_name]
					respond = S_SHUTDOWN
			finally:
				session_rec_lock.release()
			return respond, rawres

		global session_num, sto, paused, session_rec
		raw = None
		try:
			timer = phased_timer()
			timer.start('Recv')
			cdata, raw = receive_crawler_data(self.rfile)
			timer.tick('Resp')
			self.request.sendall(cdata)
			log.write(phased_timer.format_message(timer.stop()))  # TODO exception handling too weak
		except Exception, msg:
			on_exception(msg)
			if raw:
				sto.putback(raw)
			self.request.sendall(S_PEND)

def check_broadcast_and_respond():
	broadcastrecv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	broadcastrecv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	broadcastrecv.settimeout(1)
	broadcastrecv.bind(('', BROADCAST_DEST[1]))
	try:
		while True:
			try:
				data, addr = broadcastrecv.recvfrom(1000)
				if data == BROADCAST_CONTENT:
					log.write('Broadcast received from ' + str(addr) + '\n')
					broadcastrecv.sendto('', addr)
			except socket.timeout:
				pass
	finally:
		broadcastrecv.close()

def get_ip():
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		sock.connect(("10.255.255.255", 80))
		res = sock.getsockname()[0]
	finally:
		sock.close()
	return res

def start_server(srv):
	srv.serve_forever()

def _csv_list():
	for x in globals().keys():
		if x.startswith('cmd_'):
			sys.stdout.write('%15s\t' % x[4:])
	sys.stdout.write('exit\n')
	sys.stdout.flush()

def _csv_addseed(seed):
	sto.put((normalize_url(seed.decode('utf8')), S_NEWURL))

def _csv_seednum():
	print(sto.size())

def _csv_pause():
	global paused
	paused = True

def _csv_continue():
	global paused
	paused = False

def _csv_is_paused():
	global paused
	print(paused)

def _csv_fp_ratio():
	print(sto._dl.get_bloom_filter_false_positive_ratio())

def _csv_stat():
	sys.stdout.write(sto.stats.to_str())
	totut = 0.0
	print('+----+---------+-------+')
	print('| id | up time | pages |')
	print('+----+---------+-------+')
	session_rec_lock.acquire()
	try:
		ses_num = len(session_rec)
		for x in session_rec.values():
			upt = x.get_uptime()
			print('|%3s | %7.01f | %5d |' % (x.session_id, upt, x.num_pages))
			totut += upt
	finally:
		session_rec_lock.release()
	print('+----+---------+-------+')
	print('total up time:\t%.01f' % totut)
	apt = totut / sto.stats.popped_urls
	print('average page time:\t%.01f' % apt)
	print('pages per second est.:\t%.01f' % (ses_num / apt))

def main():
	global paused, sto, stopped

	t = threading.Thread(target = check_broadcast_and_respond)
	t.setDaemon(True)
	t.start()

	if len(sys.argv) > 1:
		seed = normalize_url(sys.argv[1].decode('utf8'))
		sto.put((seed, S_NEWURL))

	myip = get_ip()
	server = SocketServer.TCPServer((myip, SERVER_PORT), cralwer_tcp_handler, False)
	server.allow_reuse_address = True
	server.server_bind()
	server.server_activate()
	print 'Server is up and running on ' + myip + '...'
	t = threading.Thread(target = start_server, args = (server,))
	t.setDaemon(True)
	t.start()

	execute_commands_until('exit', '_csv_', globals())
	# on exit
	stopped = True
	while True:
		session_rec_lock.acquire()
		try:
			srl = len(session_rec)
			if srl == 0:
				break
		finally:
			session_rec_lock.release()
		sys.stdout.write('\r' + str(srl) + ' sessions remaining...  ')
		sys.stdout.flush()
		time.sleep(1)
	sys.stdout.write('\n')
	server.shutdown()

if __name__ == '__main__':
	main()
