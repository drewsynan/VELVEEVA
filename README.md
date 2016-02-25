# VELVEEVA
An easier way to manage, maintain, and build Veeva iRep presentations

## Features
* Automatic screenshot and zip file generation
* Support for static asset inlining
* Template and partial system (Embedded CoffeeScript)
* SASS support baked in
* Dev environment with re-build on change watcher
* Convert relative links to veeva: protocol links on the fly (both during dev and for a final build)
* Convert veeva: links back to relative links on the fly
* Tooling rename slides and automatically change all internal references
* Integrated slide uploading to iRep FTP server

## Requirements
* [ImageMagick](http://www.imagemagick.org/script/download.php)
* [Node.js (12+)](https://nodejs.org/en/download/) **IMPORTANT: don't use homebrew-installed node.js on OS-X**
* [Phantomjs](http://phantomjs.org/download.html)
* [Python (3.5+) with pip](https://www.python.org/downloads/)
* virtualenv (install using `pip install virtualenv`)

If installing on **OS-X**
* Xcode command line tools

If installing on **Linux**
* libxml2-dev headers
* libxslt-dev headers

## Creating a new project
In an empty folder (or empty git repo), run
```bash
git clone https://github.com/gacomm/VELVEEVA.git && VELVEEVA/install && VELVEEVA/init
```
This will install the required components for VELVEEVA, and launch a wizard to create a new project.

## Directories
* |-`src` **source files for each slide**. Create a new subdirectory for each Veeva slide. There must be one file inside the slide that has the same name as its enclosing folder (for example a slide named 01_intro must have a file called 01_intro.html or 01_intro.jpg (for image slides) to be a valid Veeva slide)
* |-`globals` **static assets to be included in all slides**. Files and folders here will be copied to the built slide folders. If a folder already exists in the local slide folder, its contents will be merged with the global folder.
* |-`templates` **location of slide templates**. Right now VELVEEVA only supports using eco (embedded coffee script) templates. There are plans to change this in the future. Note that templates are not required to compile and package slides
* |-`partials` **html snippet location for templates**
* |-`build` **output folder** (It's recommended that you add this folder along with `tmp` to your `.gitignore` file)
* |-`tmp` **temporary folder** (It's recommended that you add this folder along with `build` to your `.gitignore` file)

## Building a project
To build a project (including rendering any templates, compiling SASS, taking screenshots, and zipping the results) run
```bash
$ VELVEEVA/go
```
from the project root directory. By default, the built files are created in `build/_zips`. Under most circumstances, this is sufficient. However, for more advanced building options run 
```bash
$ VELVEEVA/go --help
```
to see a list of configuration options.

## Publishing slides
If you entered your iRep FTP server login information in the setup phase, VELVEEVA can automatically generate any necessary control files and upload them to the server for you. To publish files, first run 
```bash
$ VELVEEVA/go
```
to make the slides, and then
```bash
$ VELVEEVA/go --nobake --controls --publishonly
```
to upload files. To upload with more progress and status information, you can use the command
```bash
$ VELVEEVA/go --nobake --controls --publishonly --verbose
```
# Development environment
To launch the quick-building development (no packaging or screenshots, etc) environment with a file watcher, run
```bash
$ VELVEEVA/go --dev
```
(note that this is the same as running `VELVEEVA/go --clean --watch --veev2rel`)
The development environment automatically resolves veeva:() urls to their relative counterparts, to make in-browser testing easier. (No simulator required! Hooray!)

If you would prefer to develop using relative urls, and only later convert them to veeva: protocol links, omit the `--veev2rel` flag when developing, and build using the `--relink` flag.

# Advanced Topics
## Prefixing slide names
Since each slide must have a unique name on the Veeva server, it is often necessary to rename slides with a prefix or suffix to ensure uniqueness if two versions of a key message must exist simeltaneously. VELVEEVA provides tooling to make this process eaiser
## Renaming slides, and relinking slide references
## Generating enclosing slide folders
## Taking Screenshots
## Generating FTP Control files
## Converting PDF Slides to JPEG slides
## Build scripts
