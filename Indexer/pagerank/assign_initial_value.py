#!/usr/bin/env python
import sys, mr_common
sys.path.append('../..')

def main():
	lines = []
	with open('analyze_result', 'r') as fin:
		for x in fin.readlines():
			sr = x.split()
			if len(sr) > 0:
				lines.append(sr)
	with open('iter_input', 'w') as fout:
		v = str(1.0 / len(lines))
		for x in lines:
			fout.write('{0}\t{1}\t{2}\n'.format(x[0], v, ' '.join(x[1:])))

if __name__ == '__main__':
	main()
