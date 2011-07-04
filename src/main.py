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
from new import classobj

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import urlfetch
from google.appengine.ext import db

from django.utils import simplejson
from xml.etree import ElementTree as ET

from backend.model import IndexedJsonEntity, IndexedJsonFactory
import JSONUtils

_searchIndices = { 'identifier': db.StringProperty, 
                    'EnglishNameOfReportingEntity': db.StringProperty, 
                    'HebrewNameOfReportingEntity' : db.StringProperty }

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write('Hello world!')

class XML2JSONHandler(webapp.RequestHandler):
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
    
    def getXMLFromURL(self, url):
        result = urlfetch.fetch(url=url, deadline=10)
        if (result.status_code == 200):
            self.response.out.write("Parsing XML from url: " + url + "\n")
            return result.content
        else:
            self.response.out.write("Error fetching XML from URL:" + url + "\n")
            return None

    def storeTreeAsIndexedJSON(self, tree):
        indexedJsonFactory = IndexedJsonFactory()
        indices = _searchIndices

        for key in indices.keys():
            self.response.out.write('Adding searchable field ' + key + '\n')

        indexedJson = indexedJsonFactory.fromElementTree(tree, indices)
        if (indexedJson == None):
            self.response.out.write('Failed to convert xml to indexed JSON\n')
            return

        indexedJson.put()
        logging.info("XML2JSONHandler.storeTreeAsIndexedJSON: added to store!")

        return indexedJson

    def get(self):
        show = False
        addToDatastore = False
        xml=self._someString

        self.response.headers['Content-Type'] = "text/plain"
        addToDatastore = (self.request.get("add") == "1")
        show = (self.request.get("show") == "1")
        source = self.request.get("url")
        if (len(source) > 0):
            #source = "http://www.w3schools.com/XML/note.xml"
            #source = "http://localhost:8080/xbrl/File2011-01-155475.xbrl"
            xml = self.getXMLFromURL(source)
        else:
            xml = self._someString
            self.response.out.write("Parsing test string:\n")
            self.response.out.write(xml + "\n")
            addToDatastore = False

        try:                                  
            tree = ET.fromstring(xml)
        except (TypeError):            
            self.response.out.write('Failed XML parsing\n')
            return

        if addToDatastore:
            indexedJSON = self.storeTreeAsIndexedJSON(tree)
            json = indexedJSON.json
        else:
            json = JSONUtils.convertToJson(tree)
        
        if show:
            self.response.out.write("JSON output:\n")
            self.response.out.write(json)
            self.response.out.write("\n")

        
class QueryHandler(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = "text/plain"
        showAll = False
        fieldName = self.request.get("fieldName")
        logging.info("fieldName = " + fieldName)
        fieldValue = self.request.get("fieldValue")
        logging.info("fieldValue = " + fieldValue)
        if (len(fieldName) == 0) or (len(fieldValue) == 0):
            self.response.out.write('Empty search parameter. Showing all\n')
            showAll = True
        if not ( fieldName in _searchIndices):
            self.response.out.write(fieldName + 'is not a searchable field. Showing all\n')
            showAll = True

        if (showAll):
            q = db.GqlQuery("SELECT * FROM IndexedJsonEntity " +
                            "ORDER BY EnglishNameOfReportingEntity DESC" )
            self.response.out.write("Query is: SELECT * FROM IndexedJsonEntity \n" +
                                    "          ORDER BY EnglishNameOfReportingEntity DESC\n" )
        else:
            q = db.GqlQuery("SELECT * FROM IndexedJsonEntity " + 
                            "WHERE " + fieldName + " = :1", fieldValue)
            self.response.out.write("Query is: SELECT * FROM IndexedJsonEntity \n" + 
                                    "          WHERE " + fieldName +" = " + fieldValue +"\n" )

        self.response.out.write("\nResults:\n")
        
        results = q.fetch(15)
        ind = 1
        for p in results:
            self.response.out.write(repr(ind) + ". ")
            self.response.out.write(p.json)
            self.response.out.write("\n")
            ind = ind + 1

        self.response.out.write("\n")
        

def main():
    application = webapp.WSGIApplication([
        ('/', MainHandler),
        ('/test', XML2JSONHandler),
        ('/q', QueryHandler),
        ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

