from crawler_common import *
import re, urlparse, os, platform, socket, time, sys, Queue, threading, random
from bs4 import BeautifulSoup

try:
	from selenium import webdriver

	if platform.system().lower() == 'windows':
		PHANTOMJS_PATH = 'phantomjs.exe'
	else:
		PHANTOMJS_PATH = './phantomjs'
	webdriver.DesiredCapabilities.PHANTOMJS["phantomjs.page.settings.loadImages"] = False
	webdriver.DesiredCapabilities.PHANTOMJS["phantomjs.page.settings.resourceTimeout"] = 5000
except ImportError:
	webdriver = None  # disable the warning
	print(
		"Warning: Selenium package not found on your computer. "
		"You won't be able to access advanced features of the crawler."
	)

class phantomjs_driver:
	def __init__(self):
		self.underlying_drvr = webdriver.PhantomJS(executable_path = PHANTOMJS_PATH,
			service_log_path = os.path.devnull)

	def get(self, pg):
		self.underlying_drvr.get(pg)
		return self.underlying_drvr.page_source

class rawhtml_driver:
	def __init__(self):
		self.headers = DEFAULT_REQUEST_HEADERS
		self.timeout = 10.0

	def get(self, pg):
		return get_page_rawhtml(pg, self.headers, timeout = self.timeout)

class immediate_webpage_saver:
	def __init__(self, sn, folder = SAVE_FOLDER):
		self._folder = os.path.join(folder, sn)
		if not os.path.exists(folder):
			os.mkdir(folder)
		if not os.path.exists(self._folder):
			os.mkdir(self._folder)
		self._idxw = open(os.path.join(self._folder, 'index'), 'w')
		self._id = 0

	def buffered_size(self):
		return 0

	def shutdown(self):
		self._idxw.close()

	def shutdown_and_wait(self):
		self.shutdown()

	def has_shutdown(self):
		return True

	def write(self, pgname, cont):
		with open(os.path.join(self._folder, str(self._id)), 'w') as fout:
			fout.write(cont.encode('utf8'))
		self._idxw.write((str(self._id) + '\t' + pgname).encode('utf8'))
		self._id += 1

class async_webpage_saver:
	def __init__(self, folder = SAVE_FOLDER, nts = 5):
		self._q = Queue.Queue()
		self._stopped = False
		self._num = threading.Semaphore(nts)
		self._sz = 0
		self._szl = threading.Lock()
		if not os.path.exists(folder):
			os.mkdir(folder)
		for i in range(nts):
			t = threading.Thread(
				target = async_webpage_saver._thread_work,
				args = (self, os.path.join(folder, str(i))),
				name = 'IOWriterThread #' + str(i)
			)
			t.setDaemon(True)
			t.start()

	def buffered_size(self):
		return self._sz * 2

	def shutdown(self):
		self._stopped = True

	def shutdown_and_wait(self):
		self.shutdown()
		while not self.has_shutdown():
			pass

	def has_shutdown(self):
		return self._num > 0

	def write(self, pgname, cont):
		self._update_sz(len(cont))
		self._q.put((pgname, cont))

	def _update_sz(self, diff):
		self._szl.acquire()
		try:
			self._sz += diff
		finally:
			self._szl.release()

	def _thread_work(self, folder):
		if not os.path.exists(folder):
			os.mkdir(folder)
		indexwriter = open(os.path.join(folder, 'index'), 'w')
		try:
			filename = 0
			while True:
				if self._stopped:
					try:
						item = self._q.get(False)
					except Queue.Empty:
						break
				else:
					item = self._q.get()
				self._update_sz(-len(item[1]))
				try:
					indexwriter.write(str(filename) + '\t' + item[0] + '\n')
					with open(os.path.join(folder, str(filename)), 'w') as out:
						out.write(item[1].encode('utf8'))
				except Exception, e:  # TODO handle it
					on_exception(e)
				filename += 1
		finally:
			self._num.release()
			indexwriter.close()

class crawler_session:
	PENDING = 0
	COMM_CONNECT = 1
	COMM_SEND = 2
	COMM_RECV = 3
	GETPAGE = 4
	SAVEPAGE = 5
	SHUTDOWN = 6
	stat_description_mapping = (
		'Pending',
		'ServerConnecting',
		'SendingToServer',
		'ReceivingFromServer',
		'GettingPage',
		'SavingPage',
		'Shutdown'
	)

	def __init__(self, srv = ('', SERVER_PORT), wrtr = None, drv = None, log = None):
		self.server = srv
		self.writer = wrtr
		self.driver = drv
		self.logger = log
		self.pend_message = '{session}: Pending...\n'
		self.preget_msg = '{session}: Getting {page}...'
		self.postget_msg = ' done\n'
		self.write_stat_update_message = False
		self.write_timing_message = True
		self.write_error_message = True
		self.stop = False
		self.session_name = None
		self.status = crawler_session.SHUTDOWN
		self.cur_page = None

	def get_description(self):
		desc = crawler_session.stat_description_mapping[self.status]
		if self.status in (crawler_session.GETPAGE, crawler_session.SAVEPAGE):
			desc += ': ' + self.cur_page
		return desc

	def submit_and_acquire(self, data):
		timer = phased_timer()
		timer.start('crat')
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.status = crawler_session.COMM_CONNECT
		timer.tick('conn')
		sock.connect(self.server)
		try:
			self.status = crawler_session.COMM_SEND
			timer.tick('send')
			sock.sendall(data)
			self.status = crawler_session.COMM_RECV
			timer.tick('recv')
			msg = sock.recv(4096)
		finally:
			sock.close()
			if self.write_timing_message:
				sn = self.session_name
				if sn is None:
					sn = UNKNOWN_SESSION
				timres = timer.stop()
				if phased_timer.has_critical(timres):
					self.logger.write(sn + ': ' + phased_timer.format_message(timres))
		return msg

	@staticmethod
	def split_simple(data):
		return data[0], data[1:]

	@staticmethod
	def split_on_init(data):
		spr = data.split(SESSION_ID_DELIMETER)
		s1 = SESSION_ID_DELIMETER.join(spr[1:])
		return spr[0], s1[0], s1[1:]

	def post_and_recv(self, sig, msg = ''):
		return crawler_session.split_simple(
			self.submit_and_acquire(''.join((sig, self.session_name, SESSION_ID_DELIMETER, msg))))

	def init_connection(self):
		session, stat, pg = UNKNOWN_SESSION, S_PEND, ''
		while True:
			try:
				session, stat, pg = crawler_session.split_on_init(self.submit_and_acquire(C_INIT))
				break
			except Exception as emsg:
				on_exception(emsg)
		return session, stat, pg

	def crawl_until_stop(self):
		self.status = crawler_session.PENDING
		self.session_name, stat, self.cur_page = self.init_connection()
		while True:
			if stat == S_SHUTDOWN:
				break
			elif stat == S_PEND:
				self.status = crawler_session.PENDING
				if self.write_stat_update_message:
					self.logger.write(self.pend_message.format(session = self.session_name))
				time.sleep(2)
				commmsg = (C_PENDING, '')
			else:
				timer = phased_timer()
				timer.start('getpage')
				try:
					if self.write_stat_update_message:
						self.logger.write(self.preget_msg.format(session = self.session_name, page = self.cur_page))
					self.status = crawler_session.GETPAGE
					content = self.driver.get(self.cur_page)
					if self.write_stat_update_message:
						self.logger.write(self.postget_msg.format(session = self.session_name, page = self.cur_page))
				except Exception as msg:
					self.status = crawler_session.PENDING
					commmsg = (C_FAILED, self.cur_page + '\n' + str(msg) + '\n')
				else:
					timer.tick('savepage')
					self.status = crawler_session.SAVEPAGE
					self.writer.write(self.cur_page, content)
					timer.tick('getlinks')
					lst = get_all_links(self.cur_page, content)
					commmsg = (C_SUCCESS, str(len(lst)) + '\n' + '\n'.join(lst) + '\n')
				if self.write_timing_message:
					timres = timer.stop()
					if phased_timer.has_critical(timres, ign = ('getpage',)):
						self.logger.write(self.session_name + ': ' + phased_timer.format_message(timres))
			if self.stop:
				commmsg = (C_QUIT + commmsg[0],) + commmsg[1:]
			while True:
				try:
					stat, self.cur_page = self.post_and_recv(*commmsg)
					break
				except Exception as msg:
					self.logger.write('[COMMFAIL] ' + str(msg) + '\n')
					time.sleep(2)
		self.status = crawler_session.SHUTDOWN

def get_srv_dest_broadcast():
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	sock.settimeout(2)
	addr = ''
	sys.stdout.write('Searching for server')
	try:
		while True:
			try:
				sys.stdout.write('.')
				sys.stdout.flush()
				sock.sendto(BROADCAST_CONTENT, BROADCAST_DEST)
				dummy, addr = sock.recvfrom(1)
				addr = addr[0]
				print(' found ' + addr)
				break
			except socket.timeout:
				pass
	finally:
		sock.close()
	return addr

def main():
	if len(sys.argv) == 1:
		targetip = raw_input('Server address (leave blank to automatically search for a server): ').strip()
	else:
		targetip = sys.argv[1]
	if len(targetip) == 0:
		targetip = get_srv_dest_broadcast()
	if len(sys.argv) > 2:
		myid = sys.argv[2]
	else:
		myid = str(random.randint(0, 65535))
	writer = immediate_webpage_saver(myid)
	if NO_JAVASCRIPT:
		driver = rawhtml_driver()
	else:
		try:
			driver = phantomjs_driver()
		except NameError:
			driver = rawhtml_driver()
	logger = common_logger()
	session = crawler_session((targetip, SERVER_PORT), writer, driver, logger)
	session.crawl_until_stop()

if __name__ == '__main__':
	main()
