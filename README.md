# VELVEEVA
An easier way to manage, maintain, and build Veeva iRep presentations

## Features
* Automatic screenshot, thumbnail, and zip file generation
* Support for static asset inlining
* Template and partial system (Embedded CoffeeScript)
* SASS compilation
* Dev environment with re-build on change watcher
* Convert relative links to veeva: protocol links on the fly (both during dev and for a final build)
* Convert veeva: links back to relative links on the fly
* Tooling rename slides and automatically change all internal references
* Automatic iRep control file generator
* Smart metadata extraction from HTML (using <meta content="veeva_title"> etc tags) or XMP data from PDF and JPEG files to easily maintain slide titles and descriptions within the source files
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
project-root$ VELVEEVA/go
```
from the project root directory. By default, the built files are created in `build/_zips`. Under most circumstances, this is sufficient. However, for more advanced building options run 
```bash
project-root$ VELVEEVA/go --help
```
to see a list of configuration options.

## Publishing slides
If you have configured your iRep FTP server login information, either in the setup phase, or by later editing the `VELVEEVA-config.json` file in the project's root directory, VELVEEVA can automatically generate any necessary control files and upload them to the server for you. To publish files, first run 
```bash
project-root$ VELVEEVA/go
```
to make the slides, and then
```bash
project-root$ VELVEEVA/go --nobake --controls --publishonly
```
to upload files. To upload with more progress and status information, you can use the command
```bash
project-root$ VELVEEVA/go --nobake --controls --publishonly --verbose
```
# Development environment
To launch the quick-building development (no packaging or screenshots, etc) environment with a file watcher, run
```bash
project-root$ VELVEEVA/go --dev
```
(note that this is the same as running `VELVEEVA/go --clean --watch --veev2rel`)
The development environment automatically resolves veeva:() urls to their relative counterparts, to make in-browser testing easier. (No simulator required! Hooray!)

If you would prefer to develop using relative urls, and only later convert them to veeva: protocol links, omit the `--veev2rel` flag when developing, and build using the `--relink` flag.

# Advanced Topics
## Prefixing slide names
Since each slide must have a unique name on the Veeva server, it is often necessary to rename slides with a prefix or suffix to ensure uniqueness if two versions of a key message must exist simeltaneously. VELVEEVA provides tooling (`prefix.py`) to make this process eaiser. The tool works by renaming slide folders, and the internal slide file, and then changing any internal references in any of the slides in the folder specified to reflect the new name. Because the prefixing tool only works on built (but not zipped files) first run the build command (making sure to have resolved any relative links to veeva: links). For example, to prefix a presentation with **my_specific_prefix_**, it would look something like this
```bash
project-root$ VELVEEVA/go --clean --screenshots
project-root$ VELVEEVA/lib/prefix.py my_specific_prefix_ build
project-root$ VELVEEVA/go --packageonly
(etc)
```
For further information, run `VELVEEVA/lib/prefix.py --help`.

## Renaming slides, and relinking slide references
For more fine-grained control over the renaming process, VELVEEVA provides a re-linking utility (`relink.py`). This utility allows you to rename one slide at a time (and change all references from the old name to the new name in a folder specified). For example, to rename the source files of slide `01_something_stupid` to `index` (and change all references within `src` to point to `index` and not `01_something_stupid`) the command would look something like
```bash
project-root$ VELVEEVA/lib/relink.py --mv 01_something_stupid index src
```
To change references in only the built version of the presentation, first build without packaging (since the utility can't read zip files), and point it at the `build` directory.

For further information, run `VELVEEVA/lib/relink.py --help`
## Generating enclosing slide folders
Sometimes it's useful to be able to create the surrounding folder around the slide file (in the case of JPEG or PDF slides). VELVEEVA has a utility (`make_enclosing_folders.py`) to quickly do this.

The utility takes a path and an optional wild-card filter, and creates a folder with the same name (minus the extension) around the files it finds. For example, to create slide folders around all pdf files in the folder `example`:
```bash
project-root$ VELVEEVA/lib/make_enclosing_folders.py example "*.pdf"
```
(Note the quotes around the wild-card string... this is used to keep bash from interpreting '*' as a special character)
## Taking Screenshots
The default screenshot dimensions and names are configured at setup time, but can be altered later by editing the `VELVEEVA-config.json` file. Additional sizes and names may be specified, and a separate screenshotting tool (`screenshot.py`) is also provided. To use the screenshotting tool, specify a folder containing the slides to screenshot, and the path to the `VELVEEVA-config.json` file with screenshot size definition.
```bash
project-root$ VELVEEVA/lib/screenshot.py build VELVEEVA-config.json
```
## Generating FTP Control files
The FTP control file generator will only work on build (and zipped) slides. It can either be run as with the `--controls` flag when building, or using the `--controlsonly` flag on already-built slides. The generator pulls the FTP user name and server information from the `VELVEEVA-config.json` file, and extracts the title and description fields from the slide files.
* For html slides, the generator reads the contents of `<meta name="veeva_title">` and `<meta name="veeva_description">`
* For pdf slides, the generator reads the title and subject fields of the xmp metadata (editible within Acrobat Pro or Adobe Bridge)
* For jpeg slides, the generator reads the title and description fields of the xmp metadata (editible within Photoshop or Adobe Bridge)
If no metadata is found, the title and description fields are omitted altogether from the generated control files.

Control files can also be generated on arbitrary folders of zip files using the `genctls.py` utility. For example, to generate control files for all zips within the `arbitrary_zips` folder:
```bash
project-root$ VELVEEVA/lib/genctls.py ./arbitrary_zips ./out_folder_for_ctls --u username --pwd password --email contactemail
```
## Build scripts
Although VELVEEVA currently has a lot of useful pieces, it is likely that you'll still want to create a basic build script to automate building, renaming, packaging, etc. of the slides. Here's an example of an actual build script below, that gives a feel for this process
```bash
#!/bin/bash

# build the slides and generate screenshots
./VELVEEVA/go --screenshots --clean

# prefix the built slides
./VELVEEVA/lib/prefix.py Digital_Sales_Aid_2016_ build

# rename specific slides that aren't currently handled by VELVEEVA
./VELVEEVA/lib/relink.py --mv video Digital_Sales_Aid_2016_video build
./VELVEEVA/lib/relink.py --mv pdf_gdufa Digital_Sales_Aid_2016_pdf_gdufa build
./VELVEEVA/lib/relink.py --mv pdf_isb Digital_Sales_Aid_2016_pdf_isb build
./VELVEEVA/lib/relink.py --mv pdf_barcode Digital_Sales_Aid_2016_pdf_barcode build
./VELVEEVA/lib/relink.py --mv pdf_value Digital_Sales_Aid_2016_pdf_value build

# package the slides after the renames have been completed
./VELVEEVA/go --packageonly

# move any already zipped files that were just moved from src to the build directory to the final zips folder
cp ./build/*.zip ./build/_zips

# generate controls files based on the _zips directory
./VELVEEVA/go --controlsonly

# copy the _zips directory to a named folder
cp -r ./build/_zips ./build/Digital_Sales_Aid_2016

# combine all zips into one file
zip -r ./build/Digital_Sales_Aid_2016.zip ./build/Digital_Sales_Aid_2016
```
