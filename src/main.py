#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
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
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import urlfetch                      

from django.utils import simplejson     
from xml.etree import ElementTree as ET

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write('Hello world!')


class XML2JSON(webapp.RequestHandler):
    _someString =  """<?xml version="1.0" encoding="UTF-8"?>
<ISBNdb server_time="2005-02-25T23:03:41">
 <BookList total_results="1" page_size="10" page_number="1" shown_results="1">
  <BookData book_id="somebook" isbn="0123456789">
   <Title>Interesting Book</Title>
   <TitleLong>Interesting Book: Read it or else..</TitleLong>
   <AuthorsText>John Doe</AuthorsText>
   <PublisherText>Acme Publishing</PublisherText>
  </BookData>
 </BookList>
</ISBNdb>"""
    _contexts = {}
    _units = {}
    def get(self):
        self.response.headers['Content-Type'] = "text/plain"
        source = self.request.get("url")
        xml=self._someString
        if (len(source) > 0):
            #source = "http://www.w3schools.com/XML/note.xml"
            #source = "http://localhost:8080/xbrl/File2011-01-155475.xbrl"
            # [Eran] TODO - avoid recursion
            result = urlfetch.fetch(url=source, deadline=10)
            if (result.status_code == 200):
                self.response.out.write("Parsing XML from url: " + source + "\n")
                xml = result.content
            else:
                self.response.out.write("Bad url: " + source + "\nUsing hardcoded string instead\n")
        else:
            self.response.out.write("Parsing some hard-coded string\n")

        try:                                  
            tree = ET.fromstring(xml)
            json = self.convertToJson(tree)
        except (TypeError):            
            self.response.out.write('Failed to convert xml to json\n')
            return
        
        jsonstr = simplejson.dumps(json)
        self.response.out.write(jsonstr)
        self.response.out.write("\n\nLen: " + str(len(jsonstr)) + "\n")
        
    def convertToJson(self, tree):
        """ Convert the given xml tree to JSON.
            The conversion is done in the following manner:
            Elements are converted to json objects in case they have further children.
            Attributes are converted to json object properties.
            Empty or nil elements are dropped all together
        
            @param tree: The xml tree to convert
        """
        jsonObj = {}
        self._contexts = {}
        self._units = {}
        for elem in tree.getiterator():
            self._convertToJsonHelper(elem, jsonObj)
        
        jsonObj['contexts'] = self._contexts
        jsonObj['units'] = self._units
        
        return jsonObj
            
    def _convertToJsonHelper(self, elem, jsonObj):        
        def normalize(name):
            if name[0] == "{":
                tag = name[1:].split("}")[1]
                return tag
            else:
                return name
        
        if len(elem.attrib) > 0 or len(elem) > 0:
            # skip nil elements
            if ("{http://www.w3.org/2001/XMLSchema-instance}nil" in elem.attrib and elem.attrib["{http://www.w3.org/2001/XMLSchema-instance}nil"] == "true"):
                return
            
            tag = normalize(elem.tag)
            
            if tag == "context" or tag == "unit":
                if "id" in elem.attrib:
                    ref = {}
                    key = elem.attrib["id"]
                    collection = self._contexts if tag == "context" else self._units
                    collection[key] = ref;
                    for subelem in elem:
                        subtag = normalize(subelem.tag)
                        if subtag != "entity":
                            self._convertToJsonHelper(subelem, ref)
                return
            
            currentObj = jsonObj[tag] = {}
            
            for key,value in elem.attrib.items():
                #if key == "unitRef":
                #    currentObj['unit'] = self._units[value]
                #    continue
                #elif key == "contextRef":
                #    currentObj['context'] = self._contexts[value]
                #    continue
                
                currentObj[normalize(key)] = value
            
            if not elem.text is None:
                text = elem.text.strip()
                if text != "":
                    currentObj["value"] = elem.text
                
            for subelem in elem:
                self._convertToJsonHelper(subelem, currentObj)
        else:
            jsonObj[normalize(elem.tag)] = elem.text
        
def main():
    application = webapp.WSGIApplication([
        ('/', MainHandler),
        ('/test', XML2JSON),
        ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

