#!/usr/bin/env python
#
# Copyright 2011 xbrl-il.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import logging

from django.utils import simplejson
#from xml.etree import ElementTree as ET

def convertToJson(tree):
    """ Convert the given xml tree to JSON.
        The conversion is done in the following manner:
        Elements are converted to json objects in case they have further children.
        Attributes are converted to json object properties.
        Empty or nil elements are dropped all together
    
        @param tree: The xml tree to convert
    """
    jsonObj = {}
    for elem in tree.getiterator():
        convertToJsonHelper(elem, jsonObj)
        
    return jsonObj
        
def convertToJsonHelper(elem, jsonObj):        
    def normalize(name):
        if name[0] == "{":
            uri, tag = name[1:].split("}")
            return tag
        else:
            return name
    
    if len(elem.attrib) > 0 or len(elem) > 0:
        # skip nil elements
        if ("{http://www.w3.org/2001/XMLSchema-instance}nil" in elem.attrib and elem.attrib["{http://www.w3.org/2001/XMLSchema-instance}nil"] == "true"):
            return
        
        currentObj = jsonObj[normalize(elem.tag)] = {}
        
        for key,value in elem.attrib.items():
            currentObj[normalize(key)] = value
            #logging.info('attrib ' + key + ' value ' + value)
        
        if not elem.text is None:
            currentObj["value"] = elem.text
            
        for subelem in elem:
            convertToJsonHelper(subelem, currentObj)
    else:
        jsonObj[normalize(elem.tag)] = elem.text
        #logging.info('key ' + normalize(elem.tag) + ' value ' + elem.text)
    
