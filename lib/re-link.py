#!/usr/bin/env python3
from bs4 import BeautifulSoup # also requires lxml
from functools import reduce
from pymonad import *
from urllib.parse import urlparse
import os
import re
import sys

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
		for item in items:
			item[attribute] = transform(item[attribute])
	return transformed

def addMeta(**kwargs):
	def transformed(items, soup):
		nonlocal kwargs

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

def parseHTML(src):
	actions = [
		action(
			"stylesheets",
			lambda soup: soup.find_all("link", {"rel": "stylesheet"}),
			attributeTransform("href", fixRelativePath)),
		action(
			"scripts",
			lambda soup: soup.find_all("script"),
			attributeTransform("src", fixRelativePath)),
		action(
			"images",
			lambda soup: soup.find_all("img"),
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

	return reduce(lambda prev, new: prev >> new, actions, unit(State, src)).getResult(-1)

def parseFolder(path):
	matches = []
	for root, dirnames, filenames in os.walk(path):
		for filename in fnmatch.filter(filenames, "*.htm*"):
			matches.append(os.path.join(root, filename))

	for filename in matches:
		print("Re-linking %s" % filename)
		clean = parseHTML(open(filename, 'rb'))
		with open(filename, 'wb') as f:
			f.write(clean.encode('utf-8'))

def runScript():
	if len(sys.argv) < 2:
		print("Please specify a folder")
		return

	valid = True
	for arg in sys.argv[1:]:
		valid = valid and os.path.exists(arg)
		if not valid:
			print("%s does not exist!" % arg)

	if not valid: return

	for folder in sys.argv[1:]: parseFolder(folder)

if __name__ == "__main__": runScript()
