#!/usr/bin/env python3
from lib import activate_venv
from lib.veevutils import banner
from painter import paint

import sys, os, glob, stat, subprocess

def parseUtils():
	def isExecutable(f):
		return (os.stat(f)[stat.ST_MODE] & stat.S_IXUSR) > 0
	scripts = [util for util in glob.glob(os.path.join(UTILS_DIR, "*.py")) if isExecutable(util)]
	names = [os.path.splitext(os.path.basename(script))[0] for script in scripts]

	return names


def indented(message):
	print("     " + message)

def usage():
	def pad(name):
		return ' ' * (10 - len(name))

	print("SYNPOSIS")
	for command in sorted(COMMANDS):
		indented(PROGNAME + ' ' + command + ' ' + COMMANDS[command]['usage'])

	print("\nDESCRIPTION")
	indented("The combined cli utility for Velveeva")
	indented("The following options are available\n\n")

	for command in sorted(COMMANDS):
		indented(PROGNAME + ' ' + command + pad(command) + COMMANDS[command]['help'])



def util_help():
	print("UTILS")
	indented("(For more information use: velveeva util util_name --help)\n")

	for util in parseUtils():
		indented(PROGNAME + " util " + util)

def help(args):
	print(banner())
	usage()

def exec_util(args):
	if not args:
		print(banner())
		util_help()
		return 1

	util = args[0]
	util_args = args[1:]
	utils = parseUtils()

	if util is None:
		print(banner())
		util_help()
	elif util in utils:
		script = os.path.join(UTILS_DIR,util+".py")
		call = [script] + util_args
		sys.exit(subprocess.call(' '.join(call), shell=True))

	else:
		print(util + ' is not a recognized Velveeva util command')
		print(banner())
		util_help()


def dispatch(command_name, args):
	if COMMANDS.get(command_name, None) is not None:
		cmd = COMMANDS[command_name]['command']
		if cmd is None:
			return
		elif callable(cmd):
			cmd(args)
		else:
			call = [os.path.join(BASE_DIR, cmd)] + args
			sys.exit(subprocess.call(' '.join(call), shell=True))
	else:
		print("'%s' is not a valid velveeva command" % command_name, file=sys.stderr)

def main():
	if len(sys.argv) < 2:
		print(banner(subtitle='An easier way to manage, maintain,\n and build Veeva iRep presentations'))
		usage()
	else:
		dispatch(sys.argv[1], sys.argv[2:])
	

PROGNAME = 'velveeva'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UTILS_DIR = os.path.join(BASE_DIR,'lib')
COMMANDS = {
	'go': {
		'command': './go.py',
		'usage': '[options]',
		'help': 'build the project. See go --help for more info'
	},
	'init': {
		'command': './init',
		'usage': '',
		'help': 'initialize the wizard to create a new project'
	},
	'util': {
		'command': exec_util,
		'usage': 'utilname [options]',
		'help': 'execute a utility script'
	},
	'update': { # gets intercepted by the cli wrapper
		'command': None,
		'usage': '',
		'help': 'update to the latest VELVEEVA-cli utility docker image'
	},
	'help': {
		'command': help,
		'usage': '',
		'help': 'display this message'
	}
}

if __name__ == '__main__':
	main()
