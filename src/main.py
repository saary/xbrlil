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
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util


class MainHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write('Hello world!')

from google.appengine.api import urlfetch                      

from xml.etree import ElementTree as etree
from xml.etree.ElementTree import parse
import pesterfish

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
            tree = etree.fromstring(xml)
            json = pesterfish.to_pesterfish(tree)
        except (TypeError):            
            json = "pesterfish failed"         

        self.response.out.write('Json result:\n' + json)

def main():
    application = webapp.WSGIApplication([
        ('/', MainHandler),
        ('/test', XML2JSON),
        ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

