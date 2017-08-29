#!/usr/bin/env python3
import activate_venv

from veevutils import banner, is_slide, CONFIG_FILENAME
from prefix import parse_slide_folders

from selenium import webdriver
from contextlib import closing
from PIL import Image

import argparse
import concurrent.futures
import multiprocessing as mp
import re
import io
import json
import os
import shutil
import sys
import textwrap

def ss_(url, dest, sizes, filename, driver, verbose=False):
	BACKGROUND_COLOR = (255, 255, 255)

	def __snap(driver, w, h, fname, suffix=None):

		splitter = re.compile(r'([^.]+)(.+)')

		if suffix is None: 
			suffix = ""
		elif suffix == "[dimensions]":
			suffix = str(w) + "x" + str(h)

		if verbose: print(url + ": " + str(w)+"x"+str(h))

		try:
			driver.set_window_size(int(w), int(h))
			driver.get(url)

			pieces = list(splitter.search(fname).groups())
			new_fname = os.path.join(dest, pieces[0] + suffix + "".join(pieces[1:]))

			png = io.BytesIO(driver.get_screenshot_as_png())
			img = Image.open(png)
			cropped = img.resize((int(w), int(h)), Image.BILINEAR)

			bg = Image.new('RGB', cropped.size, BACKGROUND_COLOR)
			bg.paste(cropped, mask=cropped.split()[3])
		
			if not os.path.exists(new_fname): # don't override user provided thumbs
				bg.save(new_fname, 'jpeg')
		except Exception as e:
			raise e
	
	[__snap(driver, x['width'], x['height'], filename, x.get('suffix', None)) for x in sizes]

def ss_q(q, verbose=False):
	try:
		driver = webdriver.PhantomJS()

		while True:
			job = q.get()
			if job is None: break

			ss_(job[0], job[1], job[2], job[3], driver, verbose)
			q.task_done()

		driver.quit()
	
	except Exception as e:
		#empty the queue so it doesn't deadlock
		while True:
			job = q.get()
			if job is None: break

			q.task_done()
		
		raise e

def ss(url, dest, sizes, filename, verbose=False):
	driver = webdriver.PhantomJS()
	ss_(url, dest, sizes, filename, driver, verbose)
	driver.quit()

def ss_conc(configs, executor):
	procs = []

	for config in configs:
		job = [ss]
		job = job + config

		procs.append(executor.submit(*job))

	return procs

def gen_configs(urls, dests, templates, name_maker):
	for pair in zip(urls, dests):
		url = pair[0]
		dest = pair[1]
		yield [url, dest, templates, name_maker(url)]

def serialname(extension):
	num = -1

	def closure(url):
		nonlocal num
		num = num + 1
		return str(num) + extension

	return closure

def test_sync():
	ss('https://google.com', ".",
		[
			{'width': 1024, 'height': 768},
			{'width': 300, 'height': 300}
		], "test.png")

	ss('https://google.com', ".",
		[
			{'width': 1024, 'height': 768, 'suffix': "[dimensions]"},
			{'width': 300, 'height': 300, 'suffix': "--square"}
		], "test2.png")

def test_shared():
	with closing(webdriver.PhantomJS()) as d:
		ss_('https://google.com', ".",
			[
				{'width': 1024, 'height': 768},
				{'width': 300, 'height': 300}
			], "test.png", d)

		ss_('https://google.com', ".",
			[
				{'width': 1024, 'height': 768, 'suffix': "[dimensions]"},
				{'width': 300, 'height': 300, 'suffix': "--square"}
			], "test2.png", d)

def test_concurrent(configs, pool):
	c = [
		['https://google.com', ".", [
			{'width': 1024, 'height': 768},
			{'width': 300, 'height': 300, 'suffix': '-thumb'}
		], "test.png"]
		, ['http://bbc.co.uk', ".", [
			{'width': 1024, 'height': 768, 'suffix': "[dimensions]"},
			{'width': 300, 'height': 300, 'suffix': "--square"}
		], "test2.png"]

		]
	
	for config in c:
		pool.apply(ss, args=tuple(config), callback=None)
	pool.close()
	pool.join()

def load_ss_config(config_file):
	ss = json.load(open(config_file))['SS']
	configs = []

	for key in ss.keys():
		current_config = ss[key]
		current_config['suffix'] = current_config['name'].split(".")[0]
		configs.append(current_config)

	return configs

def local_slide_name(path):
	newname = os.path.splitext(os.path.basename(path))[0] + ".jpg"
	return newname

def take_screenshots_async(source_folder, config_path, verbose=False):
	sizes = load_ss_config(config_path)
	slides = parse_slide_folders(source_folder)

	dests = [slide[0] for slide in slides[0]]
	urls = [os.path.join(slide[0],slide[1]) for slide in slides[0]]

	shots = list(gen_configs(urls, dests, sizes, local_slide_name))

	q = mp.JoinableQueue()
	procs = []

	for i in range(mp.cpu_count()*2):
		p = mp.Process(target=ss_q, args=(q,verbose))
		procs.append(p)
		p.start()

	for item in shots:
		q.put(tuple(item))

	q.join()

	for i in range(mp.cpu_count()*2):
		q.put(None)

	for proc in procs: 
		if not proc.join():
			raise Exception("Error taking screenshots")

def fake_shared_assets(config_path, root_dir):
	if not os.path.exists(config_path): raise Exception('Config file not found!')
	
	with open(config_path) as f:
		config = json.load(f)

	dest_dir_name = os.path.relpath(config['MAIN']['output_dir'])
	globals_dir_name = os.path.relpath(config['MAIN']['globals_dir'])

	dest_path = os.path.join(root_dir, dest_dir_name)
	built_globals_path = os.path.join(root_dir, dest_dir_name, globals_dir_name)
	fake_shared_path = os.path.join(root_dir, dest_dir_name, "shared")
	fake_globals_path = os.path.join(fake_shared_path, globals_dir_name)

	# check to see if the globals dir exists inside the build dir
	if os.path.exists(built_globals_path):
		# if it does, make a 'shared' folder, and copy the globals inside of that
		if not os.path.exists(fake_shared_path): os.mkdir(fake_shared_path)
		try:
			shutil.copytree(built_globals_path, fake_globals_path)
		except Exception as e:
			# ignore it if it's already been created
			print(e, file=sys.stderr)

def cleanup_fake_shared_assets(config_path, root_dir):
	if not os.path.exists(config_path): raise Exception('Config file not found!')
	
	with open(config_path) as f:
		config = json.load(f)

	dest_dir_name = os.path.relpath(config['MAIN']['output_dir'])
	globals_dir_name = os.path.relpath(config['MAIN']['globals_dir'])

	dest_path = os.path.join(root_dir, dest_dir_name)
	built_globals_path = os.path.join(root_dir, dest_dir_name, globals_dir_name)
	fake_shared_path = os.path.join(root_dir, dest_dir_name, "shared")
	fake_globals_path = os.path.join(fake_shared_path, globals_dir_name)

	# check to see if a fake globals dir exists
	if os.path.exists(fake_globals_path):
		shutil.rmtree(fake_globals_path)

		#delete the 'shared' fake directory if it's empty (i.e. not used by the user)
		for dir_path, dir_names, files in os.walk(fake_shared_path):
			if not files and not dir_names:
				shutil.rmtree(dir_path)

def runScript():
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
		description = banner(subtitle="Screenshot Generator"))

	parser.add_argument("source", nargs=1, help="Source folder")
	parser.add_argument("config", nargs='?', help="Path to config file", default=CONFIG_FILENAME)
	parser.add_argument("--root", nargs=1, help="Project root folder", required=False)
	parser.add_argument("--verbose", action="store_true", help="Chatty Cathy", required=False)
	parser.add_argument("--shared-assets", action="store_true", help="Use Veeva shared assets", required=False)


	if len(sys.argv) == 1:
		parser.print_help()
		return 2
	
	args = parser.parse_args()
	VERBOSE = args.verbose

	# parse the root filder
	if args.root is not None:
		root_dir = args.root[0]
	else:
		root_dir = os.getcwd()

	# parse config filename
	if args.config is not None:
		config_file_name = args.config
	else:
		config_file_name = CONFIG_FILENAME

	#parse config file path
	config_path = os.path.join(root_dir, config_file_name)
	source_path = os.path.join(root_dir, args.source[0])

	# fake Veeva shared assets for the screenshots
	if args.shared_assets: fake_shared_assets(config_path, root_dir)

	take_screenshots_async(source_path, config_path, VERBOSE)

	if args.shared_assets: cleanup_fake_shared_assets(config_path, root_dir)

if __name__ == "__main__":
	sys.exit(runScript())
