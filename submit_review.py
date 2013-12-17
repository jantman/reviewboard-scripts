#!/usr/bin/env python
"""
A script using the ReviewBoard API Client
  <https://pypi.python.org/pypi/RBTools/0.2>
  <http://www.reviewboard.org/docs/rbtools/dev/api/>
to submit the review for a specific branch, at a specific commit.

requires:
rbtools
GitPython

"""

from rbtools.api.client import RBClient
import optparse
import sys
import datetime
import re
import subprocess

from puppetconfig import RB_USER, RB_PASSWORD
from rbhelpers import get_reviews_for_branch, get_repository_id_by_name

if __name__ == '__main__':
    # if the program is executed directly parse the command line options
    # and read the text to paste from stdin

    parser = optparse.OptionParser()
    parser.add_option('-r', '--repo', dest='repo', action="store", type="string",
                      help='find reviews for this repository')

    parser.add_option('-b', '--branch', dest='branch', action="store", type="string",
                       help='find reviews for this branch')

    parser.add_option('-v', '--verbose', dest='verbose', action="store_true", default=False,
                       help='verbose/debug output')

    parser.add_option('-u', '--url', dest='url', action="store", type="string",
                       help='reviewboard server url')

    parser.add_option('-m', '--message', dest='message', action="store", type="string",
                      help='review submit message/description')

    options, args = parser.parse_args()

    VERBOSE = False
    if options.verbose:
        VERBOSE = True

    if not options.url:
        print("ERROR: You must specify a reviewboard server URL (-u|--url) to use")
        sys.exit(2)

    if not options.repo:
        print("ERROR: You must specify a repo (-r|--repo) to find reviews for")
        sys.exit(2)

    if not options.branch:
        print("ERROR: You must specify a branch (-b|--branch) to find reviews for")
        sys.exit(2)

    client = RBClient(options.url, username=RB_USER, password=RB_PASSWORD)
    root = client.get_root()
    if not root:
        print("Error - could not get RBClient root.")
        sys.exit(1)

    repo = get_repository_id_by_name(root, options.repo, verbose=VERBOSE)
    if repo is None:
        print("ERROR: Could not find ReviewBoard repository with name '%s'" % options.repo)
        sys.exit(3)

    reviews = get_reviews_for_branch(root, repo, options.branch, verbose=VERBOSE)
    if len(reviews) == 0:
        print("ERROR: No open reviews found for branch %s in repo %s" % (options.branch, repo))
        sys.exit(4)
    if len(reviews) > 1:
        print("ERROR: Multiple open reviews found for branch %s in repo %s" % (repo, options.branch))
        sys.exit(5)

    # ok, we have ONE review for the branch
    review = reviews[0]
    print("Found review %d" % review.id)

    rb_data = {'status': 'submitted'}
    if options.message:
        rb_data['description'] = options.message

    print("Submitting review %d" % review.id)
    review.update(data=rb_data)
