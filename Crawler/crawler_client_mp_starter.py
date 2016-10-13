from crawler_common import *
import crawler_client

def main():
	targetip = raw_input('Server address (leave blank to automatically search for a server): ').strip()
	if len(targetip) == 0:
		targetip = crawler_client.get_srv_dest_broadcast()
	numts = input('Number of processes: ')
	for i in range(numts):
		exec_in_new_console(('python', 'crawler_client.py', targetip))

if __name__ == '__main__':
	main()
