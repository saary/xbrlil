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

from google.appengine.ext import db
from django.utils import simplejson
from xml.etree import ElementTree as ET

import JSONUtils

class JSONProperty(db.TextProperty):
    """Custom db property for holding JSON blobs"""
    def validate(self, value):
        return value

    def get_value_for_datastore(self, model_instance):
        value = super(JSONProperty, self).get_value_for_datastore(model_instance)
        return db.Text(simplejson.dumps(value))

    def make_value_from_datastore(self, value):
        if value is None:
            return {}
        if isinstance(value, basestring):
            return simplejson.loads(value)
        return value
        
class IndexedJsonEntity(db.Expando):
    """ Datastorable JSON """
    json = JSONProperty()
    
class IndexedJsonFactory:
    """ Get an datastorable JSON with searchable indices
        Currently only support text indices
    """
        
    def fromElementTree(self, tree, indices):
        """ Return indexed JSON representation of XML ElementTree
        @param tree - xml tree
        @param indices - dictionary of searchable fields and their type
        """

        json = {}
        try:                                  
            json = JSONUtils.convertToJson(tree)
        except (TypeError):            
            logging.error('IndexedJsonFactory.fromElementTree: Error converting to JSON')
            return None

        return self.fromJson(json, indices)
    
    def fromJson(self, json, indices):
        """ Return indexed JSON representation of a JSON dictionary
        @param json - JSON dictionary 
        @param indices - dictionary of searchable fields and their type
        """

        #IndexedJsonEntity = classobj('IndexedJsonEntity', (JsonEntity,db.Expando), indices)
        indexedJson = IndexedJsonEntity() 
        
        indexedJson.json = json
        for key in indices.keys():
            # logging.info('checking key: ' + key )
            if key in json:
                #logging.info('setattr: ' + key + " = " + json[key]['value'])
                setattr(indexedJson, key, json[key]['value'])
            else:
                logging.warning('Couldn\'t find key in JSON dictionary ' + key)
                
            
        return indexedJson

        
