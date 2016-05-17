#!/usr/bin/env python3
import activate_venv

from veevutils import banner, is_slide, safe_rename
from functools import reduce
from relink import parse_folder, mv_refs

import argparse
import os
import sys
import argparse
import textwrap
import re
import subprocess

def find_slides(path, cutoff = 1):
	slides = set([])

	for root, dirnames, filenames in os.walk(path):
		if root.count(os.sep) <= cutoff:
			for filename in filenames:
				parent_path, parent_name = os.path.split(root)
				if is_slide(filename): slides.add(parent_name)

	return list(slides)


def parse_slide_folders(path):
	# filter all file paths for only folders that contain a file with the same name directly inside
	filepaths = []
	dirs = set([])
	base_depth = path.count(os.sep)

	CUTOFF = 1 # only go one directory deep

	for root, dirnames, filenames in os.walk(path):
		if root.count(os.sep) - base_depth <= CUTOFF:
			for filename in filenames:
				parent_path, parent_name = os.path.split(root)

				if is_slide(filename):
					filepaths.append((root, filename))
					dirs.add(root)

	return filepaths, list(dirs)

def prefix_folder(prefix, path):
	filepaths, parentdirs = parse_slide_folders(path)

	if len(filepaths) == 0:
		print("No slides found!")
		return

	for filepath in filepaths:
		parent_folder = filepath[0]
		filename = filepath[1]

		old_file = os.path.join(parent_folder, filename)
		new_filename = prefix + filename
		new_file = os.path.join(parent_folder, new_filename)
		print("Renaming slide %s to %s" % (old_file, new_file))
		sys.stdout.flush()

		safe_rename(old_file, new_file)

	for parentdir in parentdirs:
		parent_pieces = os.path.split(parentdir)
		new_folder = os.path.join(parent_pieces[0], prefix + parent_pieces[1])
		print("Renaming container %s to %s" % (parentdir, new_folder))
		sys.stdout.flush()

		safe_rename(parentdir, new_folder)

def prefix_refs(prefix, slidelist, root):
	for slide in slidelist:
		print("Changing all references to slide %s" % slide)
		sys.stdout.flush()

		parse_folder(rmv_refsctions=[mv_refs(slide, prefix + slide)], cutoff=1)

def runScript():
	## TODO make work with --root flag
	def doesFileExist(fname):
		exists = os.path.exists(fname)
		if not exists: print("%s does not exist!" % fname)
		return exists

	def allExists(folders):
		return reduce(lambda acc, arg: acc and doesFileExist(arg), folders, True)

	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
		description = banner(subtitle="(PRE)-fixer")

	parser.add_argument("prefix", nargs=1, help="prefix string")
	parser.add_argument("source", nargs="+", help="folder(s) to process")
	parser.add_argument("--root", nargs=1, help="Project root folder", required=False)
	parser.add_argument("--verbose", action="store_true", required=False)

	if len(sys.argv) == 1:
		parser.print_help()
		return
	else:
		args = parser.parse_args()

		the_prefix = args.prefix[0]
		folders = args.source
		if not allExists(folders):
			return

		for folder in folders:
			prefix_refs(the_prefix, find_slides(folder), folder)
			prefix_folder(the_prefix, folder)

if __name__ == "__main__":
	runScript()
