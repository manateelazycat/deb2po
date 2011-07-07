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

def po2deb(poFilepath):
    '''Convert .po to .debian format.'''
    # Init rule.
    poRe = re.compile("\.po")
    packageRe = re.compile("([^\.]+)\.po")
    langRe = re.compile("^\"Language:\s([^\\\n]+)\\\\n")
    shortCtxtRe = re.compile("^msgctxt \"short")
    longCtxtRe = re.compile("^msgctxt \"long")
    shortEnDescRe = re.compile("^msgid\s\"(.*)\"$")
    shortOtherDescRe = re.compile("^msgstr\s\"(.*)\"$")
    otherLangRe = re.compile("^msgstr \"\"")
    longDescRe = re.compile("^\"(.*)\"$")
    quotationRe = re.compile(r"\\\"")
    
    # Get *.po filename.
    poFilename = os.path.basename(poFilepath)    
    
    # Get package name.
    packageName = packageRe.match(poFilename).group(1)
    
    # Get lines.
    lines = open(poFilepath).readlines()
    
    # Search language information.
    otherLang = ""
    while otherLang == "":
        lineContent = lines.pop(0)
        lineContent = lineContent.rstrip("\n")
        if langRe.match(lineContent):
            otherLang = langRe.match(lineContent).group(1)
            
    # Pick .po information. 
    poInfoDict = {"en" : {},
                  otherLang : {}}
    descType = ""
    longIndex = 1
    longDescKey = ""
    otherLangMark = False

    for line in lines:
        lineContent = line.rstrip("\n")
        
        if shortCtxtRe.match(lineContent):
            # Mark short type.
            descType = "short"
        elif longCtxtRe.match(lineContent):
            # Mark long type 
            descType = "long"
            
            longDescKey = "long" + str(longIndex)
            longIndex += 1
            otherLangMark = False
        elif descType == "long" and otherLangRe.match(lineContent):
            # Mark other language.
            otherLangMark = True
        else:
            if descType == "short":
                if shortEnDescRe.match(lineContent):
                    (poInfoDict["en"])["short"] = shortEnDescRe.match(lineContent).group(1)
                elif shortOtherDescRe.match(lineContent):
                    (poInfoDict[otherLang])["short"] = shortOtherDescRe.match(lineContent).group(1)
            elif descType == "long":
                if longDescRe.match(lineContent):
                    if otherLangMark:
                        language = otherLang
                    else:
                        language = "en"
                    longLine = longDescRe.match(lineContent).group(1) 
                    longLine = quotationRe.sub("\"", longLine)
                    
                    if not (poInfoDict[language]).has_key(longDescKey):
                        (poInfoDict[language])[longDescKey] = []
                        
                    (poInfoDict[language])[longDescKey].append(longLine)
                        
    # Generate .debian file content.
    debFilecontent = headerTemplate % (packageName, packageName)
    enDocs = poInfoDict.pop("en")
    debFilecontent += genDescription("en", enDocs)
    for (lang, docs) in poInfoDict.items():
        debFilecontent += genDescription(lang, docs)
        
    # Write content to *.debian file.
    if not os.path.exists("./lang"):
        os.makedirs("./lang")
    debFilepath = "./lang/%s.debian" % (packageName) 
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
    if len(sys.argv) == 2:
        po2deb(sys.argv[1])
    else:
        print "./po2deb.py foo.po"

#  LocalWords:  Deepin po debian msgctxt msgid msgstr lang
