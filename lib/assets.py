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
	root_dir = os.path.relpath(root_dir)
	src_dir = os.path.relpath(src_dir)
	dest_dir = os.path.relpath(dest_dir)

	abs_src_path = os.path.abspath(os.path.join(root_dir,src_dir))
	abs_dest_path = os.path.abspath(os.path.join(root_dir,dest_dir))


	s_walk = os.walk(abs_src_path)

	for current_dir_path, dirs, files in s_walk:

		#get current parent dir relative to the src directory
		relative_current_folder = os.path.relpath(os.path.abspath(current_dir_path), abs_src_path)

		# see if the relative directory exists inside of the destination
		dest_folder = os.path.join(abs_dest_path, relative_current_folder)
		if not os.path.exists(dest_folder):
			if verbose: print("Creating %s" % dest_folder)
			os.mkdir(dest_folder)

		# copy each source file
		for file in files:
			if fnmatch.fnmatch(file, filter) and not fnmatch.fnmatch(file, "index.htm*"):
				src_path = os.path.join(current_dir_path, file)
				dest_path = os.path.join(abs_dest_path, relative_current_folder, file)

				if verbose: print("Copying %s to %s" % (src_path, dest_path))

				shutil.copy2(src_path, dest_path)

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
			if ASYNC:
					inject_async(root, src, dest, verbose=VERBOSE)
			else:
				inject(root, src, dest, verbose=VERBOSE)
		else:
			subdirs = [os.path.join(dest,sd) for sd in next(os.walk(os.path.join(root,dest)))[1]]
			if ASYNC:
				inject_async(root, src, subdirs, verbose=VERBOSE)
			else:
				inject(root, src, subdirs, verbose=VERBOSE)

if __name__ == '__main__':
	sys.exit(runScript())


