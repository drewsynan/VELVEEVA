#!/usr/bin/env python3
from lib import activate_venv
from lib.veevutils import banner
from lib import build

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
import networkx


def execute(command):
	popen = subprocess.Popen(command, bufsize=0, stdout=subprocess.PIPE, universal_newlines=True)
	stdout_lines = iter(popen.stdout.readline, "")
	for stdout_line in stdout_lines:
		yield stdout_line

	popen.stdout.close()
	returncode = popen.wait()
	if returncode != 0:
		raise subprocess.CalledProcessError(returncode, command)


def action(banner=""):
	def text_wrapper(f):
		def ann():
			if len(banner) > 0:
				print(banner)
				sys.stdout.flush()

		f.BANNER = banner
		f.announce = ann

		return f
	return text_wrapper


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
				
				full_base = os.path.abspath(os.path.join(root_dir,src))
				full_current = os.path.abspath(root)

				prefix = os.path.commonprefix([full_base, full_current])
				current_relative_folder = os.path.relpath(root,prefix)

				for file in files:
					if not os.path.splitext(os.path.basename(file))[0] == current_relative_folder:
						s = os.path.abspath(os.path.join(root,file))
						dest_dir = os.path.abspath(os.path.join(root_dir,dest,current_relative_folder))
						d = os.path.abspath(os.path.join(root_dir,dest,current_relative_folder,file))

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
	ENV['PREFLIGHT_HOOK']	= config.get('HOOKS',{}).get('pre', None)
	ENV['POSTFLIGHT_HOOK']	= config.get('HOOKS', {}).get('post', None)
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
	parser.add_argument("--scaffold",		action="store_true", help="Set up build and temp folders")
	parser.add_argument("--package",		action="store_true", help="Wrap it up [Selected when no options are given]")
	parser.add_argument("--publish", 		action="store_true", help="Ship it off to market")
	parser.add_argument("--relink", 		action="store_true", help="Make some href saussage (replace relative links with global and convert to veeva: protocol)")
	parser.add_argument("--rel2veev", 		action="store_true", help="Convert relative links to veeva: protocol")
	parser.add_argument("--screenshots",	action="store_true", help="Include Screenshots")
	parser.add_argument("--veev2rel",		action="store_true", help="Convert veeva: hrefs to relative links")
	parser.add_argument("--verbose",		action="store_true", help="Chatty Cathy")
	parser.add_argument("--notparallel", 	action="store_true", help="Only run things one after another")
	parser.add_argument("--watch",			action="store_true", help="Watch for changes and re-build on change")

	return parser

@action("🔥  %s" % paint.gray("Nuking old builds..."))
def ACTION_nuke(env, i):
	# env['progress'].update(i)
	nuke(env['ROOT_DIR'], env['config'])

@action("🗄  %s" % paint.gray("Creating directories..."))
def ACTION_scaffold(env, i):
	# env['progress'].update(i)
	scaffold(env['ROOT_DIR'], env['config'])

@action("💉  %s " % paint.gray("Inlining partials and globals..."))
def ACTION_inline_local(env, i):
	# env['progress'].update(i)
	copy_locals(env['ROOT_DIR'], env['SOURCE_DIR'], env['DEST_DIR'])

@action()
def ACTION_inline_global(env, i):
	# env['progress'].update(i)
	cmd = os.path.join(env['VELVEEVA_DIR'], "lib", "assets.py")
	for out in execute(["python3", cmd, "--root", env['ROOT_DIR'], env['GLOBALS_DIR'], env['DEST_DIR']]):
		print(out)

@action("💅  %s " % paint.gray("Compiling SASS..."))
def ACTION_render_sass(env, i):
	# env['progress'].update(i)
	cmd = os.path.join(env['VELVEEVA_DIR'], "lib", "styles.py")

	for out in execute(["python3", cmd, "--root", env['ROOT_DIR'], env['DEST_DIR'], "--remove"]):
		print(out)

@action("📝  %s " % paint.gray("Rendering templates..."))
def ACTION_render_templates(env, i):
	# env['progress'].update(i)
	cmd = os.path.join(env['VELVEEVA_DIR'], "lib", "templates.py")

	for out in execute(["python3", cmd, 
		os.path.join(env['ROOT_DIR'], env['SOURCE_DIR']), os.path.join(env['ROOT_DIR'],env['DEST_DIR']),
		os.path.join(env['ROOT_DIR'], env['TEMPLATES_DIR']),
		os.path.join(env['ROOT_DIR'], env['PARTIALS_DIR'])]):
		print(out)

@action("📸  %s " % paint.gray("Taking screenshots..."))
def ACTION_take_screenshots(env, i):
	# env['progress'].update(i)
	cmd = os.path.join(env['VELVEEVA_DIR'], "lib", "screenshots.py")
	root = env['ROOT_DIR']
	folder = env['DEST_DIR']
	config = env['CONFIG_FILE_NAME']

	for out in execute(["python3", cmd, "--root", root, folder, config]):
		print(out)

@action("📬  %s " % paint.gray("Packaging slides..."))
def ACTION_package_slides(env, i):
	# env['progress'].update(i)
	cmd = os.path.join(env['VELVEEVA_DIR'], "lib", "package.py")
	root = env['ROOT_DIR']
	source = env['DEST_DIR']
	zips = os.path.join(env['DEST_DIR'],env['ZIPS_DIR'])

	for out in execute(["python3", cmd, "--root", root, source, zips]):
		print(out)

@action("⚒  %s " % paint.gray("Generating .ctl files..."))
def ACTION_generate_ctls(env, i):
	# env['progress'].update(i)
	cmd = os.path.join(env['VELVEEVA_DIR'], "lib", "ctls.py")

	flags = ["python3"
				, cmd
				, "--root", env['ROOT_DIR']
				, "--u", env['VEEVA_USERNAME']
				, "--pwd", env['VEEVA_PASSWORD']
				, os.path.abspath(os.path.join(env['DEST_DIR'],env['ZIPS_DIR']))
				, os.path.abspath(os.path.join(env['DEST_DIR'],env['CTLS_DIR']))
			]

	if env.get('VEEVA_EMAIL', None) is not None: flags = flags + ["--email", env['VEEVA_EMAIL']]

	for out in execute(flags):
		print(out)

@action("🚀  %s " % paint.gray("Publishing to Veeva FTP server..."))
def ACTION_ftp_upload(env, i):
	# env['progress'].update(i)
	
	cmd = os.path.join(env['VELVEEVA_DIR'], "lib", "publish.py")
	for out in execute(["python3", cmd
		, "--zip", os.path.abspath(os.path.join(env['ROOT_DIR'],env['DEST_DIR'],env['ZIPS_DIR']))
		, "--ctl", os.path.abspath(os.path.join(env['ROOT_DIR'],env['DEST_DIR'],env['CTLS_DIR']))
		, "--host", env['VEEVA_SERVER']
		, "--u", env['VEEVA_USERNAME']
		, "--pwd", env['VEEVA_PASSWORD'] ]):
		print(out)	

def doScript():
	VERBOSE = False

	parser = create_parser()	
	
	if len(sys.argv) == 1:
		parser.print_help()
		sys.exit(0)

	args = parser.parse_args()
	flags = [x[0] for x in filter(lambda kvpair: kvpair[1] == True, (vars(args).items()))]

	ENV = create_environment(parse_config())	

	### build planner ###
	def build_planner(flags):
		idx = {
			"nuke": ACTION_nuke,
			"scaffold": ACTION_scaffold,
			"locals": ACTION_inline_local,
			"globals": ACTION_inline_global,
			"sass": ACTION_render_sass,
			"templates": ACTION_render_templates,
			"screenshots": ACTION_take_screenshots,
			"package": ACTION_package_slides,
			"controls": ACTION_generate_ctls,
			"publish": ACTION_ftp_upload
		}

		requires = {
			"scaffold": ["nuke"],
			"locals": ["scaffold"],
			"globals": ["scaffold"],
			"sass": ["locals", "globals"],
			"templates": ["locals", "globals"],
			"screenshots": ["sass", "templates"],
			"package": ["screenshots"],
			"controls": ["package"],
			"publish": ["controls"]
		}

		plans = {
			"nuke": ["nuke"],
			"scaffold": ["nuke", "scaffold", "locals"],
			"bake": ["scaffold", "locals", "globals", "sass", "templates"],
			"screenshots": ["screenshots"],
			"package": ["package"],
			"controls": ["controls"],
			"publish": ["publish"],
			"relink": [],
			"veev2rel": [],
			"rel2veev": []
		}

		def replace_with_function(plan):
			if type(plan) is list:
				return [replace_with_function(x) for x in plan]
			else:
				return idx.get(plan)

		selected_tasks = []
		for flag in flags:
			tasks = plans.get(flag, [])
			selected_tasks = selected_tasks + tasks

		unique_tasks = list(set(selected_tasks))

		constraints = [(task, requires.get(task, None)) for task in unique_tasks if requires.get(task, None) is not None]
		
		if len(constraints) > 0:
			depgraph = build.Depgraph(constraints)
		else:
			return [[[idx.get(flag)] for flag in flags]]

		build_plan = depgraph.build_plan()
		return replace_with_function(build_plan)

		# for each flag, loop up tasks and concat them together from the task list
		# filter out unique tasks
		# build the directed graph
		# figure out which tasks can be run in parallel at different stages in the graph (topological sorting)
		# return a build plan

	def run_build(build_plan, env):
		STEPS = len(build_plan)

		if env['PREFLIGHT_HOOK'] is not None: execute([ENV['PREFLIGHT_HOOK']])

		print(banner())
		print("👉  %s 👈\n" % paint.bold.yellow(ENV['PROJECT_NAME']))

		try:
			with concurrent.futures.ProcessPoolExecutor() as executor:
			# with ProgressBar(max_value=STEPS, 
			# 		widgets=[Bar(marker="🍕"),Percentage()], 
			# 		redirect_stdout=True) as progress, concurrent.futures.ProcessPoolExecutor() as executor:
				
				# env['progress'] = progress

				i = 0
				for step in build_plan:
					if len(step) == 0:
						i = i + 1
					elif len(step) == 1:
						func = step[0][0]
						func.announce()
						func(env, i)
						i = i + 1
					else:
						futures = []
						for func in step:
							action = func[0]
							action.announce()
							futures.append(executor.submit(action, env, i))

						synchronize_and_wait = [f.result() for f in futures]
						i = i + 1

				# progress.update(STEPS) # finish up

			if env['POSTFLIGHT_HOOK'] is not None: execute([ENV['POSTFLIGHT_HOOK']])
				
		except Exception as e:
			print(paint.bold.red("\n💩  there was an error:"))
			print(e)
			sys.exit(1)

		print(paint.bold.green("\n🍕  Yum!"))
	
	#print(flags)
	plan = build_planner(flags)
	#print(plan)
	#print(ENV)

	run_build(plan, ENV)

if __name__ == '__main__':
	doScript()