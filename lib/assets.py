#!/usr/bin/env python3
from __future__ import print_function
import activate_venv
from veevutils import banner

import argparse
import fnmatch
import os
import shutil
import sys
import textwrap
import concurrent.futures

def inject1(root_dir, src_dir, dest_dir, merge=True, filter="*", verbose=False):
	s_walk = os.walk(os.path.abspath(os.path.join(root_dir,src_dir)))

	for root, dirs, files in s_walk:

		# get the current directory relative to the root
		split_root = os.path.abspath(root_dir).split(os.sep)
		split_global = os.path.abspath(root).split(os.sep)


		stripped_path = root.split(os.sep)[len(split_root)+1:]
		if len(stripped_path) > 1:
			inner_dir = os.path.join(root_dir,dest_dir,os.sep.join(stripped_path))
		else:
			inner_dir= os.path.join(root_dir,dest_dir,''.join(stripped_path))
			
		# check to see if the enclosing directory exists
		if not os.path.exists(os.path.join(dest_dir,inner_dir)):
			if verbose: print("Creating %s" % inner_dir)
			os.mkdir(os.path.join(dest_dir,inner_dir))

		# copy files
		for file in files:
			if fnmatch.fnmatch(file, filter) and not fnmatch.fnmatch(file, "index.htm*"):
				compiled_src = os.path.join(root,file)
				compiled_dest = os.path.join(dest_dir,inner_dir,file)
				
				if verbose: print("Copying %s to %s" % (compiled_src, compiled_dest))
				
				shutil.copy2(compiled_src,compiled_dest)

def inject(root, srcs, dests, verbose=False):
	if not type(srcs) == list:
		srcs = [srcs]

	if not type(dests) == list:
		dests = [dests]

	for dest in dests:
		for src in srcs:
			if verbose: print("Injecting %s to %s" % (src,dest))
			inject1(root, src, dest, verbose=verbose)

def inject_async(root, srcs, dests, verbose=False):
	if not type(srcs) == list: srcs = [srcs]
	if not type(dests) == list: dests = [dests]

	with concurrent.futures.ProcessPoolExecutor() as executor:
		futures = {}
		for dest in dests:
			for src in srcs:
				futures[executor.submit(inject1, root, src, dest, verbose=verbose)] = src+dest
		for future in concurrent.futures.as_completed(futures):
			try:
				data = future.result()
			except Exception as e:
				raise e

def runScript(ASYNC=False):

	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
		description = banner(subtitle="Asset Inliner"))

	parser.add_argument("source", help="Source folder")
	parser.add_argument("destination", help="Destination folder")
	parser.add_argument("--inject-root-only", action="store_true", 
		help="Only inject files in the root of the destination (don't look for slide folders)")
	parser.add_argument("--notparallel", action="store_true", help="Run without concurrency")
	parser.add_argument("--root", nargs=1, help="Project root directory (current directory is used if nont is specified")
	parser.add_argument("--use-shared", action="store_true", 
		help="Use Veeva's shared asset feature")
	parser.add_argument("--verbose", action="store_true", help="Chatty Cathy")

	if len(sys.argv) == 1:
		parser.print_help()
		return 2
	else:
		args = parser.parse_args()

		VERBOSE = args.verbose
		ROOT_ONLY = args.inject_root_only
		VEEVA_SHARED = args.use_shared
		ASYNC = (not args.notparallel)

		if args.root is None:
			root = os.getcwd()
		else:
			root = args.root[0]

		src = args.source ### arg! positional arguments don't return lists... oops!
		dest = args.destination ### ^ saem
		

		if not os.path.exists(os.path.join(root,src)):
			print(os.path.join(root,src))
			print("Source does not exist!")
			sys.exit(1)

		if not os.path.exists(os.path.join(root,dest)):
			os.makedirs(os.path.join(root,dest))

		if ROOT_ONLY or VEEVA_SHARED:
			# dump files into the root, or shared assets subfolder
			inject(root, src, dest, verbose=VERBOSE)
		else:
			subdirs = [os.path.join(dest,sd) for sd in next(os.walk(os.path.join(root,dest)))[1]]
			if ASYNC:
				inject_async(root, src, subdirs, verbose=VERBOSE)
			else:
				inject(root, src, subdirs, verbose=VERBOSE)

if __name__ == '__main__':
	sys.exit(runScript())


