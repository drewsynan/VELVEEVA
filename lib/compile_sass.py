#!/usr/bin/env python3
import activate_venv

import glob
import os
import sys
import textwrap
import fnmatch

from sassutils import builder

def compileSass(dir, remove_source=False):
	builder.build_directory(dir, dir)
	compiled = glob.glob(os.path.join(dir,"*.scss.css"))
	for file in compiled:
		scss_name = os.path.splitext(file)[0]
		no_ext = os.path.splitext(scss_name)[0]
		renamed = no_ext + ".css"

		os.rename(file, renamed)

	if remove_source:
		for root, dirs, files in os.walk(dir):
			for file in files:
				if fnmatch.fnmatch(file, "*.scss"):
					os.remove(os.path.join(root,file))




def runScript():
	args = sys.argv

	if len(args) < 2:
		banner = textwrap.dedent('''\
			 _   ________ _   ___________   _____ 
			| | / / __/ /| | / / __/ __| | / / _ |
			| |/ / _// /_| |/ / _// _/ | |/ / __ |
			|___/___/____|___/___/___/ |___/_/ |_|
			                                      
			~~~~~~~~~~~~ SASS Compiler ~~~~~~~~~~~
			''')
		print(banner)
		print("USAGE: ")
		print("   %s source_folder" % args[0])
		sys.exit(0)

	compileSass(args[1], remove_source=False)

if __name__ == '__main__': runScript()