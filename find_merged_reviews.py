#!/usr/bin/env python
"""
A script using the ReviewBoard API Client
  <https://pypi.python.org/pypi/RBTools/0.2>
  <http://www.reviewboard.org/docs/rbtools/dev/api/>
to find reviews for a specific branch, at a specific commit,
and make sure it's shipped.

requires:
rbtools
GitPython

"""

import optparse
import sys
import os
import re

from git import *
from rbtools.api.client import RBClient

from rbconfig import RB_USER, RB_PASSWORD
from rbhelpers import *

import pprint # DEBUG

def git_get_origin_uri(path, masterbranch, verbose=False):
    """
    Get the origin URI for a given git repository on disk.

    raises SystemExit

    :param path: path to the local git checkout to use
    :type path: string
    :param masterbranch: the ref spec for the master branch to diff against
    :type masterbranch: string

    :returns: tuple of (uri, Repo object)
    """
    repo = Repo(path)
    if repo.bare:
        raise SystemExit("repo at %s is bare." % path)

    remote_name, remote_branch_name = masterbranch.split("/")

    # find our remote, and fetch
    if verbose:
        print("\tremote name is %s" % remote_name)
    uri = None
    remote = repo.remote(remote_name)
    uri = remote.url
    if verbose:
        print("\tremote uri is %s" % uri)

    return (repo, uri)

def main():
    """
    Main function
    """
    url = None
    try:
        from rbconfig import RB_URL
        url = RB_URL
    except:
        url = None

    parser = optparse.OptionParser()
    parser.add_option('-g', '--git-dir', dest='git_path', action="store", type="string",
                      default=os.path.abspath(os.path.realpath(os.getcwd())),
                      help='absolute path to current checkout of this git branch - default is cwd')

    parser.add_option('-u', '--url', dest='url', action="store", type="string", default=url,
                       help='reviewboard server url')

    parser.add_option('-m', '--master-branch', dest='master_branch', action="store", type="string",
                      default="origin/master",
                      help='master branch to check for merge to, default origin/master')

    parser.add_option('-v', '--verbose', dest='verbose', action="store_true", default=False,
                       help='verbose/debug output')

    parser.add_option('--match-path-end', dest='pathend', action="store_true", default=False,
                      help='in addition to URI matching, match repository if the reviewboard repo "path" matches the end of the repo URI.')

    options, args = parser.parse_args()

    VERBOSE = False
    if options.verbose:
        VERBOSE = True

    if not re.match('.+/.+', options.master_branch):
        print("ERROR: master branch must be of the format '<remote name>/<branch name>'")
        sys.exit(2)

    if not options.git_path:
        print("ERROR: You must specify the path to a current git checkout of this branch (-g|--git-dir)")
        sys.exit(2)

    if not options.url:
        print("ERROR: You must specify a reviewboard server URL (-u|--url) to use")
        sys.exit(2)

    # RB root api resource
    root = get_rb_root(options.url, username=RB_USER, password=RB_PASSWORD)

    # (repo object, uri string) for git-dir
    (repo, repo_uri) = git_get_origin_uri(options.git_path, options.master_branch, verbose=VERBOSE)

    repo = get_repository_by_uri(root, repo_uri, match_path_end=options.pathend, verbose=VERBOSE)
    if repo is None:
        raise SystemExit("Could not find ReviewBoard repository with uri '%s'" % repo_origin)

    reviews = get_reviews_for_repo(root, repo.id, only_open=True, verbose=VERBOSE)

    if len(reviews) == 0:
        print("No open reviews found for repository %s (%s)" % (repo_origin, options.git_path))
        return True

    for rev in reviews:
        if VERBOSE:
            print("checking review %d" % rev.id)
        diff = get_latest_diff_for_review(rev, verbose=VERBOSE)
        for f in diff.get_files():
            print type(f)
            print dir(f)
            pprint.pprint(f.get_diff_data())
            pprint.pprint(f.get_patch())
            break
        print "#################################################"
        """
        d = diff.get_patch()
        print d
        print type(d)
        print dir(d)
        pprint.pprint(d)
        """
        return False

    return False

    # get the latest diff for the review
    diff_time = parse_rb_time_string(diffs['timestamp'])
    if diff_time is None:
        print("ERROR: could not parse timestamp for diff %d" % diff.id)
        sys.exit(2)

    diffs_ok = True
    for f in git_diffs:
        if f not in diffs['patches']:
            print("ERROR: file '%s' found in git diff but not reviewboard diff." % f)
            diffs_ok = False
            continue
        if compare_diffs(git_diffs[f], diffs['patches'][f], verbose=VERBOSE) is False:
            print("ERROR: git and reviewboard diffs not same for file '%s'" % f)
            diffs_ok = False
    for f in diffs['patches']:
        if f not in git_diffs:
            print("ERROR: file '%s' found in reviewboard diff but not git diff." % f)
            diffs_ok = False

    if diffs_ok is False:
        sys.exit(1)

    # check for shipits
    if len(shipits) < options.shipits:
        print("ERROR: Only found %d shipit(s) since last diff upload, %d are required" % (len(shipits), options.shipits))
        sys.exit(1)
    else:
        print("SHIPPED: Since last diff upload, shipped by: %s" % ", ".join(shipits))
    sys.exit(0)

if __name__ == '__main__':
    # if the program is executed directly parse the command line options
    # and read the text to paste from stdin
    main()
