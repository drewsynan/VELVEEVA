#!/usr/bin/env python3
import activate_venv
from veevutils import banner

from bs4 import BeautifulSoup # also requires lxml
from functools import reduce
from pymonad import *
from urllib.parse import urlparse

import argparse
import fnmatch
import os
import re
import sys
import textwrap

@curry
def action(name, selector, action, source):

	@State
	def closure(old_state):
		b = BeautifulSoup(source, "lxml")
		transformer_(b, selector, action)
		
		return (b.prettify(), old_state + 1)
	return closure

def transformer_(soup, selector, transform):
	items = selector(soup)
	transform(items, soup)

def attribute_transform(attribute, transform):
	def transformed(items, soup):
		if items == []: return

		for item in items:
			item[attribute] = transform(item[attribute])
	return transformed

def add_meta(**kwargs):
	def transformed(items, soup):
		nonlocal kwargs

		if soup.html is None: return #empty dom

		if items == []:
			meta = soup.new_tag("meta")
			for key in kwargs:
				meta.attrs[key] = kwargs[key]
			
			if soup.head is None: soup.html.append(soup.new_tag("head"))
			
			soup.head.append(meta)

	return transformed

def fix_relative_path(path):
	return re.sub("(\.\.\/)*", "", path)

def fix_hyperlink_protocol(href):
	if urlparse(href).netloc != '': return href
	
	match = re.search("(?P<slide_name>[^/]+)\/(?P=slide_name)\.htm(l)?", href)
	if match is None:
		return href
	else:
		slide_name = match.group(1)
		return "veeva:gotoSlide(%s.zip)" % slide_name

def fix_veev_2_rel(href):
	match = re.search("veeva:gotoSlide\((.+)\.zip\)", href)
	if match is None:
		return href
	else:
		return "../" + match.group(1) + "/" + match.group(1) + ".html"

def fix_rel_2_veev(href):
	return fix_hyperlink_protocol(fix_relative_path(href))

@curry
def mv_rel(old_slide_name, new_slide_name, href):
	if urlparse(href).netloc == '':
		oldSlide = re.compile("((?:[^/]*\/)*)(?P<slide_name>" + old_slide_name + ")\/(?P=slide_name)(\.htm(?:l)?)")
		return oldSlide.sub(r"\g<1>" + new_slide_name + "/" + new_slide_name + r"\g<3>", href)
	else:
		return href

@curry
def mv_veev(old_slide_name, new_slide_name, href):
	oldSlide = re.compile("veeva:([^(]+)\(" + old_slide_name + ".zip\)")
	return oldSlide.sub(r"veeva:\g<1>" + "(" + new_slide_name + ".zip)", href)

def run_actions(actions, src):
	return reduce(lambda prev, new: prev >> new, actions, unit(State, src)).getResult(-1)

def integrate_all(src):
	actions = [
		action(
			"stylesheets",
			lambda soup: soup.find_all("link", {"rel": "stylesheet"}),
			attribute_transform("href", fix_relative_path)),
		action(
			"scripts",
			lambda soup: soup.find_all("script", src=True),
			attribute_transform("src", fix_relative_path)),
		action(
			"images",
			lambda soup: soup.find_all("img"),
			attribute_transform("src", fix_relative_path)),
		action(
			"iframes",
			lambda soup: soup.find_all("iframe"),
			attribute_transform("src", fix_relative_path)),
		action(
			"hyperlink_paths",
			lambda soup: soup.find_all("a", href=True),
			attribute_transform("href", fix_relative_path)),
		action(
			"hyperlink_protocols",
			lambda soup: soup.find_all("a", href=True),
			attribute_transform("href", fix_hyperlink_protocol)),
		action(
			"utf",
			lambda soup: soup.find_all("meta", charset=True),
			add_meta(charset="utf-8"))
	]

	return run_actions(actions, src)

def veev2rel(src):
	actions = [
		action(
			"veeva to relative",
			lambda soup: soup.find_all("a", href=True),
			attribute_transform("href", fix_veev_2_rel))
	]
	return run_actions(actions, src)

def rel2veev(src):
	actions = [
		action(
			"relative to veeva",
			lambda soup: soup.find_all("a", href=True),
			attribute_transform("href", fix_rel_2_veev))
	]
	return run_actions(actions, src)

@curry
def mv_refs(old_slide_name, new_slide_name, src):
	actions = [
		action(
			"old rel to old rel",
			lambda soup: soup.find_all("a", href=True),
			attribute_transform("href", mv_rel(old_slide_name, new_slide_name) )),
		action(
			"old veeva to new veeva",
			lambda soup: soup.find_all("a", href=True),
			attribute_transform("href", mv_veev(old_slide_name, new_slide_name) ))
	]

	return run_actions(actions, src)

def parse_folder(path, **kwargs):
	actions = kwargs.get("actions", [])
	CUTOFF = kwargs.get("cutoff", float("inf"))
	verbose = kwargs.get("verbose", False)

	matches = []
	for root, dirnames, filenames in os.walk(path):
		if root.count(os.sep) <= CUTOFF:
			for filename in fnmatch.filter(filenames, "*.htm*"):
				matches.append(os.path.join(root, filename))

	for filename in matches:
		if verbose: print("Re-linking %s" % filename)
		for action in actions:
			clean = action(open(filename, 'rb'))
			with open(filename, 'wb') as f:
				f.write(clean.encode('utf-8'))

def runScript():
	## TODO: make work with --root flag
	def does_file_exist(fname):
		exists = os.path.exists(fname)
		if not exists: print("%s does not exist!" % fname)
		return exists

	def all_exists(folders):
		return reduce(lambda acc, arg: acc and does_file_exist(arg), folders, True)


	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
		description = banner(subtitle="Re-Linker"))

	parser.add_argument("--root", nargs=1, help="Project root folder", required=False)
	parser.add_argument("--verbose", action="store_true", required=False, help="Chatty Cathy")

	group = parser.add_mutually_exclusive_group()
	group.add_argument("--mv", nargs=3, metavar=("old_name", "new_name", "source"), help="recursively rename references to an old slide name with a new slide name")
	group.add_argument("--veev2rel", nargs="+", metavar="source", help="recursively replace veeva links with relative links")
	group.add_argument("--rel2veev", nargs="+", metavar="source", help="recursively replace relative links with veeva link")
	group.add_argument("--integrate-all", nargs="+", metavar="source", help="recursively resolve relative links and replace hrefs with veeva")

	if len(sys.argv) == 1:
		parser.print_help()
		return 2

	args = parser.parse_args()
	verbose = args.verbose

	if args.mv is not None:
		old, new, folder = args.mv
		if not all_exists([folder]): 
			return 128
		else:
			return parse_folder(folder, actions=[mv_refs(old, new)], verbose=verbose)

	if args.veev2rel is not None:
		folders = args.veev2rel
		if not all_exists(folders):
			return 128
		else:
			for folder in folders:
				parse_folder(folder, actions=[veev2rel], verbose=verbose)
			return

	if args.rel2veev is not None:
		folders = args.rel2veev
		if not all_exists(folders):
			return 128
		else:
			for folder in folders:
				parse_folder(folder, actions=[rel2veev], verbose=verbose)
			return

	if args.integrate_all is not None:
		folders = args.integrate_all
		if not all_exists(folders):
			return 128
		else:
			for folder in folders:
				parse_folder(folder, actions=[integrate_all], verbose=verbose)
			return

if __name__ == "__main__": 
	sys.exit(runScript())

