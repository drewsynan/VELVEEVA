#!/usr/bin/env python3
import activate_venv
import json, sys, os
from functools import reduce

from veevutils import CONFIG_FILENAME

def focus(acc, new_key):
	try:
		if type(acc) == list:
			focused = acc[int(new_key)]
		elif type(acc) == dict:
			focused = acc[new_key]
		else:
			raise TypeError("Cannot get subkey value for non object or array types")

	except KeyError:
		raise KeyError("Could not find key " + new_key)

	return focused

def main():
	config = {}
	if os.path.exists(CONFIG_FILENAME):
		with open(CONFIG_FILENAME) as f:
			config = json.load(f)
	else:
		raise IOError(CONFIG_FILENAME + " does not exist")

	if len(sys.argv) < 2:
		# no keys specified, just print out the whole config file
		print(config, file=sys.stdout)
	else:
		key_names = sys.argv[1].split(".")
		try:
			config_value = reduce(focus, key_names, config)
			print(config_value, file=sys.stdout)
		except KeyError:
			raise KeyError("Could not find key " + sys.argv[1] + " in " + CONFIG_FILENAME)

	return 0


if __name__ == "__main__": 
	try:
		sys.exit(main())
	except KeyboardInterrupt:
		sys.exit(1)
	except Exception as e:
		print(e, file=sys.stderr)
		sys.exit(1)