#!/usr/bin/env python3
import activate_venv

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

def isSlide(filename):
	return parseSlide(filename) is not None

def parseSlide(filename):
	baseName = os.path.split(os.path.splitext(filename)[0])[-1]
	matcher = re.compile("(?:" + baseName + "/)(" + baseName + "(.htm(?:l)?|.pdf|.jpg|.jpeg))$")

	with ZipFile(filename, 'r') as z:
		results = [x for x in z.namelist() if matcher.match(x) is not None]

		if len(results) > 0:
			slideNames = [(matcher.match(x).group(0), matcher.match(x).group(2)) for x in results]
			return slideNames[0]

	return None

def parseMeta(filename):
	slideFile = parseSlide(filename)
	if slideFile is None: return None


	with ZipFile(filename, 'r') as z:
		with(z.open(slideFile[0])) as f:
			slideType = slideFile[1]

			title_string = None
			description_string = None

			if slideType == ".htm" or slideType == ".html":
				soup = BeautifulSoup(f.read(), "lxml")

				title = soup.find('meta', {'name':'veeva_title'})
				if title is not None:
					title_string = title.get('content', None)

				description = soup.find('meta', {'name':'veeva_description'})
				if description is not None:
					description_string = description.get('content', None)

			if slideType == ".pdf":
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

			if slideType == ".jpg" or slideType == ".jpeg":
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

	meta = parseMeta(filename)
	pieces = []

	pieces.append("USER="+str(username))
	pieces.append("PASSWORD="+str(password))
	pieces.append("FILENAME="+os.path.split(meta['filename'])[-1])

	if email is not None: pieces.append("EMAIL="+str(email))
	if version is not None: pieces.append("Slide_Version_vod__c=" + str(version))
	if meta is not None:
		if meta['veeva_description'] is not None:
			pieces.append("Description_vod__c=" + str(meta['veeva_description']))
		if meta['veeva_title'] is not None:
			pieces.append("Name=" + str(meta['veeva_title']))

	pieces.append('')

	new_filename = os.path.splitext(os.path.split(meta['filename'])[-1])[0] + ".ctl"

	return {"filename": new_filename, "record": ("\n").join(pieces)}

def parseFolder(path, **kwargs):
	actions = kwargs.get("actions", [])
	CUTOFF = kwargs.get("cutoff", float("inf"))
	root = kwargs["root"]
	username = kwargs["username"]
	password = kwargs["password"]
	out = kwargs["out"]
	email = kwargs.get("email", None)

	version = parseCurrentVersion(root)

	if not os.path.exists(out): os.mkdir(out)

	matches = []
	for root, dirnames, filenames in os.walk(path):
		if root.count(os.sep) <= CUTOFF:
			for filename in fnmatch.filter(filenames, "*.zip"):
				if isSlide(os.path.join(root,filename)): matches.append(os.path.join(root, filename))

	control_files = [createRecordString(m, version=version, username=username, password=password, email=email) for m in matches]

	for control in control_files:
		with open(os.path.join(out, control['filename']), 'w') as f:
			f.write(control['record'])


def runScript():
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
		description = textwrap.dedent('''\
			 _   ________ _   ___________   _____ 
			| | / / __/ /| | / / __/ __| | / / _ |
			| |/ / _// /_| |/ / _// _/ | |/ / __ |
			|___/___/____|___/___/___/ |___/_/ |_|
			                                      
			~~~~~~~~ .ctl FILE GENERATOR ~~~~~~~~~
			'''))

	parser.add_argument("--src", nargs=1, help="path to folder containing zip files to process")
	parser.add_argument("--out", nargs=1, help="path for output ctl files (will be created if it does not exist)")
	parser.add_argument("--root", nargs=1, help="root directory for the project (used for versioning)")
	parser.add_argument("--u", nargs=1, help="Veeva username")
	parser.add_argument("--pwd", nargs=1, help="Veeva password")
	parser.add_argument("--email", nargs=1, help="Optional email for errors")

	if len(sys.argv) == 1:
		parser.print_help()
		return
	else:
		args = parser.parse_args()

	email = None
	if args.email is not None: email = args.email[0]

	parseFolder(args.src[0], out=args.out[0], root=args.root[0], username=args.u[0], password=args.pwd[0], email=email)

if __name__ == "__main__":
	runScript()