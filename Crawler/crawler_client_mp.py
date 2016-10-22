from crawler_common import *
import crawler_client, time

def main():
	targetip = raw_input('Server address (leave blank to automatically search for a server): ').strip()
	if len(targetip) == 0:
		targetip = crawler_client.get_srv_dest_broadcast()
	numts = input('Number of processes: ')
	procs = []
	for i in range(numts):
		procs.append(subprocess.Popen(('python', 'crawler_client.py', targetip, str(i))))
	while True:
		termd = 0
		for x in procs:
			if not x.returncode is None:
				termd += 1
		if termd == len(procs):
			break
		time.sleep(1)

if __name__ == '__main__':
	main()
