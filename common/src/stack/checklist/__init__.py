import os
import stack.api
import stack.commands
from stack.exception import ArgRequired, ArgUnique, CommandError
import sys
import time

dhcp_start = 0

def timeit(method):

	def timed(*args, **kwargs):
		global dhcp_start
		method(*args, **kwargs)
		end = time.time()

		if dhcp_start == 0:
			return

		elapsed = end - dhcp_start
		method_name = method.__name__
		
		if elapsed > BackendSystemTest.time_arr[method_name]:
			print('!!! %s - Timed out !!!' % method_name)

	return timed

class Command(stack.commands.Command):
	
	# Time in seconds for each stage
	time_arr    = {'process_dhcp' : 60, 'process_tftp' : 120}

	def run(self, params, args):
		dictObj = {}

		if len(args) == 1:
			dictObj['hostname'] = args[0]
		else:
			raise ArgRequired(self, 'hostname')

		op = stack.api.Call('list.host', args)
		if len(op) == 0:
			raise CommandError(self, 'invalid hostname')
		elif len(op) > 1:
			raise ArgUnique(self, 'host')

		bootaction = op[0]['installaction']

		op = stack.api.Call('list.host.interface', args)
		for o in op:
			# Check with Anoop
			if o['default']:
				dictObj['ip']  = o['ip']
				dictObj['mac'] = o['mac']

		op = stack.api.Call('list.host.boot', args)
		atype = op[0]['action']

		op = stack.api.Call('list.bootaction', ['bootaction=%s' % bootaction, 'type=%s' % atype])
		dictObj['kernel']  = op[0]['kernel']
		dictObj['ramdisk'] = op[0]['ramdisk']

		self.runPlugins(dictObj)
