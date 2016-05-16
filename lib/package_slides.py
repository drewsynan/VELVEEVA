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
	if not os.path.exists(dest): os.makedirs(dest)

	for slide in slides:
		zip_one(root_dir, slide, dest, verbose)

def zip_slides_async(root_dir, slides, dest, verbose=False):
	if not os.path.exists(dest): os.makedirs(dest)

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

	if verbose: print("Creating %s \n======================" % zip_name)

	with zipfile.ZipFile(os.path.join(dest,zip_name), 'w', zipfile.ZIP_DEFLATED) as zf:
		for root, dirs, files in os.walk(slide):
			for file in files:
				root_pieces = root_dir.split(os.sep)
				slide_pieces = root.split(os.sep)

				no_enclosing_folders = os.sep.join(slide_pieces[len(root_pieces):])
				archive_name = os.path.join(no_enclosing_folders, file)

				if verbose: print("Adding %s..." % archive_name)

				zf.write(os.path.join(root, file), archive_name)

def runScript(ASYNC=False):

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
		return
	else:
		args = parser.parse_args()
		
		VERBOSE = args.verbose
		ASYNC = (not args.notparallel)

		if args.destination is None:
			dest = os.path.join(args.source[0],"_zips")
		else:
			dest = args.destination[0]


		if args.root is not None:
			root_dir = os.path.join(args.root[0],args.source[0])
		else:
			root_dir = args.source[0]

		srcs = [os.path.join(root_dir,sd) for sd in next(os.walk(root_dir))[1] if okay_to_add(sd)]
		if len(srcs) < 1:
			print("No slides found!")
			sys.exit(1)

		if ASYNC:
			zip_slides_async(root_dir, srcs, dest, verbose=VERBOSE)
		else:
			zip_slides(root_dir, srcs, dest, verbose=VERBOSE)


if __name__ == "__main__": runScript(ASYNC=True)