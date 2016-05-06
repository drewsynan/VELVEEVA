#!/usr/bin/env python3
from __future__ import print_function
import activate_venv

import fnmatch
import os
import shutil
import sys
import textwrap

def inject1(src_dir, dest_dir, merge=True, filter="*", verbose=False):
	s_walk = os.walk(src_dir)

	for root, dirs, files in s_walk:
		stripped_path = root.split(os.sep)[1:]
		if len(stripped_path) > 1:
			inner_dir = os.path.join(*stripped_path)
		else:
			inner_dir= ''.join(stripped_path)

		# check to see if the enclosing directory exists
		if not os.path.exists(os.path.join(dest_dir,inner_dir)):
			if verbose: print("Creating %s" % inner_dir)
			os.mkdir(os.path.join(dest_dir,inner_dir))

		# copy files
		for file in files:
			if fnmatch.fnmatch(file, filter):
				compiled_src = os.path.join(root,file)
				compiled_dest = os.path.join(dest_dir,inner_dir,file)
				
				if verbose: print("Copying %s to %s" % (compiled_src, compiled_dest))
				
				shutil.copy2(compiled_src,compiled_dest)

def inject(srcs, dests, verbose=False):
	if not type(srcs) == list:
		srcs = [srcs]

	if not type(dests) == list:
		dests = [dests]

	for dest in dests:
		for src in srcs:
			if verbose: print("Injecting %s to %s" % (src,dest))
			inject1(src, dest, verbose=verbose)

def runScript():
	VERBOSE = False
	ROOT_ONLY = False

	args = sys.argv

	if "--verbose" in args:
		VERBOSE = True
		args.remove("--verbose")
	
	if "--root-only" in args:
		ROOT_ONLY = True
		args.remove("--root-only")

	if len(args) < 2:
		banner = textwrap.dedent('''\
			 _   ________ _   ___________   _____ 
			| | / / __/ /| | / / __/ __| | / / _ |
			| |/ / _// /_| |/ / _// _/ | |/ / __ |
			|___/___/____|___/___/___/ |___/_/ |_|
			                                      
			~~~~~~~~~~~ Asset Injector ~~~~~~~~~~~
			''')
		print(banner)
		print("USAGE: ")
		print("      %s source dest [--root-only] [--verbose]" % args[0])
		sys.exit(0)

	src = args[1]
	dest = args[2]

	if not os.path.exists(src):
		print("Source does not exist!")
		sys.exit(1)

	if not os.path.exists(dest):
		os.mkdirs(dest)

	if ROOT_ONLY:
		inject(src, dest, verbose=VERBOSE)
	else:
		subdirs = [os.path.join(dest, sd) for sd in next(os.walk(dest))[1]]
		inject(src, subdirs, verbose=VERBOSE)

if __name__ == '__main__':
	runScript()


