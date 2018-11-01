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
		self.dictObj = {}

		if len(args) == 1:
			self.dictObj['hostname'] = args[0]
		else:
			raise ArgRequired(self, 'hostname')

		op = stack.api.Call('list.host', args)
		if len(op) == 0:
			raise CommandError(self, 'invalid hostname')
		elif len(op) > 1:
			raise ArgUnique(self, 'host')

		bootaction = op[0]['installaction']

		op = stack.api.Call('list.network', ['pxe=True'])
		pxe_network_list = []
		for o in op:
			pxe_network_list.append(o['network'])

		ip_list  = []
		mac_list = []
		op = stack.api.Call('list.host.interface', args)
		for o in op:
			# Check with Anoop
			if o['network'] in pxe_network_list:
				ip_list.append(o['ip'])
				mac_list.append(o['mac'])

		self.dictObj['ip']  = ip_list
		self.dictObj['mac'] = mac_list

		op = stack.api.Call('list.host.boot', args)
		atype = op[0]['action']

		op = stack.api.Call('list.bootaction', ['bootaction=%s' % bootaction, 'type=%s' % atype])
		self.dictObj['kernel']  = op[0]['kernel']
		self.dictObj['ramdisk'] = op[0]['ramdisk']

		self.runPlugins(self.dictObj)
