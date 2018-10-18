# @copyright@
# Copyright (c) 2006 - 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@
import stack.commands
import time

class Plugin(stack.commands.Plugin):

	tftp_status = ['RRQ PXE file', 'RRQ VMLinuz', 'RRQ InitRD']

	def provides(self):
		return 'tftp'

	def requires(self):
		return ['dhcp']

	def process_tftp(self, line, backendObj):
		line_arr = line.split()
		daemon_name = line_arr[2]

		if 'tftp' not in daemon_name:
			return

		ip = line_arr[5]
		pxe_file = line_arr[7]

		if ip != backendObj['ip']:
			return

		if '/' in pxe_file:
			pxe_arr = pxe_file.split('/')
			hexip = pxe_arr[1]
			backend_ip_arr = backendObj['ip'].split('.')
			backend_hex_ip = '{:02X}{:02X}{:02X}{:02X}'.format(*map(int, backend_ip_arr))

			if backend_hex_ip == pxe_arr[1]:
				print('5. TFTP read file request - Received')
				self.tftp_status_index = self.tftp_status_index + 1
				return

		if self.tftp_status_index == 1 and pxe_file == backendObj['kernel']:
			print('6. VMLinuz read file request - Received')
			self.tftp_status_index = self.tftp_status_index + 1
			return

		if self.tftp_status_index == 2 and pxe_file == backendObj['ramdisk']:
			print('7. Initrd read file request - Received')
			self.tftp_status_index = self.tftp_status_index + 1
			return

	def run(self, backendObj):
		self.tftp_status_index = 0

		with open("/var/log/messages", "r") as file:
			file.seek(0, 2)

			while 1:
				where = file.tell()
				line  = file.readline()

				if not line:
					time.sleep(1)
					file.seek(where)
				else:
					self.process_tftp(line, backendObj)

				if self.tftp_status_index == len(Plugin.tftp_status):
					break
