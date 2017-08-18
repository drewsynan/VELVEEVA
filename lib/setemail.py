#!/usr/bin/env python3
import activate_venv
import json, sys, os

from veevutils import CONFIG_FILENAME

def main():
	config = {}
	if os.path.exists(CONFIG_FILENAME):
		with open(CONFIG_FILENAME) as f:
			config = json.load(f)
	else:
		raise IOError(CONFIG_FILENAME + " does not exist")

	if len(sys.argv) < 2:
		# no email specified, prompt for one
		email = prompt("Veeva notification email? ").strip("\r").strip("\n")
		if email == '':
			raise RuntimeError("Please specify an email address")
	else:
		email = sys.argv[1]
		
	updated = config['VEEVA']['email'] = email;

	with open(CONFIG_FILENAME) as f:
		config = f.write(json.dumps(updated))

	return 0


if __name__ == "__main__": 
	try:
		sys.exit(main())
	except KeyboardInterrupt:
		sys.exit(1)
	except Exception as e:
		print(e, file=sys.stderr)
		sys.exit(1)