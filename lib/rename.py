#!/usr/bin/env python3
import activate_venv

from veevutils import banner, safe_rename, is_slide, parse_slide
from relink import parse_folder, mv_refs

import argparse
import sys
import os

def rename_slide(old, new, root=None, relink=True, verbose=False):
	THUMB_NAME = "-thumb.jpg"
	FULL_NAME = "-full.jpg"

	if root is None:
		root = '.' # current directory

	if not os.path.exists(old):
		raise IOError("%s does not exist" % old)

	if not is_slide(old):
		raise TypeError("%s is not a valid slide" % old)

	
	old_slide_name = os.path.basename(old)
	new_slide_name = os.path.basename(new)

	inner_file, slide_type = parse_slide(old)

	#relink first so we don't have to worry about adjusting file paths
	if relink:
		renamer = mv_refs(old_slide_name, new_slide_name)
		parse_folder(root, actions=[renamer], verbose=verbose)


	#rename inner file
	inner_pieces = os.path.splitext(inner_file)
	new_inner_file = os.path.join(old,new_slide_name+inner_pieces[1])
	safe_rename(inner_file, new_inner_file)

	#rename -thumb.jpg if it exists
	old_thumb = os.path.join(old,old_slide_name+THUMB_NAME)
	new_thumb = os.path.join(old,new_slide_name+THUMB_NAME)
	if os.path.exists(old_thumb): safe_rename(old_thumb,new_thumb)

	#rename -full.jpg if it exists
	old_full = os.path.join(old,old_slide_name+FULL_NAME)
	new_full = os.path.join(old,new_slide_name+FULL_NAME)
	if os.path.exists(old_full): safe_rename(old_full,new_full)

	#rename outer parent folder
	safe_rename(old, new)


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
	
	ROOT = None
	args = parser.parse_args()

	if args.root is not None: ROOT = args.root[0]

	old = args.old[0]
	if ROOT is not None: old = os.path.join(ROOT, old)

	new = args.new[0]
	if ROOT is not None: new = os.path.join(ROOT, new)

	if not os.path.exists(old): raise IOError("%s does not exist" % old)
	if os.path.exists(new): raise IOError("%s already exists" % new)

	rename_slide(old, new, root=ROOT, relink=(not args.norelink), verbose=args.verbose)


if __name__ == '__main__': 
	sys.exit(runScript())