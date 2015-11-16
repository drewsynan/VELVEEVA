#!/usr/env/python3
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import os
import fnmatch
import re
import sys

def parseHTML(src):
	b = BeautifulSoup(src, 'lxml')
	replacements = []

	replacements.append({
		"name": "stylesheets", 
		"items": b.find_all("link", {"rel": "stylesheet"}),
		"attribute": "href"
	})

	replacements.append({
		"name": "scripts", 
		"items": b.find_all("script"),
		"attribute": "src"
	})

	replacements.append({
		"name": "hyperlinks",
		"items": b.find_all("a", href=True),
		"attribute": "href"
	})

	replacements.append({
		"name": "images", 
		"items": b.find_all("img"),
		"attribute": "src"
	})

	parseTagsets(replacements)
	parseHyperlinks([item["items"] for item in replacements if item["name"] == "hyperlinks"][0])
	fixUtf8(b)
	
	return b.prettify()

def parseTagsets(tagsetList):
	for tagset in tagsetList: parseTagset(tagset)

def parseHyperlinks(linkList):
	for hyperlink in linkList: 
		hyperlink["href"] = parseHyperlink(hyperlink["href"])

def parseHyperlink(link):
	if urlparse(link).netloc != '': return link
	
	match = re.search("(?P<slide_name>[^/]+)\/(?P=slide_name)\.htm(l)?", link)
	if match is None:
		return link
	else:
		slide_name = match.group(1)
		return "veeva:gotoSlide(%s.zip)" % slide_name


def parseTagset(tagset):
	for item in tagset["items"]:
		item[tagset["attribute"]] = fixRelativePath(item[tagset["attribute"]])

def fixRelativePath(path):
	return re.sub("(\.\.\/)*", "", path)

def parseFolder(path):
	matches = []
	for root, dirnames, filenames in os.walk(rootDir):
		for filename in fnmatch.filter(filenames, "*.htm*"):
			matches.append(os.path.join(root, filename))

	for filename in matches:
		print("Re-linking %s" % filename)
		clean = parseHTML(open(filename, 'rb'))
		with open(filename, 'wb') as f:
			f.write(clean.encode('utf-8'))

def fixUtf8(soup):
	if soup.find_all("meta", charset=True) == []:
		meta = soup.new_tag("meta")
		meta.attrs['charset'] = 'utf-8'
		soup.head.append(meta)

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