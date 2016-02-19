#!/usr/bin/env node


(function init() {
	var path, cliArgs, Veelveeva, configfile;

	try {
		path = require("path");
		cliArgs = require("command-line-args");

		Velveeva = require(path.join(__dirname, "lib/velveeva.js"));
	} catch (e) {
		console.log(e.message);
		return;
	}

	var cli = cliArgs([
	  { name: "clean", type: Boolean, alias: "c", description: "Clean up the mess (mom would be proud!) [Selected when no options are given]"},
	  { name: "controls", type: Boolean, alias: "l", description: "Generate slide control files (gonna have something already baked)"},
	  { name: "controlsonly", type: Boolean, alias: "L", description: "Only generate control files"},
	  { name: "dev", type: Boolean, alias: "dev", description: "Use the quick-bake test kitchen environment (no screenshots, no packaging). This is a shortcut to using go --clean --watch --veev2rel"},
	  { name: "help", type: Boolean, alias: "h", description: "Display this message"},
	  { name: "init", type: Boolean, alias: "i", description: "Initialize a new VELVEEVA project"},
	  { name: "package", type: Boolean, alias: "p", description: "Wrap it up [Selected when no options are given]"},
	  { name: "packageonly", type: Boolean, alias: "P", description: "Just wrap it up (you gotta already have something baked)"},
	  { name: "publish", type: Boolean, alias: "h", description: "Ship it off to market"},
	  { name: "publishonly", type: Boolean, alias: "H", description: "(Only) ship it off to market (you gotta already have something baked, and control files generated)"},
	  { name: "relink", type: Boolean, alias: "r", description: "Make some href saussage (replace relative links with global and convert to veeva: protocol)"},
	  { name: "screenshots", type: Boolean, alias: "s", description: "Include Screenshots [Selected when no options are given]"},
	  { name: "veev2rel", type: Boolean, alias: "2", description: "Convert veeva: hrefs to relative links"},
	  { name: "verbose", type: Boolean, alias: "v", description: "Chatty Cathy"},
	  { name: "watch", type: Boolean, alias: "w", description: "Watch for changes and re-bake on change" } 
	]);

	var options, V;
	try {
		options = cli.parse();
	} catch (e) { //was there an error with the command line flags?
		console.log(e.message);
		return;
	}


	function init() {
		
		console.log("To initialize a new project, run");
		console.log("\nVELVEEVA/lib/init.py\n");
	}


	if (options.init) init();

	try {
		configFile = require(path.join(process.cwd(),'VELVEEVA-config.json'));
	} catch (e) {
		console.log("Couln't load VELVEEVA-config.json");
		init();
		return; // ugly
	}

	V = new Velveeva(configFile);

	if (options.clean) V.config.FLAGS.CLEAN = true;
	if (options.controlsonly) {
		V.config.FLAGS.BAKE = false;
		V.config.FLAGS.CONTROLS = true;
	}
	if (options.controls) {
		V.config.FLAGS.BAKE = true;
		V.config.FLAGS.CLEAN = true;
		V.config.FLAGS.CONTROLS = true;
		V.config.FLAGS.PACKAGE = true;
	}
	if (options.dev) {
		V.config.VEEV2REL = true;
		V.config.FLAGS.PACKAGE = false;
		V.config.FLAGS.SCREENSHOTS = false;
		V.config.FLAGS.DEV = true;
		V.config.FLAGS.WATCH = true;
	}
	if (options.package) V.config.FLAGS.PACKAGE = true;
	if (options.packageonly) {
		V.config.FLAGS.BAKE = false;
		V.config.FLAGS.CLEAN = false;
		V.config.FLAGS.PACKAGE = true;
	}
	if (options.publish) {
		V.config.FLAGS.BAKE = true;
		V.config.FLAGS.CLEAN = true;
		V.config.FLAGS.CONTROLS = true;
		V.config.FLAGS.SCREENSHOTS = true;
		V.config.FLAGS.PACKAGE = true;
		V.config.FLAGS.PUBLISH = true;
	}
	if (options.publishonly) {
		V.config.FLAGS.BAKE = false;
		V.config.FLAGS.PUBLISH = true;
	}
	if (options.relink) V.config.FLAGS.RELINK = true;
	if (options.screenshots) V.config.FLAGS.SCREENSHOTS = true;
	if (options.verbose) V.config.FLAGS.VERBOSE = true;
	if (options.veev2rel) V.config.FLAGS.VEEV2REL = true;
	if (options.watch) V.config.FLAGS.WATCH = true;

	if (Object.keys(options).length === 0 || (Object.keys(options).length === 1) && options.verbose) {
	  // default case, also allows for default options with the verbose flag
	  V.config.FLAGS.PACKAGE = true;
	  V.config.FLAGS.RELINK = false;
	  V.config.FLAGS.SCREENSHOTS = true;
	  V.config.FLAGS.CLEAN = true;

	}

	if (options.help) {
		console.log(cli.getUsage());
	} else {
	    V.run();
	}
})();