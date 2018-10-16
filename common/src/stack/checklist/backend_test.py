import os
import stack.api
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

class BackendSystemTest:

	dhcp_status = ['DHCPDISCOVER', 'DHCPOFFER', 'DHCPREQUEST', 'DHCPACK']
	tftp_status = ['RRQ PXE file', 'RRQ VMLinuz', 'RRQ InitRD']

	# Time in seconds for each stage
	time_arr    = {'process_dhcp' : 60, 'process_tftp' : 120}

	def __init__(self, hostnames):

		if len(hostnames) == 1:
			self.hostname = hostnames[0]
		else:
			raise ArgRequired(self, 'hostname')

		op = stack.api.Call('list.host', hostnames)
		if len(op) == 0:
			raise CommandError(self, 'invalid hostname')
		elif len(op) > 1:
			raise ArgUnique(self, 'host')

		bootaction = op[0]['installaction']

		op = stack.api.Call('list.host.interface', hostnames)
		for o in op:
			# Check with Anoop
			if o['default']:
				self.ip  = o['ip']
				self.mac = o['mac']

		op = stack.api.Call('list.host.boot', hostnames)
		atype = op[0]['action']

		op = stack.api.Call('list.bootaction', ['bootaction=%s' % bootaction, 'type=%s' % atype])
		self.kernel  = op[0]['kernel']
		self.ramdisk = op[0]['ramdisk']

		self.dhcp_status_index = 0
		self.tftp_status_index = 0
		self.dhcp_start = 0
		self.status_arr_index = 0
		self.status_arr = [self.process_dhcp, self.process_tftp]

	@timeit	
	def process_dhcp(self, line):
		line_arr = line.split()
		daemon_name = line_arr[2]

		if 'dhcpd' not in daemon_name:
			return
		msg_type = line_arr[3]
		global dhcp_start

		if msg_type == BackendSystemTest.dhcp_status[self.dhcp_status_index]:

			if msg_type == 'DHCPDISCOVER':
				mac       = line_arr[5]
				interface = line_arr[7]

				if mac == self.mac:
					self.dhcp_status_index = self.dhcp_status_index + 1
					dhcp_start = time.time()
					print('1. DHCPDISCOVER - Received')
					return

			elif msg_type == 'DHCPOFFER':
				ip   = line_arr[5]
				mac  = line_arr[7]

				if ip == self.ip and mac == self.mac:
					self.dhcp_status_index = self.dhcp_status_index + 1
					print('2. DHCPOFFER - Received')
					return

			elif msg_type == 'DHCPREQUEST':
				ip = line_arr[5]
				mac = line_arr[8]
			
				if ip == self.ip and mac == self.mac:
					self.dhcp_status_index = self.dhcp_status_index + 1
					print('3. DHCPREQUEST - Received')
					return

			elif msg_type == 'DHCPACK':
				ip  = line_arr[5]
				mac = line_arr[7]

				if ip == self.ip and mac == self.mac:
					self.status_arr_index = self.status_arr_index + 1
					print('4. DHCPACK - Received')
					return

	@timeit
	def process_tftp(self, line):
		line_arr = line.split()
		daemon_name = line_arr[2]

		if 'tftp' not in daemon_name:
			return

		ip = line_arr[5]
		pxe_file = line_arr[7]

		if ip != self.ip:
			return
	
		if '/' in pxe_file:
			pxe_arr = pxe_file.split('/')
			hexip = pxe_arr[1]
			backend_ip_arr = self.ip.split('.')
			backend_hex_ip = '{:02X}{:02X}{:02X}{:02X}'.format(*map(int, backend_ip_arr))
		
			if backend_hex_ip == pxe_arr[1]:
				print('5. TFTP read file request - Received')
				self.tftp_status_index = self.tftp_status_index + 1
				return

		if self.tftp_status_index == 1 and pxe_file == self.kernel:
			print('6. VMLinuz read file request - Received')
			self.tftp_status_index = self.tftp_status_index + 1
			return

		if self.tftp_status_index == 2 and pxe_file == self.ramdisk:
			print('7. Initrd read file request - Received')
			self.tftp_status_index = self.tftp_status_index + 1
			self.status_arr_index = self.status_arr_index + 1
			return

	def watchLog(self):
		with open("/var/log/messages", "r") as file:
			# Seek to end of file
			file.seek(0, 2)
	
			while 1:
				where = file.tell()
				line = file.readline()
	
				if not line:
					time.sleep(1)
					file.seek(where)
				else:
					if self.status_arr_index >= len(self.status_arr):
						continue
					self.status_arr[self.status_arr_index](line)

	def dumpObject(self):
		print('Hostname %s details' % self.hostname)
		print('##############################')
		print('ip=%s' % self.ip)
		print('mac=%s' % self.mac)
		print('kernel=%s' % self.kernel)
		print('ramdisk=%s' % self.ramdisk)
		print('##############################')

def main(argv):
	b = BackendSystemTest(argv)
	b.dumpObject()

if __name__ == "__main__":
	main(sys.argv[1:])
b.watchLog()
