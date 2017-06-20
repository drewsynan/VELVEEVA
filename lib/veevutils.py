import textwrap
from painter import paint
import collections
import math
import os
import zipfile
import re
import git
import glob
import shutil
import json
from pymonad import *
import uuid

paint.enabled = True

VALID_SLIDE_EXTENSIONS = ['.html', '.htm', '.pdf', '.jpg', '.jpeg', '.mp4']
CONFIG_FILENAME = "VELVEEVA-config.json"

def get_extension_regex(exts=VALID_SLIDE_EXTENSIONS):
	return "(%s)" % "|".join(exts)

def get_path_regex(exts=VALID_SLIDE_EXTENSIONS, slide_name=None):
	vals = {
		'sep': '/',
		'ext_regex': "|".join(exts)
	}

	if slide_name is None: 
		vals["slide_name"] = "[^%s]+" % vals["sep"]
	else:
		vals["slide_name"] = slide_name

	return "(.*)(?P<slide_name>%(slide_name)s)%(sep)s(?P=slide_name)(%(ext_regex)s)" % vals

def parse_slide_path(p, slide_name=None):
	SlidePath = collections.namedtuple('SlidePath', ['parent_path', 'slide_name', 'extension'])
	matcher = re.compile(get_path_regex(slide_name=slide_name)).match(p)

	if matcher is None: 
		return None
	else:
		return SlidePath(matcher.group(1), matcher.group(2), matcher.group(3))


def get_veeva_command_regex(command_name=None, command_args=None):
	vals = {}
	if command_name is None:
		vals['command_name'] = "[^(]+"
	else:
		vals['command_name'] = command_name

	if command_args is None:
		vals['command_args'] = ".*"
	else:
		vals['command_args'] = command_args

	return "^veeva:(?P<command_name>%(command_name)s)\((%(command_args)s)\)" % vals

def get_javascript_regex(function_name=None, function_args=None, namespace=None):
	vals = {}
	if namespace is None:
		vals['namespace'] = ''
	else:
		vals['namespace'] = namespace

	if function_name is None:
		vals['function_name'] = "[^(]+"
	else:
		vals['function_name'] = function_name

	if function_args is None:
		vals['function_args'] = ".*"
	else:
		if type(function_args) is list:
			vals['function_args'] = ",".join(function_args)
		else:
			vals['function_args'] = function_args

	return "^(?:javascript:)?(%(namespace)s)?(?:[.]*)?(?P<function_name>%(function_name)s)\((%(function_args)s)\)" % vals

def get_veeva_slide_regex(command_name=None, slide_name=''):
	return get_veeva_command_regex(command_name=command_name, command_args=slide_name+".zip")

def parse_veeva_href(href, command_name=None, command_args=None):
	VeevaCommand = collections.namedtuple('VeevaCommand', ['command_name', 'command_args'])
	matcher = re.compile(get_veeva_command_regex(command_name=command_name, command_args=command_args)).match(href)

	if matcher is None:
		return None
	else:
		return VeevaCommand(matcher.group(1), matcher.group(2))

def parse_veeva_onclick(href, command_name=None, command_args=None, namespace="com.veeva.clm"):
	VeevaCommand = collections.namedtuple('VeevaCommand', ['command_name', 'command_args', 'namespace'])
	matcher = re.compile(get_javascript_regex(namespace=namespace)).match(href)

	def parse_args(arg_string):

		pass

	if matcher is None:
		return None
	else:
		unique = str(uuid.uuid1())
		func_name = matcher.group(2)
		func_args = json.loads("[%s]" % matcher.group(3).replace("\"", unique).replace("'", "\"").replace(unique, "'")) #wrong wrong wrong wrong, but ok for now
		func_namespace = matcher.group(1)

		return VeevaCommand(func_name, [arg for arg in func_args if arg != ''], func_namespace)

def search_for_repo_path(current_path, last_path=None):
	current_path = os.path.abspath(current_path)
	if current_path == last_path: return None # we've reached the top of the directory tree

	if git.repo.fun.is_git_dir(os.path.join(current_path,".git")):
		return current_path
	else:
		return search_for_repo_path(os.path.dirname(current_path), last_path=current_path)

def is_inside_git_repo(p):
	return search_for_repo_path(os.path.abspath(p)) is not None

def safe_rename(old, new):
	GIT = is_inside_git_repo(old)
	
	if GIT:
		repo = git.Git(search_for_repo_path(old))
		try:
			repo.mv(old,new)
			repo.add(new)
		except git.GitCommandError as e:
			if e.status == 128: # empty directory, so it's not tracked by git
				os.rename(old, new)
			else:
				raise e
	else:
		os.rename(old, new)

def safe_delete(p):
	GIT = is_inside_git_repo(p)

	if GIT:
		repo = git.Git(search_for_repo_path(p))
		try:
			repo.execute(['rm', '-r', p])
		except git.GitCommandError as e:
			return e
	else:
		if os.path.isdir(p):
			shutil.rmtree(p)
		else:
			os.remove(p)

def parse_slide(folder_path):
	EXTENSION_REGEX = get_extension_regex(VALID_SLIDE_EXTENSIONS)
	PATH_REGEX = "(?:.*%(slide_name)s%(os_sep)s)((?:%(slide_name)s|index)%(extension_regex)s)$"
	Result = collections.namedtuple('Result', ['full_path', 'extension'])

	def is_zip(f):
		return zipfile.is_zipfile(f)

	if not os.path.exists(folder_path):
		raise IOError("The path '%s' does not exist" % folder_path)
	if not os.path.isdir(folder_path) and not is_zip(folder_path):
		raise TypeError("The path '%s' does not refer to a directory or to a zip file" % folder_path)


	base_name = os.path.basename(folder_path)

	if is_zip(folder_path):
		slide_name = os.path.splitext(base_name)[0]
		pattern = PATH_REGEX % {'slide_name': slide_name, 'extension_regex': EXTENSION_REGEX, 'os_sep': os.sep}
		matcher = re.compile(pattern)

		with zipfile.ZipFile(folder_path, 'r') as z:
			files_in_zip = z.namelist()
			files_sharing_parent_name = []

			for file in files_in_zip:
				match = matcher.match(file)
				if match is not None:
					results_tuple = Result(match.group(0), match.group(2))
					files_sharing_parent_name.append(results_tuple)
			if len(files_sharing_parent_name) > 0:
				return files_sharing_parent_name[0]
			else:
				return None
	else:
		slide_name = os.path.basename(folder_path)
		pattern = PATH_REGEX % {'slide_name': slide_name, 'extension_regex': EXTENSION_REGEX, 'os_sep': os.sep}
		matcher = re.compile(pattern)

		files_sharing_parent_name = []
		root_1, dirs_1, files_1 = next(os.walk(folder_path))

		for file in files_1:
			file_path = os.path.join(root_1, file)

			if matcher.match(file_path) is not None:
				match = matcher.match(file_path)
				result_tuple = Result(match.group(0), match.group(2))
				files_sharing_parent_name.append(result_tuple)

		if len(files_sharing_parent_name) > 0:
			return files_sharing_parent_name[0]
		else:
			return None

def index_file_rename(slide_path):
	Rename = collections.namedtuple('Rename', ['old', 'new'])
	matcher = re.compile('(.*)/(?P<slide_name>[^/]+)/index(.htm|.html|.pdf|.jpg|.jpeg|.mp4)')
	matches = matcher.match(slide_path)

	if matches is not None:
		old_path = matches.group(0)
		new_path = matches.group(2) + matches.group(3)
		return Rename(old_path, new_path)
	else:
		return None

def is_slide(slide_path):
	return parse_slide(slide_path) is not None

def get_slides_in_folder(folder_path):
	root_1, dirs_1, files_1 = next(os.walk(folder_path))
	folders = [os.path.join(root_1,subdir) for subdir in dirs_1]
	slides = []
	for d in dirs_1:
		if is_slide(os.path.join(root_1,d)):
			slides.append(d)
	return slides

def parse_slide_name_from_href(href):
	veeva_matcher = re.compile(get_veeva_slide_regex('gotoSlide'))
	path_matcher = re.compile(get_path_regex())

	matchers = [veeva_matcher.match(href), path_matcher.match(href)]

	for matcher in matchers:
		if matcher is not None:
			return matcher.group(2) # (parent_path, slide_name, extension)

	# nothing!?
	return None

@curry
def veeva_composer(prefix, command, args):
	if args is None: args = []
	if type(args) is not list: args = [args]

	if prefix is None: prefix = ''

	return prefix + command + "(" + ",".join(args) + (")")

@curry
def path_composer(parent_path, slide_name, extension):
	if parent_path is None: parent_path = ''

	if len(parent_path > 0):
		if parent_path[-1] != "/": parent_path = parent_path + "/"

	return parent_path + slide_name + "/" + slide_name + extension

def identity_composer(*args):
	return args

def banner(type="normal",subtitle=None):
	WIDTH_IN_CHARS = 38
	LINE_FILLER = "~"

	def format_subtitle(subtitle):
		sub_length = len(subtitle) + 2
		is_odd = (sub_length % 2) > 0

		left = math.floor(0.5*(WIDTH_IN_CHARS - sub_length))

		if is_odd:
			right = math.ceil(0.5*(WIDTH_IN_CHARS - sub_length))
		else:
			right = math.floor(0.5*(WIDTH_IN_CHARS - sub_length))

		if left < 0: left = 0
		if right < 0: right = 0

		substring = LINE_FILLER*left + ' ' + subtitle + ' ' + LINE_FILLER*right

		return substring

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

	if subtitle is not None:
		MSG = MSG + "\n" + format_subtitle(subtitle) + "\n"

	return types[type](MSG)
