#!/usr/bin/env python
import sys
sys.path.append('../..')
from common import *
from settings import *

def main():
	def get_data(d, url):
		if url not in d.keys():
			d[url] = [len(d), []]
		return d[url]

	def on_page(d, sig, x, y, z, path, url):
		with open(path, 'r') as fin:
			pgdata = fin.read()
		reslst = []
		for lnk in get_all_links(url, pgdata):
			reslst.append(get_data(d, lnk)[0])
		reslst.sort()
		tarapp = get_data(d, url)
		last = -1
		for i in reslst:
			if i != last:
				last = i
				tarapp[1].append(last)
		sig.update()

	class _upd_sig:
		def __init__(self, msg):
			self._i = 0
			self._msg = msg

		def update(self):
			self._i += 1
			sys.stdout.write('\r' + self._msg + str(self._i) + '    ')
			sys.stdout.flush()

	dic = {}
	updr = _upd_sig('pages: ')
	walk_stashed_pages('../' + FOLDER_TO_INDEX, lambda *args: on_page(dic, updr, *args))
	sys.stdout.write('\ncommiting...')
	with open('analyze_result', 'w') as fout:
		for v in dic.values():
			fout.write('{0}\t{1}\n'.format(v[0], ' '.join((str(x) for x in v[1]))))
	with open('analyze_result_mapping', 'w') as fout:
		for k, v in dic.items():
			fout.write('{0}\t{1}\n'.format(v[0], k))
	print

if __name__ == '__main__':
	main()
