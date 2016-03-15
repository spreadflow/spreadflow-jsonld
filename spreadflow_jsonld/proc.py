from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
from pyld import jsonld

from spreadflow_delta.proc import MapReduceBase

class JsonLdFlatten(MapReduceBase):
    def __init__(self, context=None, options=None):
        super(JsonLdFlatten, self).__init__(coiterate=True)

        if context is not None:
            self.context = context
        else:
            self.context = {}

        if options is not None:
            self.options = options
        else:
            self.options = {}

    def map(self, key, doc):
        yield doc['@id'], doc

    def reduce(self, key, docs):
        result = jsonld.flatten(docs, self.context, self.options)
        resources = result.pop('@graph')

        n = len(resources)
        if n == 0:
            return {}
        elif n == 1:
            resource = resources.pop()
            resource['@context'] = result.pop('@context')
            return resource
        else:
            raise ValueError('The JSON-LD reduction operation must result in exactly one document.')
