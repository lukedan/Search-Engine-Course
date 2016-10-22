from crawler_common import *
import crawler_client, threading, time

crawlers = []
writer = crawler_client.async_webpage_saver()
logger = external_console_logger('/tmp/crawlermt_log.txt')

def _cclmt_list():
	list_commands('_cclmt_', globals())

def _cclmt_stat():
	print('writer_cache_size\t' + str(writer.buffered_size()))
	for x in crawlers:
		print(x.session_name + ':\t' + x.get_description())

def main():
	global crawlers, writer, logger
	targetip = raw_input('Server address (leave blank to automatically search for a server): ').strip()
	if len(targetip) == 0:
		targetip = crawler_client.get_srv_dest_broadcast()
	numts = input('Number of threads: ')
	for i in range(numts):
		if NO_JAVASCRIPT:
			driver = crawler_client.rawhtml_driver()
		else:
			try:
				driver = crawler_client.phantomjs_driver()
			except NameError:
				driver = crawler_client.rawhtml_driver()
		cc = crawler_client.crawler_session(
			(targetip, SERVER_PORT),
			writer,
			driver,
			logger
		)
		cc.pend_message = '.'
		cc.preget_msg = '<'
		cc.postget_msg = '>'
		cc.write_stat_update_message = False
		crawlers.append(cc)
		t = threading.Thread(target = cc.crawl_until_stop, name = 'CrawlerThread #' + str(i))
		t.setDaemon(True)
		t.start()

	execute_commands_until('exit', '_cclmt_', globals())

	for x in crawlers:
		x.stop = True
	while True:
		left = len(crawlers)
		for x in crawlers:
			if x.status == crawler_client.crawler_session.SHUTDOWN:
				left -= 1
		if left == 0:
			break
		sys.stdout.write('\r' + str(left) + ' sessions remaining...  ')
		sys.stdout.flush()
		time.sleep(1)
	sys.stdout.write('\rAll sessions shutdown          \n')
	writer.shutdown()
	while not writer.has_shutdown():
		sys.stdout.write('\rRemaining data: ' + str(writer.buffered_size()) + '  ')
		sys.stdout.flush()
	sys.stdout.write('\n')

if __name__ == '__main__':
	main()
