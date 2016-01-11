#!/bin/bash
mkdir -p _zips
for i in [!_zips]*/; do zip -r "_zips/${i%/}.zip" "$i"; done
#zip build.zip ./0*.zip 
exit