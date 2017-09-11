# @SI_Copyright@
# Copyright (c) 2006 - 2017 StackIQ Inc.
# All rights reserved. stacki(r) v4.0 stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @SI_Copyright@
#
# @Copyright@
# Copyright (c) 2000 - 2010 The Regents of the University of California
# All rights reserved. Rocks(r) v5.4 www.rocksclusters.org
# https://github.com/Teradata/stacki/blob/master/LICENSE-ROCKS.txt
# @Copyright@


import string
import stack.commands
from stack.exception import *

class command(stack.commands.Command):
	MustBeRoot = 0

	safe_chars = [
		'@', '%', '^', '-', '_', '=', '+', 
		':', 
		',', '.', '/'
		]
		
	def quote(self, string):
		s = ''

		if string != None:
			for c in string:
				if c.isalnum() or c in self.safe_chars:
					s += c
				else:
					s += '\\%s' % c
		return s

	def dump(self, line):
		self.addText('/opt/stack/bin/stack %s\n' % line)
#		self.addText('./stack.py %s\n' % line)

	
class Command(command):
	"""
	The top level dump command is used to recursively call all the
	dump commands in the correct order.  This is used to create the 
	restore roll.

	<example cmd='dump'>
	Recursively call all dump commands.
	</example>
	"""
	
	def run(self, params, args):
		if len(args):
			raise CommandError(self, 'command does not take arguments')
		self.addText("#!/bin/bash\n\n")
		self.runPlugins()
		self.dump("sync config")
		self.dump("sync host config")
