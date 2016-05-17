#!/usr/bin/env python3
import activate_venv

from veevutils import banner, safe_rename, is_slide, parse_slide
from relink import parse_folder, mv_refs

import argparse
import sys
import os

def rename_slide(old, new, root=None, relink=True):
	if root is None:
		root = os.getcwd()

	if not os.path.exists(old):
		raise IOError("%s does not exist" % old)

	if not is_slide(old):
		raise TypeError("%s is not a valid slide" % old)

	inner_file, slide_type = parse_slide(old)

	#rename folder
	safe_rename(old, new)

	#rename inner file
	inner_pieces = os.path.splitext(inner_file)
	safe_rename(inner_file, os.path.join(new,new+"."+inner_pieces[1]))

	if relink: 
		old_slide_name = os.path.basename(old)
		new_slide_name = os.path.basename(new)
		mv_refs(old_slide_name, new_slide_name, root)

def runScript():
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
		description = banner(subtitle="slide renamer"))

	parser.add_argument("old", nargs=1, help="Old slide name")
	parser.add_argument("new", nargs=1, help="New slide name")
	parser.add_argument("--norelink", action="store_true", help="rename only; don't relink references in other slides", required=False)
	parser.add_argument("--root", nargs=1, help="Project root folder", required=False)
	parser.add_argument("--verbose", action="store_true", help="Chatty Cathy", required=False)

	if len(sys.argv) == 1:
		parser.print_help()
		return 2
	else:
		ROOT = None
		args = parser.parse_args()

		if args.root is not None:
			ROOT = args.root[0]

		if args.verbose: VERBOSE = True

		old = args.old[0]
		if ROOT is not None:
			old = os.path.join(ROOT, old)

		new = args.new[0]
		if ROOT is not None:
			new = os.path.join(ROOT, new)

		rename_slide(old, new, ROOT, (not args.relink))


if __name__ == '__main__': 
	sys.exit(runScript())