import textwrap
from painter import paint
import math
import os
import zipfile
import re
import git
import glob
import shutil

VALID_SLIDE_EXTENSIONS = ['.htm', '.html', '.pdf', '.jpg', '.jpeg', '.mp4']

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
	FORMAT_EXTENSIONS = ['.html', '.htm', '.jpg', '.pdf', '.mp4']
	EXTENSION_REGEX = "(%s)" % "|".join(FORMAT_EXTENSIONS)
	PATH_REGEX = "(?:.*%(slide_name)s%(os_sep)s)(%(slide_name)s%(extension_regex)s)$"

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
					results_tuple = (match.group(0), match.group(2))
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
				result_tuple = (match.group(0), match.group(2))
				files_sharing_parent_name.append(result_tuple)

		if len(files_sharing_parent_name) > 0:
			return files_sharing_parent_name[0]
		else:
			return None

def is_slide(slide_path):
	return parse_slide(slide_path) is not None

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