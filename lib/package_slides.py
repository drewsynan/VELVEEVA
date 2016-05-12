#!/usr/bin/env python3
import activate_venv

from veevutils import banner

import glob
import os
import sys
import textwrap
import zipfile
import functools
import concurrent.futures

def zip_slides_sync(root_dir, slides, dest, verbose=False):
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
	VERBOSE = False

	args = sys.argv

	if "--verbose" in args:
		VERBOSE = True
		args.remove("--verbose")

	if len(args) < 2:
		print(banner(subtitle="Slide Packager"))
		print("USAGE: ")
		print("   %s src_dir [--verbose] [dest]" % args[0])
		print("   (dest defaults to src_dir/_zips)")
		sys.exit(0)

	def okay_to_add(path):
		IGNORES = ["_zips", "_ctls"]
		return functools.reduce(lambda acc,current: acc and (current != path), IGNORES, True)

	root_dir = args[1]
	srcs = [os.path.join(root_dir,sd) for sd in next(os.walk(root_dir))[1] if okay_to_add(sd)]

	if len(srcs) < 1:
		print("No slides found!")
		sys.exit(1)

	if len(args) >= 3:
		dest = args[2]
	else:
		dest = os.path.join(args[1],"_zips")
	
	if ASYNC:
		zip_slides_async(root_dir, srcs, dest, verbose=VERBOSE)
	else:
		zip_slides_sync(root_dir, srcs, dest, verbose=VERBOSE)


if __name__ == "__main__": runScript(ASYNC=True)