#!/usr/bin/env python3
#import activate_venv

import glob
import os
import sys
import textwrap
import fnmatch
import pyparsing as pp
import re
import eco
import concurrent.futures

def load_html_files(dir):
	html_dict = {}

	html_files = glob.glob(os.path.join(dir,'*.htm*'))
	for file in html_files:
		with open(file, 'r') as f:
			html_dict[os.path.basename(file)] = f.read()

	return html_dict

def parse_header(file):
	src = ""
	with open(file) as f:
		src = f.read()

	config_reader = re.compile("^(?:---\n)(.*)(?:\n---\n)(.*)", flags=re.DOTALL)
	pieces = config_reader.match(src)

	if pieces is None:
		# no config found, return source
		return {"context": {}, "src": src}

	config = pieces.group(1)
	remaining = pieces.group(2)


	# pyparsing ignores newlines a whitespace by default
	pp.ParserElement.setDefaultWhitespaceChars("")
	ws = (pp.OneOrMore(" ")^pp.OneOrMore("\t")).suppress()
	eol = pp.OneOrMore(pp.ZeroOrMore("\r") + pp.OneOrMore("\n"))

	key = pp.Regex("[^0-9\s:]+")
	value = pp.Regex("[^\r\n]+")
	row = key + pp.ZeroOrMore(ws) + pp.Literal(":").suppress() + pp.ZeroOrMore(ws) + value

	# create the environment dict
	dict = {}
	matches = row.scanString(config)
	for match in matches:
		kv_pair = match[0]
		dict[kv_pair[0]] = kv_pair[1]

	return {"context": dict, "src": remaining}

def render_slide(file, templates, partials):
	header = parse_header(file)
	slide_src = header["src"]
	template_name = header.get("context", {}).get("template", None)
	template_src = templates.get(template_name, None)

	template_config = {"partial": partials}

	if template_src is not None:
		# bind to contents variable
		template_config["contents"] = slide_src
		eco_ctx = eco.context_for(template_src)
	else:
		eco_ctx = eco.context_for(slide_src)

	# merge with header context dictionary
	return eco_ctx.call("render", dict(template_config, **header["context"]))

def render_one(src, slide, dest, templates, partials, verbose=False):
	html_files = glob.glob(os.path.join(src, slide, "*.htm*"))

	if not os.path.exists(os.path.join(dest,slide)):
		os.makedirs(os.path.join(dest,slide))

	for file in html_files:
		if verbose: print("Rendering %s" % file)
		html_basename = os.path.basename(file)
		if verbose: print(os.path.join(dest,slide,html_basename))
		rendered = render_slide(file, templates, partials)

		html_path = os.path.join(dest,slide,html_basename)
		with open(html_path, 'w') as f:
			f.write(rendered)

def render_slides_sync(src, dest, templates_dir, partials_dir, verbose=True):
	if verbose: print("Loading templates...")
	templates = load_html_files(templates_dir)

	if verbose: print("Loading partials...")
	partials = load_html_files(partials_dir)


	slides = next(os.walk(src))[1] # (root, dirs, files)
	for slide in slides:
		render_one(src, slide, dest, templates, partials, verbose)
			
def render_slides_async(src, dest, templates_dir, partials_dir, verbose=True):
	if verbose: print("Loading templates...")
	templates = load_html_files(templates_dir)

	if verbose: print("Loading partials...")
	partials = load_html_files(partials_dir)

	slides = next(os.walk(src))[1] # (root, dirs, files)
	with concurrent.futures.ProcessPoolExecutor() as executor:
		futures = {executor.submit(render_one, src, slide, dest, templates, partials, verbose): slide for slide in slides}

		for future in concurrent.futures.as_completed(futures):
			try:
				data = future.result()
			except Exception as exec:
				raise exe
		

def runScript():
	VERBOSE = False
	args = sys.argv

	if "--verbose" in args:
		VERBOSE = True
		args.remove("--verbose")

	if len(args) < 5:
		banner = textwrap.dedent('''\
			 _   ________ _   ___________   _____ 
			| | / / __/ /| | / / __/ __| | / / _ |
			| |/ / _// /_| |/ / _// _/ | |/ / __ |
			|___/___/____|___/___/___/ |___/_/ |_|
			                                      
			~~~~~~~~~~ Template Renderer ~~~~~~~~~
			''')
		print(banner)
		print("USAGE: ")
		print("   %s [--verbose] source_folder dest_folder templates_dir partials_dir" % args[0])
		sys.exit(0)

	else:
		render_slides_sync(args[1], args[2], args[3], args[4], VERBOSE)

if __name__ == '__main__': runScript()