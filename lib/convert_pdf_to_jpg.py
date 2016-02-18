#!/usr/bin/env python3
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
		banner = textwrap.dedent('''\
			 _   ________ _   ___________   _____ 
			| | / / __/ /| | / / __/ __| | / / _ |
			| |/ / _// /_| |/ / _// _/ | |/ / __ |
			|___/___/____|___/___/___/ |___/_/ |_|
			                                      
			~~~~~~~~~~~ PDF Rasterizer ~~~~~~~~~~~
			''')
		print(banner)
		print("USAGE: ")
		print("   %s source_folder dest_folder" % args[0])
		return

	convertPDFs(args[1], args[2])

if __name__ == '__main__': runScript()