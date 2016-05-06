#!/usr/bin/env python3
import activate_venv

import glob
import os
import sys
import textwrap
import fnmatch


def runScript():
	args = sys.argv

	if len(args) < 2:
		banner = textwrap.dedent('''\
			 _   ________ _   ___________   _____ 
			| | / / __/ /| | / / __/ __| | / / _ |
			| |/ / _// /_| |/ / _// _/ | |/ / __ |
			|___/___/____|___/___/___/ |___/_/ |_|
			                                      
			~~~~~~~~~~ Template Renderer ~~~~~~~~~
			''')
		print(banner)
		print("USAGE: ")
		print("   %s source_folder [partials_dir]" % args[0])
		sys.exit(0)


if __name__ == '__main__': runScript()