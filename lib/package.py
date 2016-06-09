#!/usr/bin/env python3
import activate_venv

from veevutils import banner

import argparse
import glob
import os
import sys
import textwrap
import zipfile
import functools
import concurrent.futures

def zip_slides(root_dir, slides, dest, verbose=False):
	if not os.path.exists(os.path.join(root_dir,dest)): os.makedirs(os.path.join(root_dir,dest))

	for slide in slides:
		zip_one(root_dir, slide, dest, verbose)

def zip_slides_async(root_dir, slides, dest, verbose=False):

	if not os.path.exists(os.path.join(root_dir,dest)): os.makedirs(os.path.join(root_dir,dest))

	with concurrent.futures.ProcessPoolExecutor() as executor:
		futures = {executor.submit(zip_one, root_dir, slide, dest, verbose): slide for slide in slides}

		for future in concurrent.futures.as_completed(futures):
			try:
				data = future.result()
			except Exception as e:
				raise e

def zip_one(root_dir, slide, dest, verbose=False):
	slide_name = os.path.basename(slide)
	zip_name = slide_name + ".zip"
	zip_path = os.path.join(root_dir,dest,zip_name)

	if verbose: print("Creating %s \n======================" % zip_name)

	with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
		for root, dirs, files in os.walk(os.path.join(root_dir,slide)):
			for file in files:
				root_pieces = os.path.join(root_dir, dest).split(os.sep)
				slide_pieces = root.split(os.sep)

				no_enclosing_folders = os.sep.join(slide_pieces[len(root_pieces)-1:])
				archive_name = os.path.join(no_enclosing_folders, file)

				if verbose: print("Adding %s..." % archive_name)

				zf.write(os.path.join(root, file), archive_name)

def runScript(ASYNC=False):

	# should use is_slide() to check that a folder is actually a slide folder
	def okay_to_add(path):
		IGNORES = ["_zips", "_ctls"]
		return functools.reduce(lambda acc,current: acc and (current != path), IGNORES, True)

	parser = argparse.ArgumentParser(
		formatter_class=argparse.RawDescriptionHelpFormatter,
		description = banner(subtitle="Slide Packager"))

	parser.add_argument("source", nargs=1, help="Source folder")
	parser.add_argument("destination", nargs='?', help="Destination folder (if none is specified, defaults to source/_zips)")
	parser.add_argument("--root", nargs=1, help="Project root directiory", required=False)
	parser.add_argument("--verbose", action="store_true", help="Chatty Cathy", required=False)
	parser.add_argument("--notparallel", action="store_true", help="Run without concurrency", required=False)
	
	if len(sys.argv) == 1:
		parser.print_help()
		return 2
	else:
		args = parser.parse_args()
		
		VERBOSE = args.verbose
		ASYNC = (not args.notparallel)

		SOURCE = args.source[0]

		if args.destination is None:
			dest = os.path.join(SOURCE,"_zips")
		else:
			dest = args.destination #?? oh god this isn't a list!


		if args.root is None:
			root_dir = os.getcwd()
		else:
			root_dir = args.root[0]

		DEST = dest
		ROOT = root_dir

		SOURCE_PATH = os.path.abspath(os.path.join(ROOT,SOURCE))

		srcs = [os.path.join(SOURCE,sd) for sd in next(os.walk(SOURCE_PATH))[1] if okay_to_add(sd)]

		if len(srcs) < 1:
			print("No slides found!")
			sys.exit(1)

		if ASYNC:
			zip_slides_async(root_dir, srcs, dest, verbose=VERBOSE)
		else:
			zip_slides(root_dir, srcs, dest, verbose=VERBOSE)


if __name__ == "__main__": 
	sys.exit(runScript(ASYNC=True))