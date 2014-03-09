#!/usr/bin/env python
# encoding: utf-8
#
# Copyright © 2014 deanishe@deanishe.net
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2014-03-08
#

"""
Search for directories matching `query` under directory `root`.

First, a Spotlight search is performed with `mdfind` to find all
folders (and optionally files) under `root` matching the last part of `query`.

Then, earlier parts of `query` are successively matched against the path
components of Spotlight's results.
"""

from __future__ import print_function, unicode_literals

import sys
import os
import subprocess
import argparse
import unicodedata

from workflow import Workflow

log = None


def search_in(root, query, dirs_only=False):
    """Search for files under `root` matching `query`

    If `dirs_only` is True, only search for directories.

    """

    cmd = ['mdfind', '-onlyin', root]
    query = ["(kMDItemFSName == '*{}*'c)".format(query)]
    if dirs_only:
        query.append("(kMDItemContentType == 'public.folder')")
    cmd.append(' && '.join(query))
    log.debug(cmd)
    output = subprocess.check_output(cmd).decode('utf-8')
    output = unicodedata.normalize('NFC', output)
    paths = [s.strip() for s in output.split('\n') if s.strip()]
    log.debug('{:d} hits from Spotlight index'.format(len(paths)))
    return paths


def filter_paths(queries, paths, root):
    """Return subset of `paths` whose path segments contain the elements
    in ``queries` in the same order. Case-insensitive.

    """

    hits = set()
    queries = [q.lower() for q in queries]
    for i, p in enumerate(paths):
        # Split path into lower-case components,
        # removing the last one (matched by Spotlight)
        components = p.replace(root, '').lower().split('/')[:-1]
        matches = 0
        for q in queries:
            for j, s in enumerate(components):
                if q in s:
                    log.debug('{!r} in {!r}'.format(q, components))
                    matches += 1
                    components = components[j:]
                    break
        if matches == len(queries):
            log.debug('match: {!r} --> {!r}'.format(queries, p))
            hits.add(i)
    log.debug('{:d}/{:d} after filtering'.format(len(hits), len(paths)))
    return [p for i, p in enumerate(paths) if i in hits]


def main(wf):
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dirs', action='store_true', dest='dirs_only',
                        help='only search for directories')
    parser.add_argument('root', metavar='DIR', default=None,
                        help='directory to search in')
    parser.add_argument('query', default=None, help='what to search for')
    args = parser.parse_args(wf.args)
    root = args.root
    query = args.query
    query = query.split()  # split on spaces
    if len(query) > 1:
        mdquery = query[-1]
        query = query[:-1]
    else:
        mdquery = query[0]
        query = None

    log.debug('mdquery : {!r}  query : {!r}'.format(mdquery, query))
    paths = search_in(root, mdquery, args.dirs_only)

    if query:
        paths = filter_paths(query, paths, root)

    home = os.path.expanduser('~/')
    for path in paths:
        filename = os.path.basename(path)
        wf.add_item(filename, path.replace(home, '~/'),
                    valid=True, arg=path,
                    autocomplete=filename,
                    uid=path, type='file',
                    icon=path, icontype='fileicon')

    wf.send_feedback()
    log.debug('finished')


if __name__ == '__main__':
    wf = Workflow()
    log = wf.logger
    sys.exit(wf.run(main))
