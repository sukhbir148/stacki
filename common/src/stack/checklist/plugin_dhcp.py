# @copyright@
# Copyright (c) 2006 - 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@
import stack.commands
import time

class Plugin(stack.commands.Plugin):

	dhcp_status = ['DHCPDISCOVER', 'DHCPOFFER', 'DHCPREQUEST', 'DHCPACK']

	def provides(self):
		return 'dhcp'

	def precedes(self):
		return ['tftp']

	def process_dhcp(self, line, backendObj):
		line_arr = line.split()
		daemon_name = line_arr[2]

		if 'dhcpd' not in daemon_name:
			return

		msg_type = line_arr[3]

		if msg_type == Plugin.dhcp_status[self.dhcp_status_index]:

			if msg_type == 'DHCPDISCOVER':
				mac = line_arr[5]
				interface = line_arr[7]

				if mac == backendObj['mac']:
					self.dhcp_status_index = self.dhcp_status_index + 1
					dhcp_start = time.time()
					print('1. DHCPDISCOVER - Received')
					return

			elif msg_type == 'DHCPOFFER':
				ip   = line_arr[5]
				mac  = line_arr[7]

				if ip == backendObj['ip'] and mac == backendObj['mac']:
					self.dhcp_status_index = self.dhcp_status_index + 1
					print('2. DHCPOFFER - Received')
					return

			elif msg_type == 'DHCPREQUEST':
				ip = line_arr[5]
				mac = line_arr[8]

				if ip == backendObj['ip'] and mac == backendObj['mac']:
					self.dhcp_status_index = self.dhcp_status_index + 1
					print('3. DHCPREQUEST - Received')
					return

			elif msg_type == 'DHCPACK':
				ip  = line_arr[5]
				mac = line_arr[7]

				if ip == backendObj['ip'] and mac == backendObj['mac']:
					self.dhcp_status_index = self.dhcp_status_index + 1
					print('4. DHCPACK - Received')
					return

	def run(self, backendObj):
		self.dhcp_status_index = 0
		self.dhcp_start = 0

		with open("/var/log/messages", "r") as file:
			file.seek(0, 2)

			while 1:
				where = file.tell()
				line  = file.readline()

				if not line:
					time.sleep(1)
					file.seek(where)
				else:
					self.process_dhcp(line, backendObj)

				if self.dhcp_status_index == len(Plugin.dhcp_status):
					break
