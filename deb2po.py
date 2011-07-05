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

header = '''
msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION"
"Report-Msgid-Bugs-To: "
"POT-Creation-Date: 2011-07-05 01:00+0800"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>"
"Language-Team: LANGUAGE <LL@li.org>"
"MIME-Version: 1.0"
"Content-Type: text/plain; charset=UTF-8"
"Content-Transfer-Encoding: 8bit"\n
'''

def deb2po():
    
    
    '''Convert .debian to .po format.'''
    # Init rules.
    poRe = re.compile("\.debian")
    langRe = re.compile("-([a-zA-Z_]+).+")
    shortDescRe = re.compile("^Description(-[^:]+)?:\s([^\n]+)")
    longDescRe = re.compile("^ ([^\.][^\n]+)")
    breakLineRe = re.compile("^ \.")
    commentRe = re.compile("#[^\n]+")
    
    # Get *.debian filename.
    debFilename = sys.argv[1]
    
    # Get *.po filename.
    poFilename = poRe.sub(".po", debFilename)
    
    # Convert format.
    poFileDict = {}
    lang = ""
    longIndex = 1
    for line in open(debFilename).readlines():
        lineContent = line.rstrip("\n")
        if shortDescRe.match(lineContent):
            langStr = shortDescRe.match(lineContent).group(1)
            
            if langStr == None:
                lang = "en"
            else:
                lang = langRe.match(langStr).group(1)
            longIndex = 1
            
            if not poFileDict.has_key(lang):
                poFileDict[lang] = {}
            
            shortDesc =  shortDescRe.match(lineContent).group(2)
            (poFileDict[lang])["short"] = shortDesc
        elif longDescRe.match(lineContent):
            longDesc = longDescRe.match(lineContent).group(1)
            longKey = "long" + str(longIndex)
            
            if not (poFileDict[lang]).has_key(longKey):
                (poFileDict[lang])[longKey] = []
            
            (poFileDict[lang])[longKey].append(longDesc)
        elif breakLineRe.match(lineContent):
            longIndex += 1
            
    # Generate *.po files.
    for (lang, docs) in poFileDict.items():
        if docs["short"] != "<trans>":
            # Fill *.po content.
            poFilecontent = ""
            
            poFilecontent += header
            
            poFilecontent += '''msgctxt \"short\"\n'''
            poFilecontent += '''msgid \"%s\"\n''' % (docs["short"])
            poFilecontent += '''msgstr \"\"\n\n'''
            
            longDescList = docs.keys()
            longDescList.remove("short")
            for longDescKey in sorted(longDescList):
                poFilecontent += '''msgctxt \"%s\"\n''' % (longDescKey)
                poFilecontent += '''msgid \"\"\n'''
                for longDesc in docs[longDescKey]:
                    poFilecontent += '''\"%s\"\n''' % (longDesc)
                poFilecontent += '''msgstr \"\"\n\n'''
            
            poDir = "./" + lang
            if not os.path.exists(poDir):
                os.makedirs(poDir)
                
            poFilepath = "./%s/%s" % (lang, poFilename)
            poFile = open(poFilepath, "w")            
            poFile.write(poFilecontent)
            poFile.close()
     
    print "Convert %s successful." % (debFilename)
            
if __name__ == "__main__":
    deb2po()
