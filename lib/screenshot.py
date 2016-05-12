#!/usr/bin/env python3
import activate_venv

from veevutils import banner

from selenium import webdriver
from contextlib import closing
from PIL import Image
from prefix import parse_slide_folders
import concurrent.futures
import multiprocessing as mp
import re
import io
import json
import os
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

		driver.set_window_size(int(h), int(w))
		driver.get(url)

		pieces = list(splitter.search(fname).groups())
		new_fname = os.path.join(dest, pieces[0] + suffix + "".join(pieces[1:]))

		png = io.BytesIO(driver.get_screenshot_as_png())
		img = Image.open(png)
		cropped = img.resize((int(w), int(h)), Image.BILINEAR)

		bg = Image.new('RGB', cropped.size, BACKGROUND_COLOR)
		bg.paste(cropped, mask=cropped.split()[3])
		
		bg.save(new_fname, 'jpeg')
	
	[__snap(driver, x['width'], x['height'], filename, x.get('suffix', None)) for x in sizes]

def ss_q(q, verbose=False):
	driver = webdriver.PhantomJS()

	while True:
		job = q.get()
		if job is None: break

		ss_(job[0], job[1], job[2], job[3], driver, verbose)
		q.task_done()

	driver.quit()


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

	dests = list(map(lambda pair: pair[0], slides[0]))
	urls = list(map(lambda pair: os.path.join(pair[0], pair[1]), slides[0]))

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

	for proc in procs: proc.join()

def runScript():
	VERBOSE = False
	args = sys.argv

	if "--verbose" in args:
		VERBOSE = True
		args.remove("--verbose")

	if len(args) < 3:
		print(banner(subtitle="Screenshot Generator"))
		print("USAGE: ")
		print("   %s [--verbose] source_folder path_to_config" % args[0])
		sys.exit(0)

	source_folder = args[1]
	config_path = args[2]

	take_screenshots_async(source_folder, config_path, VERBOSE)

if __name__ == "__main__":
	runScript()