#!/usr/bin/env python3
import json

import os
import sys
import textwrap

def string_parser(input, default):
	converted = str(input)
	if converted == '':
		return default
	else:
		return converted

def int_parser(input, default):
	try:
		converted = int(input)
		return converted
	except ValueError:
		return default

def promptRuleset(ruleset, configState):
	section_name = ruleset['key']
	prompts = ruleset['subkeys']

	configState[section_name] = {}

	def makequery(name, default):
		if str(default) != '':
			default = " [%s]" % str(default)

		return ("What is the %s%s? " % (name, default))

	for prompt in prompts:
		query = makequery(prompt['prompt'], prompt['default'])
		parsed = prompt['parser'](input(query), prompt['default'])

		configState[section_name][prompt['key']] = parsed

	return configState

def write_config(config, filename="VELVEEVA-config.json"):
	with open(filename, 'w') as f:
		f.write(json.dumps(config))

def runScript():
	main = {
		'key': 'MAIN',
		'subkeys' : [
			{
				'key' : 'name',
				'prompt': 'project name', 
				'default': 'untitled', 
				'parser': string_parser
			},
			{
				'key' : 'source_dir',
				'prompt':'source directory',
				'default': './src',
				'parser': string_parser
			},
			{	'key' : 'output_dir', 
				'prompt':'build directory',
				'default': './build',
				'parser': string_parser
			},
			{
				'key' : 'globals_dir',
				'prompt':'globals directory', 
				'default': './global', 
				'parser': string_parser},
			{
				'key' : 'templates_dir', 
				'prompt':'templates directory', 
				'default': './templates', 
				'parser': string_parser
			},
			{
				'key' : 'temp_dir',
				'prompt' : 'temp directory',
				'default' :'./tmp',
				'parser': string_parser
			},
			{
				'key' : 'partials_dir',
				'prompt': 'partials directory',
				'default': './partials',
				'parser': string_parser
			},
			{
				'key' : 'zips_dir',
				'prompt' : 'built zips sub-directory',
				'default' : '_zips',
				'parser' : string_parser
			},
			{
				'key' : 'ctls_dir',
				'prompt': 'control files sub-directory',
				'default' : "_ctls",
				'parser' : string_parser
			}
		]
	}

	ss_full = {
		'key' : 'full',
		'subkeys' : [
			{
				'key' : 'with',
				'prompt' : 'width',
				'default': 1024, 
				'parser': int_parser
			},
			{
				'key' : 'height',
				'prompt' : 'height', 
				'default': 768, 
				'parser': int_parser
			},
			{
				'key' : 'name',
				'prompt' : 'file suffix',
				'default' : '-full.jpg',
				'parser': string_parser 
			}
		]
	}

	ss_thumb = {
		'key' : 'thumb',
		'subkeys' : [
			{
				'key' : 'with',
				'prompt' : 'width',
				'default': 200, 
				'parser': int_parser
			},
			{
				'key' : 'height',
				'prompt' : 'height', 
				'default': 150, 
				'parser': int_parser
			},
			{
				'key' : 'name',
				'prompt' : 'file suffix',
				'default' : '-thumb.jpg',
				'parser': string_parser 
			}
		]
	}

	ss = {
		'key' : 'SS',
		'subkeys' : [ss_full, ss_thumb]
	}

	veeva = {
		'key': 'VEEVA',
		'subkeys': [
			{
				'key' : 'server',
				'prompt' : 'Veeva ftp server',
				'default' : '',
				'parser' : string_parser
			},
			{
				'key' : 'username',
				'prompt' : 'ftp username',
				'default' : '',
				'parser' : string_parser
			},
			{
				'key' : 'password',
				'prompt' : 'ftp password',
				'default' : '',
				'parser' : string_parser
			},
			{
				'key' : 'email',
				'prompt' : 'Veeva notification email',
				'default' : '',
				'parser' : string_parser	
			}
		]
	}
	
	banner = textwrap.dedent('''\
	 _   ________ _   ___________   _____ 
	| | / / __/ /| | / / __/ __| | / / _ |
	| |/ / _// /_| |/ / _// _/ | |/ / __ |
	|___/___/____|___/___/___/ |___/_/ |_|
	                                      
	~~~~~~~ New Project Generator ~~~~~~~~
	''')

	config = {}

	print(banner)
	
	print("\nGENERAL CONFIGURATION")
	print("---------------------")
	promptRuleset(main, config)

	print("\nSCREENSHOTS")
	print("-----------")
	ss = {}
	print("\nFull-Size Screenshots")
	promptRuleset(ss_full, ss)
	print("\nSlide Thumbnails")
	promptRuleset(ss_thumb, ss)
	config['SS'] = ss

	print("\nVEEVA DEPLOYMENT")
	print("----------------")
	promptRuleset(veeva, config)

	confirm = input("\nWrite config file [y]? ")
	if not (confirm.upper() == 'N' or confirm.upper == 'NO'):
		print("\nWriting VELVEEVA-config.json file...")
		write_config(config)

	print("Bye!")

if __name__ == "__main__": runScript()