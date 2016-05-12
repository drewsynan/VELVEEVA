#!/usr/bin/env python3
import activate_venv

import glob
import os
import sys
import textwrap
import fnmatch
import concurrent.futures

from sassutils import builder

def rename_one(file):
	scss_name = os.path.splitext(file)[0]
	no_ext = os.path.splitext(scss_name)[0]
	renamed = no_ext + ".css"

	os.rename(file, renamed)

def compileSass(dir, remove_source=False, async=False):
	builder.build_directory(dir, dir)
	#compiled = glob.glob(os.path.join(dir,"*.scss.css"))
	compiled = []
	w = os.walk(dir)
	for root, dirs, files in w:
		for file in files:
			if fnmatch.fnmatch(file, "*.scss.css"):
				compiled.append(os.path.join(root,file))

	if async:
		with concurrent.futures.ProcessPoolExecutor() as e:
			for file in compiled:
				e.submit(rename_one, file)
	else:
		for file in compiled:
			rename_one(file)

	if remove_source:
		for root, dirs, files in os.walk(dir):
			for file in files:
				if fnmatch.fnmatch(file, "*.scss"):
					os.remove(os.path.join(root,file))

def runScript(ASYNC=False):
	REMOVE = False
	args = sys.argv

	if "--remove" in args:
		args.remove("--remove")

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

	compileSass(args[1], remove_source=REMOVE, async=ASYNC)

if __name__ == '__main__': runScript(ASYNC=True)