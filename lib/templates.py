#!/usr/bin/env python3
import activate_venv

from veevutils import banner

import argparse
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

def render_slides(src, dest, templates_dir, partials_dir, verbose=True):
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
			except Exception as e:
				raise e
		

def runScript(ASYNC=False):
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
		description = banner(subtitle="Template Renderer"))

	parser.add_argument("source", nargs=1, help="Source folder")
	parser.add_argument("destination", nargs=1, help="Destination folder")
	parser.add_argument("templates", nargs=1, help="Templates folder")
	parser.add_argument("partials", nargs=1, help="Partials folder")
	parser.add_argument("--notparallel", action="store_true", help="Run without concurrency")
	parser.add_argument("--root", nargs=1, help="Project root folder", required=False)
	parser.add_argument("--verbose", action="store_true", help="Chatty Cathy", required=False)

	if len(sys.argv) == 1:
		parser.print_help()
		return 2
	else:
		args = parser.parse_args()

		VERBOSE = args.verbose
		ASYNC = (not args.notparallel)

		SOURCE = args.source[0]
		DEST = args.destination[0]
		TEMPS = args.templates[0]
		PARTS = args.partials[0]

		if args.root is not None:
			ROOT = args.root[0]
			SOURCE = os.path.join(ROOT,SOURCE)
			DEST = os.path.join(ROOT,DEST)
			TEMPS = os.path.join(ROOT,TEMPS)
			PARTS = os.path.join(ROOT,PARTS)


		if ASYNC:
			render_slides_async(SOURCE, DEST, TEMPS, PARTS, VERBOSE)
		else:
			render_slides(SOURCE, DEST, TEMPS, PARTS, VERBOSE)

if __name__ == '__main__': 
	sys.exit(runScript())