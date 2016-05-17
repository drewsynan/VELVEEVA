#!/usr/bin/env python3
import activate_venv

from veevutils import banner

import argparse
import os
import sys
import glob
import subprocess
import textwrap

def convertPDFs(source, dest, density=72):
	if not os.path.exists(source): raise IOError("Source folder does not exist!")
	if not os.path.exists(dest): os.mkdir(dest)

	files = glob.glob(os.path.join(source, "*.pdf"))

	for file in files:
		bare_name = os.path.splitext(os.path.basename(file))[0]
		print("Converting %s" % file)
		subprocess.call([
			"convert", 
			"-density", str(density),
			"-flatten",
			"-quality", "90%", 
			file, 
			os.path.join(dest, bare_name + ".jpg")])

def runScript():
	parser = argparse.ArgumentParser(
		formatter_class=argparse.RawDescriptionHelpFormatter,
		description=banner(subtitle="PDF Rasterizer"))

	parser.add_argument("source", nargs=1, help="Source folder")
	parser.add_argument("destination", nargs=1, help="Destination folder")
	parser.add_argument("--root", nargs=1, help="Project root directory")
	parser.add_argument("--verbose", action="store_true", help="Chatty Cathy")

	if len(sys.argv) == 1:
		parser.print_help()
		return
	else:
		args = parser.parse_args()
		convertPDFs(args.source[0], args.destination[0])

if __name__ == '__main__': runScript()