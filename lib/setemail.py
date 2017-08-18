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

	currentEmail = config['VEEVA']['email']

	if currentEmail:
		currentEmail = " [" + currentEmail + "]"

	if len(sys.argv) < 2:
		# no email specified, prompt for one
		email = input("Veeva notification email" + currentEmail + "? ").strip("\r").strip("\n")
		if email == '':
			return 0
	else:
		email = sys.argv[1]
		
	config['VEEVA']['email'] = email

	with open(CONFIG_FILENAME, 'w') as f:
		config = f.write(json.dumps(config))

	return 0


if __name__ == "__main__": 
	try:
		sys.exit(main())
	except KeyboardInterrupt:
		sys.exit(1)
	except Exception as e:
		print(e, file=sys.stderr)
		sys.exit(1)