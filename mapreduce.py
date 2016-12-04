#!/usr/bin/env python
import sys, os

USAGE = """\
Usage: exec [input] [output] ([commands] --) [mapper1] [reducer1] ([mapper2] [reducer2] ...)
    -t1    specify temporary folder 1
    -t2    specify temporary folder 2
    -n     set the job name
    -w     set the working directory
    -i     set the job info format
    -a     add an additional file
    -c     customize the hadoop command
"""

NONE = 'NONE'
DEFAULT_INFO = \
"""
 #########################################
 # Round {round}
 #  mapper:  {mapper}
 #  reducer: {reducer}
 #  input:   {input}
 #  output:  {output}
 #########################################
"""
DEFAULT_CMD = '\
hadoop fs -rm -r {output}; \
hadoop jar /usr/local/hadoop/share/hadoop/tools/lib/hadoop-streaming-2.2.0.jar \
	-files {all_files} -mapper {mapper} -reducer {reducer} -input {input} -output {output} {addparams} \
'

def exec_mapreduce(inp, outp, steps, t1 = '', t2 = '', afil = (), aparam = '', cmd = DEFAULT_CMD, inf = DEFAULT_INFO):
	tempf = (inp, t1, t2, outp)
	ctv = 0
	for i in range(len(steps)):
		nv = 1
		if i == len(steps) - 1:
			nv = 3
		elif ctv == 1:
			nv = 2
		kwdict = {
			'round': i + 1,
			'all_files': ','.join(steps[i] + tuple(afil)),
			'mapper': steps[i][0],
			'reducer': steps[i][1],
			'input': tempf[ctv],
			'output': tempf[nv],
			'addparams': aparam
		}
		print inf.format(**kwdict)
		os.system(cmd.format(**kwdict))
		ctv = nv

class _command_exec:
	def __init__(self, ps = sys.argv):
		self.command = DEFAULT_CMD
		self.info = DEFAULT_INFO
		self.working_dir = os.getcwd()
		self.t1 = ''
		self.t2 = ''
		self.add_params = []
		self.add_files = []
		self.args = ps
		self.input = self.args[1]
		self.output = self.args[2]

		cp = 3
		while cp < len(self.args):
			curopt = self.args[cp]
			if curopt[0] == '-' and '_' + curopt[1:] in vars(self).keys():
				vars(self)['_' + curopt[1:]](self.args[cp + 1])
			else:
				if curopt == '--':
					cp += 1
				break
			cp += 2

		files = self.args[cp:]
		for i in range(len(files)):
			files[i] = os.path.join(self.working_dir, files[i])
		steps = []
		for i in range(len(files) / 2):
			steps.append((files[i * 2], files[i * 2 + 1]))
		exec_mapreduce(
			self.input, self.output, steps, self.t1, self.t2,
			self.add_files, ' '.join(self.add_params), self.command, self.info
		)

	def _t1(self, v):
		self.t1 = v

	def _t2(self, v):
		self.t2 = v

	def _n(self, v):
		self.add_params.append('-jobconf mapred.job.name=\"{0}\"'.format(v))

	def _w(self, v):
		self.working_dir = v

	def _i(self, v):
		self.info = v

	def _a(self, v):
		self.add_files.append(v)

	def _c(self, v):
		self.command = v

def main():
	if len(sys.argv) < 5:
		print USAGE
		return

	_command_exec()

if __name__ == '__main__':
	main()
