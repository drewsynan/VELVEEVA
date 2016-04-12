#!/usr/bin/env python3
import activate_venv

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

def attributeTransform(attribute, transform):
	def transformed(items, soup):
		if items == []: return

		for item in items:
			item[attribute] = transform(item[attribute])
	return transformed

def addMeta(**kwargs):
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

def fixRelativePath(path):
	return re.sub("(\.\.\/)*", "", path)

def fixHyperlinkProtocol(href):
	if urlparse(href).netloc != '': return href
	
	match = re.search("(?P<slide_name>[^/]+)\/(?P=slide_name)\.htm(l)?", href)
	if match is None:
		return href
	else:
		slide_name = match.group(1)
		return "veeva:gotoSlide(%s.zip)" % slide_name

def fixVeev2Rel(href):
	match = re.search("veeva:gotoSlide\((.+)\.zip\)", href)
	if match is None:
		return href
	else:
		return "../" + match.group(1) + "/" + match.group(1) + ".html"

def fixRel2Veev(href):
	return fixHyperlinkProtocol(fixRelativePath(href))

@curry
def mvRel(old_slide_name, new_slide_name, href):
	if urlparse(href).netloc == '':
		oldSlide = re.compile("((?:[^/]*\/)*)(?P<slide_name>" + old_slide_name + ")\/(?P=slide_name)(\.htm(?:l)?)")
		return oldSlide.sub(r"\g<1>" + new_slide_name + "/" + new_slide_name + r"\g<3>", href)
	else:
		return href

@curry
def mvVeev(old_slide_name, new_slide_name, href):
	oldSlide = re.compile("veeva:([^(]+)\(" + old_slide_name + ".zip\)")
	return oldSlide.sub(r"veeva:\g<1>" + "(" + new_slide_name + ".zip)", href)

def runActions(actions, src):
	return reduce(lambda prev, new: prev >> new, actions, unit(State, src)).getResult(-1)

def integrateAll(src):
	actions = [
		action(
			"stylesheets",
			lambda soup: soup.find_all("link", {"rel": "stylesheet"}),
			attributeTransform("href", fixRelativePath)),
		action(
			"scripts",
			lambda soup: soup.find_all("script", src=True),
			attributeTransform("src", fixRelativePath)),
		action(
			"images",
			lambda soup: soup.find_all("img"),
			attributeTransform("src", fixRelativePath)),
		action(
			"iframes",
			lambda soup: soup.find_all("iframe"),
			attributeTransform("src", fixRelativePath)),
		action(
			"hyperlink_paths",
			lambda soup: soup.find_all("a", href=True),
			attributeTransform("href", fixRelativePath)),
		action(
			"hyperlink_protocols",
			lambda soup: soup.find_all("a", href=True),
			attributeTransform("href", fixHyperlinkProtocol)),
		action(
			"utf",
			lambda soup: soup.find_all("meta", charset=True),
			addMeta(charset="utf-8"))
	]

	return runActions(actions, src)

def veev2rel(src):
	actions = [
		action(
			"veeva to relative",
			lambda soup: soup.find_all("a", href=True),
			attributeTransform("href", fixVeev2Rel))
	]
	return runActions(actions, src)

def rel2veev(src):
	actions = [
		action(
			"relative to veeva",
			lambda soup: soup.find_all("a", href=True),
			attributeTransform("href", fixRel2Veev))
	]
	return runActions(actions, src)

@curry
def mvRefs(old_slide_name, new_slide_name, src):
	actions = [
		action(
			"old rel to old rel",
			lambda soup: soup.find_all("a", href=True),
			attributeTransform("href", mvRel(old_slide_name, new_slide_name) )),
		action(
			"old veeva to new veeva",
			lambda soup: soup.find_all("a", href=True),
			attributeTransform("href", mvVeev(old_slide_name, new_slide_name) ))
	]

	return runActions(actions, src)

def parseFolder(path, **kwargs):
	actions = kwargs.get("actions", [])
	CUTOFF = kwargs.get("cutoff", float("inf"))

	matches = []
	for root, dirnames, filenames in os.walk(path):
		if root.count(os.sep) <= CUTOFF:
			for filename in fnmatch.filter(filenames, "*.htm*"):
				matches.append(os.path.join(root, filename))

	for filename in matches:
		print("Re-linking %s" % filename)
		for action in actions:
			clean = action(open(filename, 'rb'))
			with open(filename, 'wb') as f:
				f.write(clean.encode('utf-8'))

def runScript():
	def doesFileExist(fname):
		exists = os.path.exists(fname)
		if not exists: print("%s does not exist!" % fname)
		return exists

	def allExists(folders):
		return reduce(lambda acc, arg: acc and doesFileExist(arg), folders, True)


	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
		description = textwrap.dedent('''\
			 _   ________ _   ___________   _____ 
			| | / / __/ /| | / / __/ __| | / / _ |
			| |/ / _// /_| |/ / _// _/ | |/ / __ |
			|___/___/____|___/___/___/ |___/_/ |_|
			                                      
			~~~~~~~~~~~~ RE - LINKER ~~~~~~~~~~~~~
			'''))

	parser.add_argument("--mv", nargs=3, help="recursively rename slide refs", metavar=("OLD_NAME", "NEW_NAME", "FOLDER"))
	parser.add_argument("--veev2rel", nargs="+", help="recursively replace veeva links with relative links", metavar="FOLDER")
	parser.add_argument("--rel2veev", nargs="+", help="recursively replace relative links with veeva links", metavar="FOLDER")
	parser.add_argument("--integrate_all", nargs="+", help="recursively resolve relative links and replace hrefs with veeva", metavar="FOLDER")
	
	if len(sys.argv) == 1:
		parser.print_help()
		return
	else:
		args = parser.parse_args()

	if args.mv is not None:
		old, new, folder = args.mv
		if not allExists([folder]): 
			return
		else:
			return parseFolder(folder, actions=[mvRefs(old, new)])

	if args.veev2rel is not None:
		folders = args.veev2rel
		if not allExists(folders):
			return
		else:
			for folder in folders:
				parseFolder(folder, actions=[veev2rel])
			return

	if args.rel2veev is not None:
		folders = args.rel2veev
		if not allExists(folders):
			return
		else:
			for folder in folders:
				parseFolder(folder, actions=[rel2veev])
			return

	if args.integrate_all is not None:
		folders = args.integrate_all
		if not allExists(folders):
			return
		else:
			for folder in folders:
				parseFolder(folder, actions=[integrateAll])
			return

if __name__ == "__main__": runScript()

