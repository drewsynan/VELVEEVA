#!/usr/bin/env python3
import activate_venv

from veevutils import banner, parse_slide, is_slide

from zipfile import ZipFile
from functools import reduce
from bs4 import BeautifulSoup
from git import Repo
from pdfminer.pdfparser import PDFDocument
from pdfminer.pdfparser import PDFParser
from libxmp import consts
from libxmp import XMPFiles

import re
import os
import time
import sys
import argparse
import textwrap
import fnmatch
import uuid

# def isSlide(filename):
# 	return parseSlide(filename) is not None

# def parseSlide(filename):
# 	baseName = os.path.split(os.path.splitext(filename)[0])[-1]
# 	matcher = re.compile("(?:" + baseName + "/)(" + baseName + "(.htm(?:l)?|.pdf|.jpg|.jpeg))$")

# 	with ZipFile(filename, 'r') as z:
# 		results = [x for x in z.namelist() if matcher.match(x) is not None]

# 		if len(results) > 0:
# 			slideNames = [(matcher.match(x).group(0), matcher.match(x).group(2)) for x in results]
# 			return slideNames[0]

# 	return None

def parse_meta(filename):
	slide_file = parse_slide(filename)
	if slide_file is None: 
		return { 'filename': os.path.basename(filename), 
				 'veeva_title': os.path.splitext(os.path.basename(filename))[0], 
				 'veeva_description': os.path.splitext(os.path.basename(filename))[0] }


	with ZipFile(filename, 'r') as z:
		with(z.open(slide_file[0])) as f:
			slide_type = slide_file[1]

			title_string = None
			description_string = None

			if slide_type == ".htm" or slide_type == ".html":
				soup = BeautifulSoup(f.read(), "lxml")

				title = soup.find('meta', {'name':'veeva_title'})
				if title is not None:
					title_string = title.get('content', None)

				description = soup.find('meta', {'name':'veeva_description'})
				if description is not None:
					description_string = description.get('content', None)

			if slide_type == ".pdf":
				doc = PDFDocument()
				parser = PDFParser(f)

				# omfg this is so janky, there needs to be a better library
				parser.set_document(doc)
				doc.set_parser(parser)

				metadata = doc.info
				if len(metadata) > 0:
					latest = metadata[-1]
					try:
						if latest['Title'] != '': title_string = latest['Title']
					except KeyError:
						title_string = None

					try:
						if latest['Subject'] != '': description_string = latest['Subject']
					except KeyError:
						description_string = None

			if slide_type == ".jpg" or slide_type == ".jpeg":
				tmp_file_name = str(uuid.uuid1()) + ".jpg"
				with open(tmp_file_name, 'wb') as tf:
					tf.write(f.read())

				xmpfile = XMPFiles(file_path=tmp_file_name)
				xmp = xmpfile.get_xmp()
				xmpfile.close_file()

				try:
					title_string = xmp.get_localized_text(consts.XMP_NS_DC, 'title', None, 'x-default')
				except XMPError:
					title_string = None

				try:
					description_string = xmp.get_localized_text(consts.XMP_NS_DC, 'description', None, 'x-default')
				except XMPError:
					description_string = None

				os.remove(tmp_file_name)

	return {"filename": filename, "veeva_title": title_string, "veeva_description": description_string}

def parseCurrentCommit(repo_path):
	r = Repo(repo_path)
	sha = str(r.head.commit)
	return sha[0:4] + "..." + sha[-4:]


def parseCurrentVersion(root_path):
	try:
		v = parseCurrentCommit(root_path)
	except Exception:
		v = str(time.time())

	return v

def createRecordString(filename, version=None, email=None, username=None, password=None):

	meta = parse_meta(filename)
	pieces = []

	pieces.append("USER="+str(username))
	pieces.append("PASSWORD="+str(password))
	pieces.append("FILENAME="+os.path.basename(meta['filename']))

	if email is not None: pieces.append("EMAIL="+str(email))
	if version is not None: pieces.append("Slide_Version_vod__c=" + str(version))
	if meta is not None:
		if meta['veeva_description'] is not None:
			pieces.append("Description_vod__c=" + str(meta['veeva_description']))
		if meta['veeva_title'] is not None:
			pieces.append("Name=" + str(meta['veeva_title']))
		else:
			pieces.append("Name=" + os.path.splitext(os.path.basename(meta['filename']))[0])

	pieces.append('')

	new_filename = os.path.splitext(os.path.split(meta['filename'])[-1])[0] + ".ctl"

	return {"filename": new_filename, "record": ("\n").join(pieces)}

def parseFolder(src, **kwargs):
	actions = kwargs.get("actions", [])
	CUTOFF = kwargs.get("cutoff", float("inf"))
	root = kwargs["root"]
	out = kwargs["out"]

	username = kwargs["username"]
	password = kwargs["password"]
	email = kwargs.get("email", None)

	version = parseCurrentVersion(root)

	source_path = os.path.join(root, src)
	dest_path = os.path.join(root, out)

	novalidate = kwargs["novalidate"]

	if not os.path.exists(dest_path): os.makedirs(dest_path)


	matches = []
	for root, dirnames, filenames in os.walk(source_path):
		for filename in fnmatch.filter(filenames, "*.zip"):
			if novalidate:
				matches.append(os.path.join(root,filename))
			else:
				if is_slide(os.path.join(root,filename)): matches.append(os.path.join(root,filename))


	control_files = [createRecordString(m, version=version, username=username, password=password, email=email) for m in matches]

	for control in control_files:
		with open(os.path.join(dest_path, control['filename']), 'w') as f:
			f.write(control['record'])

def runScript():
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
		description = banner(subtitle=".ctl File Generator"))

	parser.add_argument("source", nargs=1, help="path to folder containing zip files to process")
	parser.add_argument("destination", nargs=1, help="path for output ctl files (will be created if it does not exist)")
	parser.add_argument("--u", metavar="USERNAME", nargs=1, help="Veeva username", required=True)
	parser.add_argument("--pwd", metavar="PASSWORD", nargs=1, help="Veeva password", required=True)
	parser.add_argument("--email", nargs=1, help="Optional email for errors", required=False)
	parser.add_argument("--verbose", action="store_true", help="Chatty Cathy", required=False)
	parser.add_argument("--root", nargs=1,
		 help="Optional root directory for the project (used for versioning) current working directory used if none specified", 
		 required=False)
	parser.add_argument("--novalidate", action="store_true", help="Don't check to see if each zip file is a slide")

	if len(sys.argv) == 1:
		parser.print_help()
		return 2
	else:
		args = parser.parse_args()

	email = None
	if args.email is not None: email = args.email[0]
	if args.root is None:
		ROOT = os.getcwd()
	else:
		ROOT = args.root[0]

	SOURCE = args.source[0]
	DEST = args.destination[0]

	parseFolder(SOURCE, out=DEST, root=ROOT, username=args.u[0], password=args.pwd[0], email=email, novalidate=args.novalidate)

if __name__ == "__main__":
	sys.exit(runScript())