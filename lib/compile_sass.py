#!/usr/bin/env python3
import activate_venv
from veevutils import banner

import argparse
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
	parser = argparse.ArgumentParser(
		formatter_class=argparse.RawDescriptionHelpFormatter,
		description=banner(subtitle="SASS Compiler"))

	parser.add_argument("source", nargs=1, help="Source folder")
	parser.add_argument("--remove", action="store_true", help="Remove .scss source files after compilation")
	parser.add_argument("--root", nargs=1, help="Root project folder")
	parser.add_argument("--sync", action="store_true", help="Run without concurrency")
	parser.add_argument("--verbose", action="store_true", help="Chatty Cathy")


	if len(sys.argv) == 1:
		parser.print_help()
		return
	else:
		args = parser.parse_args()
		compileSass(args.source[0], remove_source=args.remove, async=(not args.sync))

if __name__ == '__main__': runScript(ASYNC=True)