#!/usr/bin/env python3
import activate_venv

from veevutils import banner

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
	args = sys.argv

	if len(args) < 3:
		print(banner(subtitle="PDF Rasterizer"))
		print("USAGE: ")
		print("   %s source_folder dest_folder" % args[0])
		return

	convertPDFs(args[1], args[2])

if __name__ == '__main__': runScript()