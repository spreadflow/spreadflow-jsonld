from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
from pyld import jsonld

from spreadflow_delta.proc import MapReduceBase, UnpackBase


class JsonLdUnpackBase(UnpackBase):
    """
    Generates JSON-LD keywords (e.g. @id, @context, @type) for the given
    subjects and replaces embedded objects with subject references.
    """

    def _replace_by_reference(self, value, refmap):
        if id(value) in refmap:
            return refmap[id(value)]
        elif isinstance(value, collections.Mapping):
            return {k: self._replace_by_reference(v, refmap) for k, v in value.items()}
        elif isinstance(value, collections.Iterable) and not isinstance(value, (str, unicode, bytearray, buffer)):
            return [self._replace_by_reference(v, refmap) for v in value]
        else:
            return value

    def unpack(self, key, doc):
        subjects = doc[self.key]
        keywords = [self.keywords(subj) for subj in subjects]
        pairs = zip(subjects, keywords)
        refmap = {id(subj): {'@id': kws['@id']} for subj, kws in pairs}
        for subj, kws in pairs:
            result = {k: self._replace_by_reference(v, refmap) for k, v in subj.items()}
            result.update(kws)
            yield result

    def keywords(self, subject):
        idkw = subject.get('@id', hash(subject))
        return {'@id': idkw}


class JsonLdUnpack(JsonLdUnpackBase):
    def __init__(self, key, func, *args, **kwds):
        super(JsonLdUnpack, self).__init__(key)
        self._unpack_func = func
        self._unpack_args = args
        self._unpack_kwds = kwds

    def keywords(self, subject):
        return self._unpack_func(subject, *self._unpack_args, **self._unpack_kwds)


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
