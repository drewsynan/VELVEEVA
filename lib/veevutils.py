import textwrap
from painter import paint
import math

__all__ = ['banner']

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