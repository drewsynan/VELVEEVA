#!/usr/bin/env python3
from lib import activate_venv
from lib.veevutils import banner
from painter import paint

import codecs, sys, os, glob, stat, subprocess, pty

def parseUtils():
	def isExecutable(f):
		return (os.stat(f)[stat.ST_MODE] & stat.S_IXUSR) > 0
	scripts = [util for util in glob.glob(os.path.join(UTILS_DIR, "*.py")) if isExecutable(util)]
	names = [os.path.splitext(os.path.basename(script))[0] for script in scripts]

	return sorted(names)


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

def exec_cmd(cmd, args=[]):
	call = [os.path.join(BASE_DIR, cmd)] + args
	process = subprocess.Popen([cmd] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	while True:
		try:
			out = process.stdout.read(1).decode('utf-8','replace')
		except KeyboardInterrupt:
			sys.stdout.write("\n")
			return 1

		if out == '' and process.poll() != None:
			for err in process.stderr.readlines():
				sys.stdout.write(err.decode('utf-8','replace'))
			sys.stderr.flush()
			break
		if out != '':
			sys.stdout.write(out)
			sys.stdout.flush()

	return process.returncode

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
		return 1
	elif util in utils:
		script = os.path.join(UTILS_DIR,util+".py")
		return exec_cmd(script, util_args)
	else:
		print(util + ' is not a recognized Velveeva util command')
		return 1


def dispatch(command_name, args):
	if COMMANDS.get(command_name, None) is not None:
		cmd = COMMANDS[command_name]['command']
		if cmd is None:
			return
		elif callable(cmd):
			cmd(args)
		else:
			return exec_cmd(os.path.join(BASE_DIR, cmd), args)


	else:
		print("'%s' is not a valid velveeva command" % command_name, file=sys.stderr)

def main():

	sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

	if len(sys.argv) < 2:
		print(banner(subtitle='An easier way to manage, maintain,\n and build Veeva iRep presentations'))
		usage()
		return 1
	else:
		return dispatch(sys.argv[1], sys.argv[2:])
	

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
	},
	'version': {
		'command': None,
		'usage': '',
		'help': 'velveeva-cli version info'
	}
}

if __name__ == '__main__':
	sys.exit(main())
