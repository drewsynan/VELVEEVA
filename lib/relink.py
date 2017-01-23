#!/usr/bin/env python3
import activate_venv
from veevutils import banner, VALID_SLIDE_EXTENSIONS, parse_slide_name_from_href, veeva_composer, path_composer

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
def action(name, selector, action_closure, composer, source):

	@State
	def closure(old_state):
		b = BeautifulSoup(source, "lxml")
		transformer_(b, selector, action_closure(composer))
		
		return (str(b), old_state + 1)
	return closure

def transformer_(soup, selector, transform):
	items = selector(soup)
	transform(items, soup)


def attribute_transform(attribute, transform):
	@curry
	def transformed(composer, items, soup):
		if items == []: return

		for item in items:
			try:
				transformed = transform(composer, item[attribute])
				item[attribute] = transformed
			except KeyError:
				pass #items might not have the attribute we're looking for
	return transformed

def add_meta(**kwargs):
	@curry
	def transformed(composer, items, soup):
		nonlocal kwargs

		if soup.html is None: return #empty dom

		if items == []:
			meta = soup.new_tag("meta")
			for key in kwargs:
				meta.attrs[key] = kwargs[key]
			
			if soup.head is None: soup.html.append(soup.new_tag("head"))
			
			soup.head.append(meta)

	return transformed

@curry
def veeva_href_to_onclick(composer, items, soup):
	if soup.html is None: return #empty dom

	for item in items:
		current_href = item["href"]
		veeva_match = parse_veeva_href(current_href)
		if veeva_match is not None:
			cmd = veeva_match.command_name
			cmd_args = veeva_match.command_args
			item["href"] = "javascript:void(0)"
			item["onClick"] = composer(cmd, [cmd_args, "''"])

@curry
def veeva_onclick_to_href(composer, items, soup):
	if soup.html is None: return

	for item in items:
		match = parse_veeva_onclick(item["onClick"])
		if match is not None:
			cmd = match.command_name
			cmd_args = match.command_args
			item["href"] = composer(cmd, cmd_args)
			item["onClick"] = None

@curry
def fix_trailing_slash(composer, path):
	last_folder = re.search("(?<=/)[^/]+(?=/$)", path)
	if last_folder is not None:
		return path + last_folder.group(0) + ".html"
	else:
		return path

@curry
def fix_document_root(composer, path):
	return re.sub("^\/(?=[^\/])", "../", path)

@curry
def fix_relative_path(composer, path):
	return re.sub("(\.\.\/)*", "", path)

@curry
def fix_hyperlink_protocol(composer, href):
	if urlparse(href).netloc != '': return href
	
	match = parse_slide_name_from_href(href)

	if match is None:
		return href
	else:
		return composer("gotoSlide", match + ".zip")
@curry
def fix_veev_2_rel(composer, href):
	match = parse_slide_name_from_href(href)
	if match is None:
		return href
	else:
		return composer(match, ".html")
@curry
def fix_rel_2_veev(composer, href):
	return fix_hyperlink_protocol(composer, fix_relative_path(composer, href))

@curry
def mv_rel(old_slide_name, new_slide_name):

	@curry
	def closure(composer, href):
		if urlparse(href).netloc == '':
			old_slide = parse_slide_path(href, slide_name=old_slide_name)
			if old_slide is not None:
				#return old_slide.parent_path + new_slide_name + "/" + new_slide_name + old_slide.extension
				return composer(new_slide_name, old_slide.extension)
			else:
				return href
		else:
			return href

	return closure

@curry
def mv_veev(old_slide_name, new_slide_name):

	@curry
	def closure(composer, href):
		old_slide = parse_veeva_href(href, command_args=old_slide_name+".zip")

		if old_slide is not None:
			return composer(old_slide.command_name, new_slide_name+".zip")
		else:
			return href

	return closure

def run_actions(actions, src):
	return reduce(lambda prev, new: prev >> new, actions, unit(State, src)).getResult(-1)

@curry
def integrate_all(composer, src):
	actions = [
		action(
			"stylesheets",
			lambda soup: soup.find_all("link", {"rel": "stylesheet"}),
			attribute_transform("href", fix_relative_path),
			composer),
		action(
			"scripts",
			lambda soup: soup.find_all("script", src=True),
			attribute_transform("src", fix_relative_path),
			composer),
		action(
			"images",
			lambda soup: soup.find_all("img"),
			attribute_transform("src", fix_relative_path),
			composer),
		action(
			"iframes",
			lambda soup: soup.find_all("iframe"),
			attribute_transform("src", fix_relative_path),
			composer),
		action(
			"hyperlink_paths",
			lambda soup: soup.find_all("a", href=True),
			attribute_transform("href", fix_relative_path),
			composer),
		action(
			"hyperlink_protocols",
			lambda soup: soup.find_all("a", href=True),
			attribute_transform("href", fix_hyperlink_protocol),
			veeva_composer("veeva:")),
		action(
			"utf",
			lambda soup: soup.find_all("meta", charset=True),
			add_meta(charset="utf-8"),
			veeva_composer("veeva:"))
	]

	return run_actions(actions, src)

@curry
def veev2rel(composer,src):
	actions = [
		action(
			"veeva to relative",
			lambda soup: soup.find_all("a", href=True),
			attribute_transform("href", fix_veev_2_rel),
			path_composer("../"))
	]
	return run_actions(actions, src)

@curry
def rel2veev(composer, src):
	actions = [
		action(
			"expand trailing slash", 
			lambda soup: soup.find_all("a", href=True), 
			attribute_transform("href", fix_trailing_slash), 
			composer),
		action(
			"fix root linking",
			lambda soup: soup.find_all("a", href=True),
			attribute_transform("href", fix_document_root),
			composer),
		action(
			"relative to veeva",
			lambda soup: soup.find_all("a", href=True),
			attribute_transform("href", fix_rel_2_veev),
			composer)
	]
	return run_actions(actions, src)

@curry
def mv_refs(old_slide_name, new_slide_name, src):
	actions = [
		action(
			"old rel to old rel",
			lambda soup: soup.find_all("a", href=True),
			attribute_transform("href", mv_rel(old_slide_name, new_slide_name)),
			veeva_composer("veeva:")),
		action(
			"old veeva to new veeva",
			lambda soup: soup.find_all("a", href=True),
			attribute_transform("href", mv_veev(old_slide_name, new_slide_name)),
			veeva_composer("veeva:"))
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

	composer = veeva_composer("veeva:")

	if args.mv is not None:
		old, new, folder = args.mv
		if not all_exists([folder]): 
			return 128
		else:
			return parse_folder(folder, actions=[mv_refs(composer, old, new)], verbose=verbose)

	if args.veev2rel is not None:
		folders = args.veev2rel
		if not all_exists(folders):
			return 128
		else:
			for folder in folders:
				parse_folder(folder, actions=[veev2rel(composer)], verbose=verbose)
			return

	if args.rel2veev is not None:
		folders = args.rel2veev
		if not all_exists(folders):
			return 128
		else:
			for folder in folders:
				parse_folder(folder, actions=[rel2veev(composer)], verbose=verbose)
			return

	if args.integrate_all is not None:
		folders = args.integrate_all
		if not all_exists(folders):
			return 128
		else:
			for folder in folders:
				parse_folder(folder, actions=[integrate_all(composer)], verbose=verbose)
			return

if __name__ == "__main__": 
	sys.exit(runScript())

