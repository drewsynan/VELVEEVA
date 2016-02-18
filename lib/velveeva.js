module.exports = Velveeva;

function Velveeva(configRecipe) {
  var CONFIG = {
    MAIN: {},
    ROOT_DIR: process.cwd(),
    VEEVA: {}
  };

  this.config = CONFIG;

  CONFIG["FLAGS"] = {
    BAKE: true,
    CONTROLS: false,
    VERBOSE: false,
    DEV: false,
    RELINK: false,
    WATCH: false,
    PACKAGE: false,
    PUBLISH: false,
    SCREENSHOTS: false,
    CLEAN: false,
    VEEV2REL: false
  };

  var Metalsmith = require('metalsmith'),
    collections = require('metalsmith-collections'),
    ignore  = require('metalsmith-ignore'),
    templates  = require('metalsmith-templates'),
    partial = require('metalsmith-partial'),
    sass = require('metalsmith-sass'),
    assets = require('./assets-recursive.js');

  var chalk = require('chalk'),
    fs = require('graceful-fs'),
    path = require('path'),
    Q = require('q'),
    rimraf = require('rimraf'),
    mkdirp = require('mkdirp'),
    ___ = require('lodash');

  var configRecipe = configRecipe || {};

  CONFIG.MAIN.ASSETS = configRecipe.MAIN.globals_dir || "./global_includes";
  CONFIG.MAIN.DEST = configRecipe.MAIN.output_dir || "./build";
  CONFIG.MAIN.PARTIALS = configRecipe.MAIN.partials_dir || "./partials/sections";
  CONFIG.MAIN.SOURCE = configRecipe.MAIN.source_dir || "./src";
  CONFIG.MAIN.TEMP = configRecipe.MAIN.temp_dir || "./temp";
  CONFIG.MAIN.TEMPLATES = configRecipe.MAIN.templates_dir || "./partials/full_templates";
  CONFIG.MAIN.ZIPS = configRecipe.MAIN.zips_dir || "_zips";
  CONFIG.MAIN.CTLS = configRecipe.MAIN.ctls_dir || "_ctls";

  CONFIG.VEEVA.USERNAME = configRecipe.VEEVA.username;
  CONFIG.VEEVA.PASSWORD = configRecipe.VEEVA.password;
  CONFIG.VEEVA.SERVER = configRecipe.VEEVA.server;
  CONFIG.VEEVA.EMAIL = configRecipe.VEEVA.email;


  if (configRecipe.SS) {
    CONFIG.SS = CONFIG.SS || configRecipe.SS;
  }

  function buildPromise(metalsmith) {
    var deferred = Q.defer();
    metalsmith.build(function (err, data) {
      if (err) {
        deferred.reject(err);
      } else {
        deferred.resolve(data);
      }
    });
    return deferred.promise;
  }

  Metalsmith.prototype.buildPromise = function () {
    var deferred = Q.defer();
    this.build(function (err, data) {
      if (err) {
        deferred.reject(err);
      } else {
        deferred.resolve(data);
      }
    });
    return deferred.promise;
  };

  function mkdir(dirname) {
    var deferred = Q.defer();
    mkdirp(dirname, function (err) {
      if (err) {
        console.log("error");

        deferred.reject(err);
      } else {
        deferred.resolve(dirname);
      }
    });

    return deferred.promise;
  }

  function rmdir(dirname) {
    var deferred = Q.defer();

    rimraf(dirname, function (err) {
      if (err) {
        deferred.reject(err);
      } else {
        deferred.resolve();
      }
    });

    return deferred.promise;
  }

  function rm(filename) {
    var deferred = Q.defer();
    fs.unlink(filename, function (err) {
      if (err) {
        deferred.reject(err);
      } else {
        deferred.resolve()
      }
    });

    return deferred.promise;
  }


  function getDirectories(srcpath) {
    return fs.readdirSync(srcpath).filter(function (file) {
      return fs.statSync(path.join(srcpath, file)).isDirectory();
    });
  }

  function getFiles(srcpath) {
    return fs.readdirSync(srcpath).filter(function (file) {
      return fs.statSync(path.join(srcpath, file)).isFile();
    });
  }

  function note(msg) { console.log(chalk.blue(msg)); }
  function error(msg) { console.log(chalk.red.bold("✗ 💩 ") + msg); }
  function success(msg) { console.log(chalk.yellow.bold("✔︎ " + msg)); }
  function stdOut(msg) { console.log(chalk.gray(msg)); }

  function executeWhen(condition, func, successMsg, failureMsg) {
  	if(Array.isArray(condition)) {
  		condition = condition.reduce(function(acc, val) { return acc && val;}, true);
  	}

  	if(condition) {
  		if (successMsg) note(successMsg);
  		return func();
  	} else {
  		if (failureMsg) note (failureMsg);
  		return (function() {  d = Q.defer(); d.resolve("Short circuit"); return d.promise; })();
  	}
  }

  function bake() {
    var deferred = Q.defer();

      // make a temp directory
      executeWhen(CONFIG.FLAGS.BAKE, function() {
        return mkdir(path.join(CONFIG.ROOT_DIR, CONFIG.MAIN.TEMP));
      })
      // inline all partials, and insert globals
      .then(function () {
        return executeWhen(CONFIG.FLAGS.BAKE, inlinePartialsAndGlobals, "⤷ Baking ");
      })
      // compile sass
      .then(function () {
        return executeWhen(CONFIG.FLAGS.BAKE, compileSass, "⤷ Mixing in SASS ");
      })
      //re-link
      .then(function () {
      	return executeWhen(CONFIG.FLAGS.RELINK, relink, "⤷ Whipping up assets and hyperlinks ");
      })
      .then(function () {
      	return executeWhen(CONFIG.FLAGS.VEEV2REL, veev2rel, "⤷ VEEV2REL ");
      })
      //take screenshots
      .then(function () {
      	return executeWhen(CONFIG.FLAGS.SCREENSHOTS, screenshots, "⤷ Sprinkling with screenshots ");
      })
      // zip it all up
      .then(function () {
      	return executeWhen(CONFIG.FLAGS.PACKAGE, pkg, "⤷ Bagging it up");
      })
      // generate control files
      .then(function() {
        return executeWhen(CONFIG.FLAGS.CONTROLS, generateCtlFiles, "⤷ Generating metadata ");
      })
      // publish it!
      .then(function() {
        return executeWhen(CONFIG.FLAGS.PUBLISH, uploadSlides, "⤷ Shipping it off to market ");
      })
      // clean up temp folder
      .then(function (err) {
      	return executeWhen(CONFIG.FLAGS.CLEAN, function() { rmdir(path.join(CONFIG.ROOT_DIR, CONFIG.MAIN.TEMP)) }, "⤷ Washing ");
      })
      //.catch(function (err) { console.log(err); })
      .done(function () {
        success("yum!🍕");
        deferred.resolve();
      },
      function (err) {
        error(err);
        deferred.reject(err);
      });

      return deferred.promise;
  }

  function inlinePartialsAndGlobals() {
      var ms = new Metalsmith(CONFIG.ROOT_DIR)
        .source(CONFIG.MAIN.SOURCE)
        .destination(CONFIG.MAIN.TEMP)
        .use(partial({
          directory: path.join(CONFIG.ROOT_DIR, CONFIG.MAIN.PARTIALS),
          engine: 'eco'
        }))
        .use(templates({
          directory: path.join(CONFIG.ROOT_DIR, CONFIG.MAIN.TEMPLATES),
          engine: 'eco'
        }))
        .use(assets({
          source: path.join(CONFIG.ROOT_DIR, CONFIG.MAIN.ASSETS),
          destination: ".",
          recursive: true
        }));
      return ms.buildPromise();
  }

  function compileSass() {
      var ms = new Metalsmith(CONFIG.ROOT_DIR)
              .source(CONFIG.MAIN.TEMP)
              .destination(CONFIG.MAIN.DEST)
              .use(sass());
      return ms.buildPromise();
  }

  function runShellScript(cmd, args, name, shellOpts) {
  	var shellOpts = shellOpts || {};
  	var deferred = Q.defer();
  	var spawn = require('child_process').spawn;
  	shell = spawn(cmd, args, shellOpts);

    shell.stdout.on('data', function(data) {
  	   if (CONFIG.FLAGS.VERBOSE) stdOut('stdout: ' + data);
  	});

  	shell.stderr.on('data', function (data) {
  	 error('stderr: ' + data);
  	});

    shell.on('exit', function (status) {
      if (status === 0) {
        deferred.resolve();
      } else {
        deferred.reject(name + ' script exited with status ' + status);
      }
    });

    return deferred.promise;
  }

  function relink() {
  	return runShellScript('python3', [path.join(__dirname, './relink.py'), '--integrate_all', path.join(CONFIG.ROOT_DIR, CONFIG.MAIN.DEST)], "Linking");
  }

  function veev2rel() {
  	return runShellScript('python3', [path.join(__dirname, './relink.py'), '--veev2rel', path.join(CONFIG.ROOT_DIR, CONFIG.MAIN.DEST)], "veev2rel");
  }

  function generateCtlFiles() {
    return runShellScript('python3', [path.join(__dirname, './genctls.py'), '--src', path.join(CONFIG.ROOT_DIR, CONFIG.MAIN.DEST, CONFIG.MAIN.ZIPS), '--out', path.join(CONFIG.ROOT_DIR, CONFIG.MAIN.DEST, CONFIG.MAIN.CTLS), '--root', CONFIG.ROOT_DIR, '--u', CONFIG.VEEVA.USERNAME, '--pwd', CONFIG.VEEVA.PASSWORD, '--email', CONFIG.VEEVA.EMAIL], "Generating control files");
  }

  function uploadSlides() {
    return runShellScript('python3', [path.join(__dirname, './publish.py'), '--zip', path.join(CONFIG.ROOT_DIR, CONFIG.MAIN.DEST, CONFIG.MAIN.ZIPS), '--ctl', path.join(CONFIG.ROOT_DIR, CONFIG.MAIN.DEST, CONFIG.MAIN.CTLS), '--host', CONFIG.VEEVA.SERVER, '--u', CONFIG.VEEVA.USERNAME, '--pwd', CONFIG.VEEVA.PASSWORD], "Publishing slides");
  }

  function screenshots() {
    var d = Q.defer();

    var baseDir = CONFIG.MAIN.DEST,
      basePath = path.join(CONFIG.ROOT_DIR, baseDir);
    var phantom = require('phantom'),
        im = require('imagemagick');

    var dirs = getDirectories(basePath);

    var sizes = CONFIG.SS || {
      full: {width: 1024, height: 768, name: "-full.jpg"},
      thumb: {width: 200, height: 150, name: "-thumb.jpg"}
    };

    function convertImage (opts) {
      var deferred = Q.defer();
      im.convert(opts, function(err) {
        if (err) {
          deferred.reject(err);
        };

        deferred.resolve();
      });

      return deferred.promise;
    }

    function renderPage (url, output) {
      var deferred = Q.defer();

      if (url.match(".pdf") == null) {
        phantom.create(function (ph) {
          ph.createPage(function (page) {
            page.set('viewportSize', sizes.full);

            var completePath = url;

            page.open(completePath, function () {
              page.render(output+".png", function () {
                ph.exit();
                deferred.resolve();
              });
            });

          });
        });
      } else {
        convertImage(['-density', '72', url, output+".png"])
          .then(function() {
            deferred.resolve();
          });
      }

      return deferred.promise;
    }

    function takeScreenshot (basePath, dir, matchingFile) {

    	  if(CONFIG.FLAGS.VERBOSE) stdOut("Screenshotting " + matchingFile);

          var deferred = Q.defer();

          var full = dir, //+ "-full",
            thumb = dir + "-thumb.png";

            var completePath = "file://" + path.join(basePath,dir,matchingFile),
                outputFile = path.join(basePath,dir,full);

          renderPage(completePath,outputFile)
            .then(function () { // convert to jpg
              return convertImage([outputFile+".png", '-background', 'white', '-flatten', outputFile+sizes.full.name]);
            })
            .then(function () { // resize jpg to thumbnail
              return convertImage([outputFile+sizes.full.name, '-resize', sizes.thumb.width+'x'+sizes.thumb.height, outputFile+sizes.thumb.name]);
            })
            .then(function () { // remove the original png
              rm(outputFile+".png");
            })
            .done(function () {
              deferred.resolve();
            }, function () {
              deferred.reject();
            });
          
          return deferred.promise;
    };

    var allScreenshots = ___(dirs)
      .map(function (dir) {
        var files = getFiles(path.join(basePath, dir));
        
        return ___(files)
          .filter(function (file) { 
            var regex = new RegExp(dir + "(.htm|.pdf)", "g");
            return file.match(regex);
          })
          .map(function(matchingFile) { return takeScreenshot(basePath, dir, matchingFile); })
          .value(); // end matching

      })
      .flattenDeep()
      .value(); // create an array of promise-returning functions containing all the screenshots


    Q.all(allScreenshots).done(function() { // if all are accepted
      d.resolve(); // resolve the main promise
    }, function() { // if any are rejected
      d.reject();
    });

    return d.promise;
  } // end screenshots

  function pkg() {
  	return runShellScript('sh', [path.join(__dirname, './package_slides.sh')], 'Packaging', { cwd: path.join(CONFIG.ROOT_DIR, CONFIG.MAIN.DEST) });
  }

  function watch() {
      //let's watch
    return function () {

      var ASSETS = CONFIG.MAIN.ASSETS,
        DEST = CONFIG.MAIN.DEST,
        PARTIALS = CONFIG.MAIN.PARTIALS,
        SOURCE = CONFIG.MAIN.SOURCE,
        TEMP = CONFIG.MAIN.TEMP,
        TEMPLATES = CONFIG.MAIN.TEMPLATES;

      function watcher() {

        bake().then(function () {
          stdOut("⤷ Watching for changes (^C to quit)...");
        })
        .done(function() {
        
        if(CONFIG.FLAGS.VERBOSE) {
			note("build: " + DEST);
			note("source: " + SOURCE);
			console.log(chalk.blue("partials: ") + PARTIALS);
			console.log(chalk.blue("global assets: ") + ASSETS);
			console.log(chalk.blue("templates: ") + TEMPLATES);
        }

        require('chokidar')
          .watch([SOURCE, PARTIALS, ASSETS, TEMPLATES], {ignored: /[\/\\]\./, ignoreInitial: true})
          .on('all', function (event, path) {
            console.log(chalk.blue(event), path);
            bake().done(function () { /*success("yum!🍕");*/ }, function (err) { /*error(err);*/ });
          });
        });

      }

      return watcher();
    };
  }

  function run() {
    console.log(chalk.yellow.bold("  _   ________ _   ___________   _____ "));
    console.log(chalk.yellow.bold(" | | / / __/ /| | / / __/ __| | / / _ |"));
	  console.log(chalk.yellow.bold(" | |/ / _// /_| |/ / _// _/ | |/ / __ |"));
	  console.log(chalk.yellow.bold(" |___/___/____|___/___/___/ |___/_/ |_|"));
 	  console.log(chalk.yellow.bold(""));

    if (CONFIG.FLAGS.WATCH) {
      watch(bake)();
    } else {
      bake();
    }
  }

  this.pkg = pkg;
  this.run = run;

}