#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 Deepin, Inc.
#               2011 Yong Wang
#
# Author:     Yong Wang <lazycat.manatee@gmail.com>
# Maintainer: Yong Wang <lazycat.manatee@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import sys
import os

headerTemplate = '''
# Source: %s
# Package(s): %s
# Prioritize: 50
# This Description is active
# This Description is owned
'''

def po2deb():
    '''Convert .po to .debian format.'''
    # Init rule.
    shortCtxtRe = re.compile("^msgctxt \"short")
    longCtxtRe = re.compile("^msgctxt \"long")
    shortEnDescRe = re.compile("^msgid\s\"(.*)\"$")
    shortOtherDescRe = re.compile("^msgstr\s\"(.*)\"$")
    otherLangRe = re.compile("^msgstr \"\"")
    longDescRe = re.compile("^\"(.*)\"$")
    quotationRe = re.compile(r"\\\"")
    
    # Get po directory.
    poDir = (sys.argv[1]).rstrip("/")
    packageName = os.path.basename(poDir)
    
    # Get files.
    poFiles = []
    for (pathName, dirName, fileName) in os.walk(poDir):
        if os.path.basename(pathName) != packageName:
            poFiles.append((os.path.basename(pathName), fileName[0]))
    
    # Pick .po information. 
    poInfoDict = {}
    for (dirname, filename) in poFiles:
        # Init.
        descType = ""
        longIndex = 1
        longDescKey = ""
        otherLangMark = False
    
        if dirname == "pot":
            lang = "en"
        else:
            lang = dirname
        
        if not poInfoDict.has_key(lang):
            poInfoDict[lang] = {}
        
        poFilepath = "%s/%s/%s" % (poDir, dirname, filename)
        # Handle English content.
        for line in open(poFilepath).readlines():
            lineContent = line.rstrip("\n")
            
            if shortCtxtRe.match(lineContent):
                descType = "short"
            elif longCtxtRe.match(lineContent):
                descType = "long"
                longDescKey = "long" + str(longIndex)
                longIndex += 1
                otherLangMark = False
            elif descType == "long" and otherLangRe.match(lineContent):
                otherLangMark = True
            else:
                if descType == "short":
                    if lang == "en":
                       if shortEnDescRe.match(lineContent):
                           (poInfoDict[lang])["short"] = shortEnDescRe.match(lineContent).group(1)
                    elif shortOtherDescRe.match(lineContent):
                        (poInfoDict[lang])["short"] = shortOtherDescRe.match(lineContent).group(1)
                elif descType == "long":
                    if (lang == "en" or otherLangMark) and longDescRe.match(lineContent):
                        longLine = longDescRe.match(lineContent).group(1) 
                        longLine = quotationRe.sub("\"", longLine)
                        
                        if not (poInfoDict[lang]).has_key(longDescKey):
                            (poInfoDict[lang])[longDescKey] = []
                            
                        (poInfoDict[lang])[longDescKey].append(longLine)
                        
    # Generate .debian file content.
    debFilecontent = headerTemplate % (packageName, packageName)
    enDocs = poInfoDict.pop("en")
    debFilecontent += genDescription("en", enDocs)
    for (lang, docs) in poInfoDict.items():
        debFilecontent += genDescription(lang, docs)
        
    # Write content to *.debian file.
    debFilepath = "%s.debian" % (packageName)
    debFile = open(debFilepath, "w")            
    debFile.write(debFilecontent)
    debFile.close()
    
def genDescription(lang, docs):
    '''Generate description.'''
    # Init.
    content = ""
    
    # Generate short description.
    if lang == "en":
        descHeader = "Description: "
    else:
        descHeader = "Description-%s.UTF-8: " % (lang)
    
    shortDesc = docs.pop("short")
    
    content += descHeader + shortDesc + "\n"
    
    # Generate long description.
    longDescKeys = sorted(docs.keys())
    lastLongDescKey = longDescKeys[-1]
    for longDescKey in longDescKeys:
        # Fill long description.
        longDescList = docs[longDescKey]
        for longDesc in longDescList:
            splitList = longDesc.split("\\n")
            if len(splitList) == 2:
                # If current line end with \n
                content += " " + splitList[0] + "\n"
            else:
                # Otherwise split line.
                content += " " + longDesc + "\n"
        
        # Fill long description segment.
        if longDescKey != lastLongDescKey:
            content += " .\n"
        
    return content
    
if __name__ == "__main__":
    po2deb()
