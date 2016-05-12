#!/usr/bin/env python3
from lib import activate_venv

from painter import paint
from progressbar import ProgressBar, Percentage, Bar

import argparse
import textwrap
import sys
import json
import shutil
import subprocess
import os
import inspect
import concurrent.futures



def banner(type="normal"):
	MSG = textwrap.dedent('''\
			 _   ________ _   ___________   _____ 
			| | / / __/ /| | / / __/ __| | / / _ |
			| |/ / _// /_| |/ / _// _/ | |/ / __ |
			|___/___/____|___/___/___/ |___/_/ |_|                                      
			''')

	types = {
		"normal": paint.yellow.bold,
		"error": paint.red.bold
	}

	return types[type](MSG)

def execute(command):
	popen = subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True)
	stdout_lines = iter(popen.stdout.readline, "")
	for stdout_line in stdout_lines:
		yield stdout_line

	popen.stdout.close()
	returncode = popen.wait()
	if returncode != 0:
		raise subprocess.CalledProcessError(returncode, command)


def parse_config(config_file="VELVEEVA-config.json"):
	return json.load(open(config_file))

def scaffold(root, config, verbose=False):
	folders = config["MAIN"]

	def mine(p):
		if not os.path.exists(os.path.join(root,p)): os.makedirs(os.path.join(root, p))

	mine(folders["source_dir"])
	mine(folders["output_dir"])
	mine(folders["temp_dir"])

	#mine(os.path.join(folders["output_dir"], folders["zips_dir"]))
	#mine(os.path.join(folders["output_dir"], folders["ctls_dir"]))

def nuke(root, config, verbose=False):
	folders = config["MAIN"]
	try:
		shutil.rmtree(os.path.join(root,folders["output_dir"]))
		shutil.rmtree(os.path.join(root,folders["temp_dir"]))
	except Exception as e:
		pass

def copy_locals(root_dir, src, dest, verbose=False):
	slides = next(os.walk(os.path.join(root_dir,src)))[1] # (root, dirs, files)
	
	with concurrent.futures.ProcessPoolExecutor() as executor:
		futures = {}

		for slide in slides:
			# copy everything except for html files that match the parent folder name
			for root, dirs, files in os.walk(os.path.join(root_dir,src,slide)):
				for file in files:
					if not os.path.splitext(os.path.basename(file))[0] == slide:
						s = os.path.abspath(os.path.join(root,file))
						dest_dir = os.path.abspath(os.path.join(root_dir,dest,slide))
						d = os.path.abspath(os.path.join(root_dir,dest,slide,file))

						if not os.path.exists(dest_dir): os.makedirs(dest_dir)
						futures[executor.submit(shutil.copy,s,d)] = s+d
		for future in concurrent.futures.as_completed(futures):
			try:
				data = future.result()
			except Exception as e:
				raise e

def doScript():
	VERBOSE = False

	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
		description=banner())
	
	parser.add_argument("--bake", 			action="store_true", help="Compile templates and SASS (yum!)")
	parser.add_argument("--clean",			action="store_true", help="Clean up the mess (mom would be proud!) [Selected when no options are given]")
	parser.add_argument("--controls",		action="store_true", help="Generate slide control files (gonna have something already baked)")
	parser.add_argument("--controlsonly", 	action="store_true", help="Only generate control files")
	parser.add_argument("--dev",			action="store_true", help="Use the quick-bake test kitchen environment (no screenshots, no packaging). This is a shortcut to using go --clean --watch --veev2rel")
	parser.add_argument("--init",			action="store_true", help="Initialize a new VELVEEVA project")
	parser.add_argument("--nuke", 			action="store_true", help="Nuke old builds and temp files")
	parser.add_argument("--nobake",			action="store_true", help="Don't bake it...")
	parser.add_argument("--package",		action="store_true", help="Wrap it up [Selected when no options are given]")
	parser.add_argument("--packageonly",	action="store_true", help="Just wrap it up (you gotta already have something baked)")
	parser.add_argument("--publish", 		action="store_true", help="Ship it off to market")
	parser.add_argument("--publishonly",	action="store_true", help="(Only) ship it off to market (you gotta already have something baked, and control files generated)")
	parser.add_argument("--relink", 		action="store_true", help="Make some href saussage (replace relative links with global and convert to veeva: protocol)")
	parser.add_argument("--screenshots",	action="store_true", help="Include Screenshots [Selected when no options are given]")
	parser.add_argument("--veev2rel",		action="store_true", help="Convert veeva: hrefs to relative links")
	parser.add_argument("--verbose",		action="store_true", help="Chatty Cathy")
	parser.add_argument("--watch",			action="store_true", help="Watch for changes and re-bake on change")
	
	if len(sys.argv) == 1:
		parser.print_help()
		sys.exit(0)

	args = parser.parse_args()
	config = parse_config()

	SOURCE_DIR = config['MAIN']['source_dir']
	DEST_DIR = config['MAIN']['output_dir']
	GLOBALS_DIR = config['MAIN']['globals_dir']
	PARTIALS_DIR = config['MAIN']['partials_dir']
	TEMPLATES_DIR = config['MAIN']['templates_dir']
	ZIPS_DIR = config['MAIN']['zips_dir']

	### CTL File Info ###
	CTLS_DIR = config['MAIN']['ctls_dir']
	VEEVA_USERNAME = config['VEEVA']['username']
	VEEVA_PWD = config['VEEVA']['password']
	VEEVA_SERVER = config['VEEVA']['server']
	VEEVA_EMAIL = config['VEEVA'].get('email', None)

	ROOT_DIR = os.getcwd()
	CONFIG_FILE_NAME = "VELVEEVA-config.json"
	PROJECT_NAME = config['MAIN']['name']

	VELVEEVA_DIR = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))

	#💩🍕

	print(banner())
	print("👉  %s 👈\n" % paint.bold.yellow(PROJECT_NAME))

	with ProgressBar(max_value=8, widgets=[Bar(marker="🍕"),Percentage()], redirect_stdout=True) as progress:
		#0. nuke
		progress.update(0)
		print("🔥  %s" % paint.gray("Nuking old builds..."))
		nuke(ROOT_DIR, config)

		#1. scaffold needed folders 🗄
		progress.update(1)
		print("🗄  %s" % paint.gray("Creating directories..."))
		scaffold(ROOT_DIR, config)

		#2. inline local (non-html) files, and create build folders 💉
		progress.update(2)
		print("💉  %s " % paint.gray("Inlining partials and globals..."))
		copy_locals(ROOT_DIR, SOURCE_DIR, DEST_DIR)

		#3. inline partials and globals 
		progress.update(3)
		cmd = os.path.join(VELVEEVA_DIR, "lib", "inject.py")
		for out in execute(["python3", cmd, ROOT_DIR, GLOBALS_DIR, DEST_DIR]):
			print(out)

		#4. render sass 💅
		progress.update(4)
		print("💅  %s " % paint.gray("Compiling SASS..."))
		cmd = os.path.join(VELVEEVA_DIR, "lib", "compile_sass.py")

		for out in execute(["python3", cmd, os.path.join(ROOT_DIR,DEST_DIR)]):
			print(out)

		#5. render templates 📝
		progress.update(5)
		print("📝  %s " % paint.gray("Rendering templates..."))
		cmd = os.path.join(VELVEEVA_DIR, "lib", "render_templates.py")

		for out in execute(["python3", cmd, 
			os.path.join(ROOT_DIR, SOURCE_DIR), os.path.join(ROOT_DIR,DEST_DIR),
			os.path.join(ROOT_DIR, TEMPLATES_DIR),
			os.path.join(ROOT_DIR, PARTIALS_DIR)]):
			print(out)

		#6. take screenshots 📸
		progress.update(6)
		print("📸  %s " % paint.gray("Taking screenshots..."))
		cmd = os.path.join(VELVEEVA_DIR, "lib", "screenshot.py")
		src = os.path.abspath(os.path.join(ROOT_DIR,DEST_DIR))
		cfg = os.path.abspath(os.path.join(ROOT_DIR,CONFIG_FILE_NAME))

		for out in execute(["python3", cmd, src, cfg]):
			print(out)

		#7. package slides 📬
		progress.update(7)
		print("📬  %s " % paint.gray("Packaging slides..."))
		cmd = os.path.join(VELVEEVA_DIR, "lib", "package_slides.py")
		for out in execute(["python3", cmd, os.path.join(ROOT_DIR,DEST_DIR), os.path.join(ROOT_DIR,DEST_DIR,ZIPS_DIR)]):
			print(out)

		#8. generate control files ⚒
		progress.update(8)
		print("⚒  %s " % paint.gray("Generating .ctl files..."))
		cmd = os.path.join(VELVEEVA_DIR, "lib", "genctls.py")

		flags = ["python3"
			, cmd
			, "--root", ROOT_DIR
			, "--src", os.path.abspath(os.path.join(ROOT_DIR,DEST_DIR,ZIPS_DIR))
			, "--out", os.path.abspath(os.path.join(ROOT_DIR,DEST_DIR,CTLS_DIR))
			, "--u", VEEVA_USERNAME
			, "--pwd", VEEVA_PWD]

		if VEEVA_EMAIL is not None: flags = flags + ["--email", VEEVA_EMAIL]

		for out in execute(flags):
			print(out)

		#9. ftp 🚀
		# relinking
		# concurrent build
		# not as shitty exception handling
		# file watcher architecture
		# all utils should use python argparse and --src SRC (e.g.) flags not strictly positional arguments
		# make flags required (so fails if not present)
		# unified banner printer

	print(paint.bold.green("\n🍕  Yum!"))
	print(paint.bold.red("\n💩  there was an error:"))

if __name__ == '__main__':
	doScript()