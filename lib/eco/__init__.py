import re
import os
import six
import execjs
import coffeescript

EngineError = execjs.RuntimeError
CompilationError = execjs.ProgramError
bundled_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "eco.js")
version_ptn = re.compile(".+Eco Compiler (.*).*")


class Source(object):

    def __init__(self):
        self._path = ""
        self._contents = ""
        self._version = ""
        self._context = ""
        self._combined_contents = ""

    def path(self, path=None):
        if path:
            self._contents = self._version = self._context = None
        self._path = path or self._path or os.environ.get("ECO_SOURCE_PATH") or bundled_path
        return self._path

    @property
    def contents(self):
        self._contents = self._contents or open(self.path()).read()
        return self._contents

    @property
    def combined_contents(self):
        return ";\n".join([coffeescript.get_compiler_script(), self.contents])

    @property
    def version(self):
        self._version = self._version or version_ptn.search(self.contents).group(1)
        return self._version

    @property
    def context(self):
        self._context = self._context or execjs.compile(self.combined_contents)
        return self._context


source = Source()


def version():
    return source.version


def compile(template):
    template_ = template.read() if hasattr(template, "read") else template
    return source.context.call("eco.precompile", template_)


def context_for(template):
    return execjs.compile(six.u("var render = {0}").format(compile(template)))


def render(template, **locals_kw):
    return context_for(template).call("render", locals_kw)
