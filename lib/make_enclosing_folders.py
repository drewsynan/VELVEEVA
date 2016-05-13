#!/usr/bin/env python3
import activate_venv

from veevutils import banner

import argparse
import glob
import os
import sys
import shutil
import textwrap

def createEnclosingFolders(path, filter="*"):
	files = glob.glob(os.path.join(path,filter))

	for file in files:
		if os.path.isfile(file):
			bare_name = os.path.splitext(os.path.basename(file))[0]
			src = file
			dest = os.path.join(path, bare_name, os.path.basename(file))

			try:
				os.mkdir(os.path.join(path, bare_name))
			except FileExistsError:
				pass

			shutil.move(src, dest)

def stripSpaces(path, filter="*"):
	matches = glob.glob(os.path.join(path, filter))

	for match in matches:
		if os.path.isfile(match):
			clean_name = match.replace(" ", "-")
			if not clean_name == match:
				os.rename(os.path.join(path, match), os.path.join(path, clean_name))


def runScript():
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
		description = banner(subtitle="Folder Generator"))

	parser.add_argument("source", nargs=1, help="Source folder")
	parser.add_argument("--filter", metavar="\"filter\"", nargs=1, help="Glob filter in quotes e.g.: \"*_slide\"")
	parser.add_argument("--no-strip", action="store_true", help="Do not substitute spaces with '-'s in folder names")
	parser.add_argument("--root", nargs=1, help="Project root folder")
	parser.add_argument("--verbose", action="store_true", help="Chatty Cathy")

	if len(sys.argv) == 1:
		parser.print_help()
		return
	else:
		args = parser.parse_args()

		if args.filter is None:
			filter = "*"
		else:
			filter = args.filter[0]

		if not args.no_strip:
			stripSpaces(args.source[0])

		createEnclosingFolders(args.source[0], filter)

if __name__ == "__main__": runScript()