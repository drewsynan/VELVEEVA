#!/usr/bin/env python3
from ftplib import FTP
from genctls import isSlide
from functools import reduce
import argparse
import textwrap
import fnmatch
import re
import os
import sys

def match_zips_to_ctls(zip_path, ctl_path):

	def globWalk(path, ext):
		matches = []
		for root, dirnames, filenames in os.walk(path):
			for filename in fnmatch.filter(filenames, "*"+ext):
				matches.append(os.path.join(root, filename))
		return matches

	def doesFileExist(fname):
		exists = os.path.exists(fname)
		if not exists: print("%s does not exist!" % fname)
		return exists

	def allExists(folders):
		return reduce(lambda acc, arg: acc and doesFileExist(arg), folders, True)

	def baseFilename(path):
		return os.path.splitext(os.path.split(path)[-1])[0]

	zips = globWalk(zip_path, '.zip')
	ctls = globWalk(ctl_path, '.ctl')

	goodZips = [x for x in zips if doesFileExist(x) and isSlide(x)]
	goodCtls = [x for x in ctls if doesFileExist(x)]

	both = list(set([baseFilename(x) for x in goodZips]) & set([baseFilename(x) for x in goodCtls]))

	return [os.path.join(zip_path, x + ".zip") for x in both], [os.path.join(ctl_path, x + ".ctl") for x in both]

def ftp_publish(**kwargs):
	ZIP_LOCATION = "/content"
	CTL_LOCATION = "/ctlfile"

	server = kwargs['server']
	username = kwargs['username']
	password = kwargs['password']
	zips = kwargs['zips']
	ctls = kwargs['ctls']

	with FTP(server) as f:
		print("Connecting to %s..." % server)
		print("Logging in as %s..." % username)
		f.login(username, password)
		
		# per documentation, always upload zip files first
		# try to cwd into content directory (if there isn't one, then upload to the home directory)
		print("ZIP FILES")
		try:
			f.cwd(ZIP_LOCATION)
		except Exception:
			pass

		try:
			for zip in zips:
				with open(zip, 'rb') as zipfile:
					print("Uploading %s..." % zip)
					filename = os.path.split(zip)[-1]

					f.storbinary("STOR " + filename, zipfile)
		except Exception as e:
			# bail on any ftp errors (TODO FIX THIS LOL)
			raise Exception('Error in uploading zip files: ' + str(e))


		print("CONTROL FILES")
		try:
			f.cwd(CTL_LOCATION)
		except Exception as e:
			raise Exception('Error in accessing control file directory: ' + str(e))

		try:
			for ctl in ctls:
				with open(ctl, 'rb') as ctlfile:
					print("Uploading %s..." % ctl)
					filename = os.path.split(ctl)[-1]

					f.storbinary("STOR " + filename, ctlfile)
		except Exception as e:
			#bail
			raise Exception('Error in uploading control files: ' + str(e))


def runScript():
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
		description = textwrap.dedent('''\
			 _   ________ _   ___________   _____ 
			| | / / __/ /| | / / __/ __| | / / _ |
			| |/ / _// /_| |/ / _// _/ | |/ / __ |
			|___/___/____|___/___/___/ |___/_/ |_|
			                                      
			~~~~~~====P U B L I S H E R====~~~~~~~

			    FTP only for now (sorry, folks)
			'''))

	parser.add_argument("--zip", nargs=1, help="path to zip files")
	parser.add_argument("--ctl", nargs=1, help="path to ctl files")
	parser.add_argument("--host", nargs=1, help="server name")
	parser.add_argument("--u", nargs=1, help="Veeva username")
	parser.add_argument("--pwd", nargs=1, help="Veeva password")

	if len(sys.argv) == 1:
		parser.print_help()
		return
	else:
		args = parser.parse_args()

	zips, ctls = match_zips_to_ctls(args.zip[0], args.ctl[0])

	try:
		ftp_publish(zips=zips, ctls=ctls, username=args.u[0], password=args.pwd[0], server=args.host[0])
	except Exception as e:
		print(e)
		return

if __name__ == "__main__":
	runScript()
