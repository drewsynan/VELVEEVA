#!/usr/bin/env python3
import activate_venv

import glob
import os
import sys
import textwrap
import zipfile

def zip_slides(slides, dest, verbose=False):
	if not os.path.exists(dest): os.makedirs(dest)

	for slide in slides:
		slide_name = os.path.basename(slide)
		zip_name = slide_name + ".zip"

		if verbose: print("Creating %s \n======================" % zip_name)

		with zipfile.ZipFile(os.path.join(dest,zip_name), 'w', zipfile.ZIP_DEFLATED) as zf:
			for root, dirs, files in os.walk(slide):
				for file in files:
					if verbose: print("Adding %s..." % file)
					no_enclosing_folder = os.sep.join(root.split(os.sep)[1:])
					archive_name = os.path.join(os.sep.join(root.split(os.sep)[1:]), file)

					zf.write(os.path.join(root, file), archive_name)


def runScript():
	VERBOSE = False

	args = sys.argv

	if "--verbose" in args:
		VERBOSE = True
		args.remove("--verbose")

	if len(args) < 2:
		banner = textwrap.dedent('''\
			 _   ________ _   ___________   _____ 
			| | / / __/ /| | / / __/ __| | / / _ |
			| |/ / _// /_| |/ / _// _/ | |/ / __ |
			|___/___/____|___/___/___/ |___/_/ |_|
			                                      
			~~~~~~~~~~~ SLIDE PACKAGER ~~~~~~~~~~~
			''')
		print(banner)
		print("USAGE: ")
		print("   %s src_dir [--verbose] [dest]" % args[0])
		print("   (dest defaults to src_dir/_zips)")
		sys.exit(0)

	src = args[1]
	src = [os.path.join(src,sd) for sd in next(os.walk(args[1]))[1] if sd != "_zips"]

	if len(src) < 1:
		print("No slides found!")
		sys.exit(1)

	if len(args) >= 3:
		dest = args[2]
	else:
		dest = os.path.join(args[1],"_zips")
	
	zip_slides(src, dest, verbose=VERBOSE)


if __name__ == "__main__": runScript()