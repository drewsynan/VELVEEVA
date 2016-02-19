#!/usr/bin/env python3
import os

def activate():
	VENV_NAME = "velvenv"
	VENV_ACTIVATE = os.path.join("bin", "activate_this.py")

	lib_path = os.path.dirname(os.path.abspath(__file__))
	activate_this_file = os.path.join(lib_path, VENV_NAME, VENV_ACTIVATE)

	with open(activate_this_file) as f:
		code = compile(f.read(), activate_this_file, "exec")
		exec(code, dict(__file__=activate_this_file))

try:
	activate()
except FileNotFoundError:
	print("Could not activate venv ... ! Falling back to local imports")