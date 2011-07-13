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
    '''Convert .po to .deepin format.'''
    # Init rule.
    poRe = re.compile("\.po")
    packageRe = re.compile("([^\.]+)\.po")
    languageRe = re.compile("^\"Language:\s([^\\\n]+)\\\\n")
    shortCtxtRe = re.compile("^msgctxt \"short")
    longCtxtRe = re.compile("^msgctxt \"long")
    shortEnDescRe = re.compile("^msgid\s\"(.*)\"$")
    shortOtherDescRe = re.compile("^msgstr\s\"(.*)\"$")
    langRe = re.compile("^msgid\s+(.*)")
    otherLangRe = re.compile("^msgstr\s+(.*)")
    longDescRe = re.compile("^\"(.*)\"$")
    quotationRe = re.compile(r"\\\"")
    rx = re.compile(u"([\u2e80-\uffff])", re.UNICODE)
    
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
        if languageRe.match(lineContent):
            otherLang = languageRe.match(lineContent).group(1)
            
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
        elif descType == "short":
            if shortEnDescRe.match(lineContent):
                (poInfoDict["en"])["short"] = shortEnDescRe.match(lineContent).group(1)
            elif shortOtherDescRe.match(lineContent):
                (poInfoDict[otherLang])["short"] = shortOtherDescRe.match(lineContent).group(1)
        elif descType == "long":
            if langRe.match(lineContent):
                otherLangMark = False
                longLine = langRe.match(lineContent).group(1)
                if longLine != "\"\"":
                    addInLongDesc(poInfoDict, longDescKey, "en", quotationRe, longDescRe, longLine)
            elif otherLangRe.match(lineContent):
                otherLangMark = True
                longLine = otherLangRe.match(lineContent).group(1)
                if longLine != "\"\"":
                    addInLongDesc(poInfoDict, longDescKey, otherLang, quotationRe, longDescRe, longLine)
            elif longDescRe.match(lineContent):
                if otherLangMark:
                    language = otherLang
                else:
                    language = "en"
                addInLongDesc(poInfoDict, longDescKey, language, quotationRe, longDescRe,
                              longDescRe.match(lineContent).group(0))
                
    # Wrap long description.
    for (lang, docs) in poInfoDict.items():
        for (descType, descList) in docs.items():
            if descType != "short":
                wrapList = map (lambda l: cjkwrap(l, 80, rx), descList)
                (poInfoDict[lang])[descType] = wrapList
    
    # Generate .deepin file content.
    debFilecontent = headerTemplate % (packageName, packageName)
    enDocs = poInfoDict.pop("en")
    debFilecontent += genDescription("en", enDocs)
    for (lang, docs) in poInfoDict.items():
        debFilecontent += genDescription(lang, docs)
        
    # Write content to *.deepin file.
    debDir = "./" + otherLang
    if not os.path.exists(debDir):
        os.makedirs(debDir)
    debFilepath = "%s/%s.deepin" % (debDir, packageName)
    debFile = open(debFilepath, "w")            
    debFile.write(debFilecontent)
    debFile.close()
    
def cjkwrap(text, width, rx, encoding="utf8"):
    return reduce(lambda line, word, width=width: '%s%s%s' %              
                  (line,
                   [' ','\n ', ''][(len(line)-line.rfind('\n')-1 + len(word.split('\n',1)[0] ) >= width) or
                                  line[-1:] == '\0' and 2],
                   word),
                  rx.sub(r'\1\0 ', unicode(text,encoding)).split(' ')
                  ).replace('\0', '').encode(encoding)

def addInLongDesc(poInfoDict, longDescKey, language, quotationRe, longDescRe, longLine):
    '''Add in long description.'''
    # Replace \"foo\" to "foo".
    longLine = quotationRe.sub("\"", longLine)
    
    # Pick content from "".
    longLine = longDescRe.match(longLine).group(1)
                
    if not (poInfoDict[language]).has_key(longDescKey):
        (poInfoDict[language])[longDescKey] = []
    
    # Append directly if haven't other long description exists.
    if len((poInfoDict[language])[longDescKey]) == 0:
        (poInfoDict[language])[longDescKey].append(longLine)
    else:
        lastLine = ((poInfoDict[language])[longDescKey])[-1]

        # Append directly if last long description end with \n.
        if len(lastLine.split("\\n")) > 1:
            (poInfoDict[language])[longDescKey].append(longLine)
        # Otherwise connect current line to the end of last line.
        else:
            ((poInfoDict[language])[longDescKey])[-1] = lastLine + longLine
    
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
            content += " " + splitList[0] + "\n"
        
        # Fill long description segment.
        if longDescKey != lastLongDescKey:
            content += " .\n"
        
    return content
    
if __name__ == "__main__":
    if len(sys.argv) == 2:
        po2deb(sys.argv[1])
    else:
        print "./po2deb.py foo.po"

#  LocalWords:  Deepin po deepin msgctxt msgid msgstr lang
