#!/usr/bin/env python3
from lib import activate_venv
from lib.veevutils import banner

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
import functools


def execute(command):
	popen = subprocess.Popen(command, bufsize=0, stdout=subprocess.PIPE, universal_newlines=True)
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

def create_environment(config):
	ENV = {}
	ENV['config'] = config

	ENV['SOURCE_DIR']		= config['MAIN']['source_dir']
	ENV['DEST_DIR']			= config['MAIN']['output_dir']
	ENV['GLOBALS_DIR']		= config['MAIN']['globals_dir']
	ENV['PARTIALS_DIR']		= config['MAIN']['partials_dir']
	ENV['TEMPLATES_DIR']	= config['MAIN']['templates_dir']
	ENV['ZIPS_DIR']			= config['MAIN']['zips_dir']

	### CTL File Info ###
	ENV['CTLS_DIR']			= config['MAIN']['ctls_dir']
	ENV['VEEVA_USERNAME']	= config['VEEVA']['username']
	ENV['VEEVA_PASSWORD']	= config['VEEVA']['password']
	ENV['VEEVA_SERVER']		= config['VEEVA']['server']
	ENV['VEEVA_EMAIL']		= config['VEEVA'].get('email', None)

	ENV['ROOT_DIR']			= os.getcwd()
	ENV['CONFIG_FILE_NAME']	= "VELVEEVA-config.json"
	ENV['PROJECT_NAME']		= config['MAIN']['name']

	ENV['VELVEEVA_DIR']		= os.path.dirname(os.path.abspath(inspect.stack()[0][1]))

	return ENV

def create_parser():
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
		description=banner())
	
	parser.add_argument("--bake", 			action="store_true", help="Compile templates and SASS (yum!)")
	parser.add_argument("--clean",			action="store_true", help="Clean up the mess (mom would be proud!)")
	parser.add_argument("--controls",		action="store_true", help="Generate slide control files (gonna have something already baked)")
	parser.add_argument("--dev",			action="store_true", help="Use the quick-bake test kitchen environment (no screenshots, no packaging). This is a shortcut to using --nuke --bake --watch --veev2rel")
	parser.add_argument("--go", 			action="store_true", help="Use a quick-bake recipe -> nuke, bake, screenshots, package, clean")
	parser.add_argument("--init",			action="store_true", help="Initialize a new VELVEEVA project")
	parser.add_argument("--nuke", 			action="store_true", help="Nuke old builds and temp files")
	parser.add_argument("--package",		action="store_true", help="Wrap it up [Selected when no options are given]")
	parser.add_argument("--publish", 		action="store_true", help="Ship it off to market")
	parser.add_argument("--relink", 		action="store_true", help="Make some href saussage (replace relative links with global and convert to veeva: protocol)")
	parser.add_argument("--rel2veev", 		action="store_true", help="Convert relative links to veeva: protocol")
	parser.add_argument("--screenshots",	action="store_true", help="Include Screenshots")
	parser.add_argument("--veev2rel",		action="store_true", help="Convert veeva: hrefs to relative links")
	parser.add_argument("--verbose",		action="store_true", help="Chatty Cathy")
	parser.add_argument("--watch",			action="store_true", help="Watch for changes and re-bake on change")

	return parser

def doScript():
	VERBOSE = False

	parser = create_parser()	
	
	if len(sys.argv) == 1:
		parser.print_help()
		sys.exit(0)

	args = parser.parse_args()
	flags = filter(lambda kvpair: kvpair[1] == True, (vars(args).items()))

	print(list(flags))
	return

	ENV = create_environment(parse_config())


	def nuke(env, i):
		print("🔥  %s" % paint.gray("Nuking old builds..."))
		env['progress'].update(i)
		nuke(env['ROOT_DIR'], env['config'])

	def scaffold(env, i):
		print("🗄  %s" % paint.gray("Creating directories..."))
		env['progress'].update(i)
		scaffold(env['ROOT_DIR'], env['config'])

	def inline_local(env, i):
		print("💉  %s " % paint.gray("Inlining partials and globals..."))
		env['progress'].update(i)
		copy_locals(env['ROOT_DIR'], env['SOURCE_DIR'], env['DEST_DIR'])

	def inline_global(env, i):
		env['progress'].update(i)
		cmd = os.path.join(env['VELVEEVA_DIR'], "lib", "inject.py")
		for out in execute(["python3", cmd, env['ROOT_DIR'], env['GLOBALS_DIR'], env['DEST_DIR']]):
			print(out)

	def render_sass(env, i):
		print("💅  %s " % paint.gray("Compiling SASS..."))
		env['progress'].update(i)
		cmd = os.path.join(env['VELVEEVA_DIR'], "lib", "compile_sass.py")

		for out in execute(["python3", cmd, os.path.join(env['ROOT_DIR'],env['DEST_DIR'])]):
			print(out)

	def render_templates(env, i):
		print("📝  %s " % paint.gray("Rendering templates..."))
		env['progress'].update(i)
		cmd = os.path.join(env['VELVEEVA_DIR'], "lib", "render_templates.py")

		for out in execute(["python3", cmd, 
			os.path.join(env['ROOT_DIR'], env['SOURCE_DIR']), os.path.join(env['ROOT_DIR'],env['DEST_DIR']),
			os.path.join(env['ROOT_DIR'], env['TEMPLATES_DIR']),
			os.path.join(env['ROOT_DIR'], env['PARTIALS_DIR'])]):
			print(out)

	def take_screenshots(env, i):
		print("📸  %s " % paint.gray("Taking screenshots..."))
		env['progress'].update(i)
		cmd = os.path.join(env['VELVEEVA_DIR'], "lib", "screenshot.py")
		src = os.path.abspath(os.path.join(env['ROOT_DIR'],env['DEST_DIR']))
		cfg = os.path.abspath(os.path.join(env['ROOT_DIR'],env['CONFIG_FILE_NAME']))

		for out in execute(["python3", cmd, src, cfg]):
			print(out)

	def package_slides(env, i):
		print("📬  %s " % paint.gray("Packaging slides..."))
		env['progress'].update(i)
		cmd = os.path.join(env['VELVEEVA_DIR'], "lib", "package_slides.py")
		for out in execute(["python3", cmd, 
				os.path.join(env['ROOT_DIR'],env['DEST_DIR']), 
				os.path.join(env['ROOT_DIR'],env['DEST_DIR'],env['ZIPS_DIR'])]):
			print(out)

	def generate_ctls(env, i):
		print("⚒  %s " % paint.gray("Generating .ctl files..."))
		env['progress'].update(i)
		cmd = os.path.join(env['VELVEEVA_DIR'], "lib", "genctls.py")

		flags = ["python3"
					, cmd
					, "--root", env['ROOT_DIR']
					, "--src", os.path.abspath(os.path.join(env['ROOT_DIR'],env['DEST_DIR'],env['ZIPS_DIR']))
					, "--out", os.path.abspath(os.path.join(env['ROOT_DIR'],env['DEST_DIR'],env['CTLS_DIR']))
					, "--u", env['VEEVA_USERNAME']
					, "--pwd", env['VEEVA_PASSWORD']
				]

		if env.get('VEEVA_EMAIL', None) is not None: flags = flags + ["--email", env['VEEVA_EMAIL']]

		for out in execute(flags):
			print(out)

	def ftp_upload(env, i):
		print("🚀  %s " % paint.gray("Publishing to Veeva FTP server..."))
		env['progress'].update(i)
		
		cmd = os.path.join(env['VELVEEVA_DIR'], "lib", "publish.py")
		for out in execute(["python3", cmd
			, "--zip", os.path.abspath(os.path.join(env['ROOT_DIR'],env['DEST_DIR'],env['ZIPS_DIR']))
			, "--ctl", os.path.abspath(os.path.join(env['ROOT_DIR'],env['DEST_DIR'],env['CTLS_DIR']))
			, "--host", env['VEEVA_SERVER']
			, "--u", env['VEEVA_USERNAME']
			, "--pwd", env['VEEVA_PASSWORD'] ]):
			print(out)		

	### build planner ###
	def build_planner(flags):
		tasks = {
			"nuke": [nuke],
			"bake": [scaffold, inline_local, inline_global, render_sass, render_templates],
			"screenshots": [take_screenshots],
			"package": [package_slides],
			"controls": [generate_ctls],
			"publish": [ftp_upload],
			"relink": [],
			"veev2rel": [],
			"rel2veev": []
		}

		task_dependencies = {
			nuke: [None],
			scaffold: [None, nuke],
			inline_local: [scaffold],
			inline_global: [scaffold],
			render_sass: [inline_local, inline_global],
			render_templates: [inline_local, inline_global],
			take_screenshots: [render_sass, render_templates],
			package_slides: [render_sass, render_templates, take_screenshots],
			generate_ctls: [package_slides],
			ftp_upload: [generate_ctls]
		}

		## create dependency graph
		## figure out which tasks can be run in parallel at different stages in the graph
		## return a build plan

	def build_runner(build, env):

		print(banner())
		print("👉  %s 👈\n" % paint.bold.yellow(ENV['PROJECT_NAME']))

		try:
			with ProgressBar(max_value=11, widgets=[Bar(marker="🍕"),Percentage()], redirect_stdout=True) as progress:
		
				progress.update(11)

				
		except Exception as e:
			print(paint.bold.red("\n💩  there was an error:"))
			print(e)
			sys.exit(1)

		print(paint.bold.green("\n🍕  Yum!"))
	

if __name__ == '__main__':
	doScript()