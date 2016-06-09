#!/usr/bin/env python3
import activate_venv

from veevutils import banner, is_slide

from ftplib import FTP
from functools import reduce

import argparse
import textwrap
import fnmatch
import re
import os
import sys

def match_zips_to_ctls(zip_path, ctl_path):

	def glob_walk(path, ext):
		matches = []
		for root, dirnames, filenames in os.walk(path):
			for filename in fnmatch.filter(filenames, "*"+ext):
				matches.append(os.path.join(root, filename))
		return matches

	def does_file_exist(fname):
		exists = os.path.exists(fname)
		if not exists: 
			print("%s does not exist!" % fname)
			sys.stdout.flush()
		return exists

	def all_exists(folders):
		return reduce(lambda acc, arg: acc and does_file_exist(arg), folders, True)

	def base_filename(path):
		return os.path.splitext(os.path.split(path)[-1])[0]

	zips = glob_walk(zip_path, '.zip')
	ctls = glob_walk(ctl_path, '.ctl')

	good_zips = [x for x in zips if does_file_exist(x) and is_slide(x)]
	good_ctls = [x for x in ctls if does_file_exist(x)]

	both = list(set([base_filename(x) for x in good_zips]) & set([base_filename(x) for x in good_ctls]))

	return [os.path.join(zip_path, x + ".zip") for x in both], [os.path.join(ctl_path, x + ".ctl") for x in both]

def ftp_publish(**kwargs):
	ZIP_LOCATION = "/content"
	CTL_LOCATION = "/ctlfile"

	server = kwargs['server']
	username = kwargs['username']
	password = kwargs['password']
	zips = kwargs['zips']
	ctls = kwargs['ctls']

	verbose = kwargs.get('verbose', False)

	with FTP(server) as f:
		if verbose:
			print("Connecting to %s..." % server)
			print("Logging in as %s..." % username)
			sys.stdout.flush()

		f.login(username, password)
		
		# per documentation, always upload zip files first
		# try to cwd into content directory (if there isn't one, then upload to the home directory)
		if verbose:
			print("ZIP FILES")
			sys.stdout.flush()

		try:
			f.cwd(ZIP_LOCATION)
		except Exception:
			pass # ignore cd into non-existant folder -> upload to home

		try:
			for zip in zips:
				with open(zip, 'rb') as zipfile:
					if verbose:
						print("Uploading %s..." % zip)
						sys.stdout.flush()

					filename = os.path.split(zip)[-1]

					f.storbinary("STOR " + filename, zipfile)
		except Exception as e:
			# bail on any ftp errors (TODO FIX THIS LOL)
			raise Exception('Error in uploading zip files: ' + str(e))

		if verbose:
			print("CONTROL FILES")
			sys.stdout.flush()

		try:
			f.cwd(CTL_LOCATION)
		except Exception as e:
			raise Exception('Error in accessing control file directory: ' + str(e))

		try:
			for ctl in ctls:
				with open(ctl, 'rb') as ctlfile:
					if verbose:
						print("Uploading %s..." % ctl)
						sys.stdout.flush()

					filename = os.path.split(ctl)[-1]

					f.storbinary("STOR " + filename, ctlfile)
		except Exception as e:
			#bail
			raise Exception('Error in uploading control files: ' + str(e))


def runScript(verbose=False):
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
		description = banner(subtitle="Publisher"))

	parser.add_argument("--zip", nargs=1, help="path to zip files", required=True)
	parser.add_argument("--ctl", nargs=1, help="path to ctl files", required=True)
	parser.add_argument("--host", nargs=1, help="server name", required=True)
	parser.add_argument("--u", nargs=1, help="Veeva username", required=True)
	parser.add_argument("--pwd", nargs=1, help="Veeva password", required=True)
	parser.add_argument("--root", nargs=1, help="Project root folder", required=False)
	parser.add_argument("--verbose", action="store_true", help="Chatty Cathy")

	if len(sys.argv) == 1:
		parser.print_help()
		return 2
	else:
		args = parser.parse_args()

	zips, ctls = match_zips_to_ctls(args.zip[0], args.ctl[0])

	try:
		ftp_publish(zips=zips, ctls=ctls, username=args.u[0], password=args.pwd[0], server=args.host[0], verbose=args.verbose)
	except Exception as e:
		print(e)
		sys.stdout.flush()
		return 128

if __name__ == "__main__":
	sys.exit(runScript())
