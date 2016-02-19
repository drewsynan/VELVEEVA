#!/usr/bin/env python3
import activate_venv

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
	args = sys.argv

	if len(args) < 2:
		banner = textwrap.dedent('''\
			 _   ________ _   ___________   _____ 
			| | / / __/ /| | / / __/ __| | / / _ |
			| |/ / _// /_| |/ / _// _/ | |/ / __ |
			|___/___/____|___/___/___/ |___/_/ |_|
			                                      
			~~~~~~~~~~ FOLDER GENERATOR ~~~~~~~~~~
			''')
		print(banner)
		print("USAGE: ")
		print("   %s path [\"glob-filter\"]" % args[0])
		return

	filter = "*"
	path = os.path.realpath(args[1])
	if len(args) >= 3: filter = args[2]
	
	stripSpaces(path)
	createEnclosingFolders(path, filter)


if __name__ == "__main__": runScript()