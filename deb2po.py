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

copyrightTemplate = '''# Chinese (China) description translation of %s
# Copyright (C) 2011 Free Software Foundation, Inc.
# This file is distributed under the same license as the %s package.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#'''

pootleTemplate = "\n#, fuzzy"

headerTemplate = '''
msgid ""
msgstr ""
"Project-Id-Version: %s ddtp-core\\n"
"Report-Msgid-Bugs-To: happyaron.xu@gmail.com\\n"
"POT-Creation-Date: 2011-07-05 01:00+0800\\n"
"PO-Revision-Date: 2011-07-05 10:13+0800\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: Chinese (simplified) <i18n-zh@googlegroups.com>\\n"
"Language: %s\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"\n
'''

shortTemplate = '''#. Translators: This is the short description.
#.
#: %s
#: short
'''

longTemplate = '''#. Translators: This is the long description part %s.
#.
#: %s
#: long part %s
'''

def deb2po(debFilepath):
    '''Convert .debian to .po format.'''
    # Init rules.
    debPo = re.compile("\.debian")
    packageRe = re.compile("([^\.]+)\.debian")
    langRe = re.compile("-([a-zA-Z_]+).+")
    shortDescRe = re.compile("^Description(-[^:]+)?:\s([^\n]+)")
    longDescRe = re.compile("^ ([^\.][^\n]+)")
    segmentIndexRe = re.compile("long([0-9]+)")
    breakRe = re.compile("[^:]+(\：|:)")
    returnRe = re.compile("^\s+(\-|\*)\s")
    segmentRe = re.compile("^ \.")
    quotationRe = re.compile("\"")
    commentRe = re.compile("#[^\n]+")
    sourceRe = re.compile("^#\sSource:")
    
    # Get *.debian filename.
    debFilename = os.path.basename(debFilepath)    
    
    # Get package name.
    packageName = packageRe.match(debFilename).group(1)
    
    # Remove duplicate description.
    lines = []
    for line in open(debFilepath).readlines():
        # Clean previous source segment if match sourceRe.
        if sourceRe.match(line):
            lines = []
            
        # Append line.
        lines.append(line)
        
    # Convert format.
    poFileDict = {}
    lang = ""
    segmentIndex = 1
    returnMark = False
    
    for line in lines:
        lineContent = line.rstrip("\n")
        if shortDescRe.match(lineContent):
            langStr = shortDescRe.match(lineContent).group(1)
            
            if langStr == None:
                lang = "en"
            else:
                lang = langRe.match(langStr).group(1)
                
            # Init.
            segmentIndex = 1
            returnMark = False
            
            if not poFileDict.has_key(lang):
                poFileDict[lang] = {}
            
            shortDesc = shortDescRe.match(lineContent).group(2)
            shortDesc = quotationRe.sub("\\\"", shortDesc)
            (poFileDict[lang])["short"] = shortDesc
        elif longDescRe.match(lineContent):
            longDesc = longDescRe.match(lineContent).group(1)
            
            # Strip beginning blank if current line not beginning with - or *
            if returnRe.match(longDesc) == None:
                longDesc = longDesc.strip(" ")
                
            # Add blank at line end.
            longDesc = longDesc + " "
            
            # Add \n if last character is : or ：
            if breakRe.match(longDesc):
                longDesc = longDesc.rstrip(" ") + "\\n"
                
            if returnMark:
                # Add \n in previous line if current line and previous line 
                # both beginning with '-' or '*'
                if returnRe.match(longDesc):
                    returnMark = True
                    lastLine = (poFileDict[lang])[longKey].pop()
                    (poFileDict[lang])[longKey].append(lastLine.rstrip(" ") + "\\n")
            else:                    
                # Mark returnMark if current line  beginning with '-' or '*'
                # and previous line is not.
                if returnRe.match(longDesc):
                    returnMark = True

            longKey = "long" + str(segmentIndex)
            
            if not (poFileDict[lang]).has_key(longKey):
                (poFileDict[lang])[longKey] = []
            
            longDesc = quotationRe.sub("\\\"", longDesc)
            (poFileDict[lang])[longKey].append(longDesc)
        elif segmentRe.match(lineContent):
            # Reset mark if reach '.'
            returnMark = False
            
            # Update segment index.
            segmentIndex += 1
            
    # Append \n in long description:
    for (lang, docs) in poFileDict.items():
        if docs["short"] != "<trans>":
            for (descType, desc) in docs.items():
                if descType != "short":
                    lastLine = (poFileDict[lang])[descType].pop()
                    (poFileDict[lang])[descType].append(lastLine.rstrip(" ") + "\\n")
                    
    # Check description segment number in different language.
    longSegmentNumList = []
    origianlSegmentNum = 0
    for (lang, docs) in poFileDict.items():
        # Append segment number.
        descList = docs.keys()
        descList.remove("short")
        descNum = len(descList)
        longSegmentNumList.append((lang, descNum))
        
        if lang == "en":
            origianlSegmentNum = descNum
        
    for (lang, longDescNum) in longSegmentNumList:
        if longDescNum != origianlSegmentNum:
            print "* WARNING: The segment number of ./%s/%s/%s.po (%s) is different with original (%s)." % (packageName, lang, packageName, longDescNum, origianlSegmentNum)
    
    # Generate *.po files.
    for (lang, docs) in poFileDict.items():
        
        
        if docs["short"] != "<trans>":
            # Fill *.po content.
            poFilecontent = ""
            
            # Fill copyright string.
            poFilecontent += copyrightTemplate % (packageName, packageName)
            
            # Fill pootle string.
            if lang == "en":
                poFilecontent += pootleTemplate

            # Fill header string.
            if lang == "en":
                poFilecontent += headerTemplate % (packageName, "")
            else:
                poFilecontent += headerTemplate % (packageName, lang)
            
            # Fill short template.
            poFilecontent += shortTemplate % (packageName)
            
            # Fill short description.
            poFilecontent += '''msgctxt \"short\"\n'''
            if lang == "en":
                poFilecontent += '''msgid \"%s\"\n''' % (docs["short"])
                poFilecontent += '''msgstr \"\"\n\n'''
            else:
                poFilecontent += '''msgid \"%s\"\n''' % ((poFileDict["en"])["short"])
                poFilecontent += '''msgstr \"%s\"\n\n''' % (docs["short"])
            
            # Fill long description.
            longDescList = docs.keys()
            longDescList.remove("short")
            for longDescKey in sorted(longDescList):
                index = segmentIndexRe.match(longDescKey).group(1)
                # Fill long template.
                poFilecontent += longTemplate % (index, packageName, index)
                
                poFilecontent += '''msgctxt \"%s\"\n''' % (longDescKey)
                poFilecontent += '''msgid \"\"\n'''
                if lang == "en":
                    for longDesc in docs[longDescKey]:
                        poFilecontent += '''\"%s\"\n''' % (longDesc)
                    poFilecontent += '''msgstr \"\"\n\n'''
                else:
                    for longDesc in (poFileDict["en"])[longDescKey]:
                        poFilecontent += '''\"%s\"\n''' % (longDesc)
                    poFilecontent += '''msgstr \"\"\n'''
                    for longDesc in docs[longDescKey]:
                        poFilecontent += '''\"%s\"\n''' % (longDesc)
                    poFilecontent += "\n"
            
            # Create file.
            if lang == "en":
                poDir = "./pot"
                poFilename = debPo.sub(".pot", debFilename)
            else:
                poDir = "./" + lang
                poFilename = debPo.sub(".po", debFilename)
            if not os.path.exists(poDir):
                os.makedirs(poDir)
            
            # Write content to *.po file.
            poFilepath = "%s/%s" % (poDir, poFilename)
            poFile = open(poFilepath, "w")            
            poFile.write(poFilecontent)
            poFile.close()
     
    print "Convert %s successful." % (debFilepath)
            
if __name__ == "__main__":
    if len(sys.argv) == 2:
        deb2po(sys.argv[1])
    else:
        print "./deb2po.py foo.debian"

#  LocalWords:  pootle msgctxt
