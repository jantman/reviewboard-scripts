#!/usr/bin/env python
"""
A script using the ReviewBoard API Client
  <https://pypi.python.org/pypi/RBTools/0.2>
  <http://www.reviewboard.org/docs/rbtools/dev/api/>
To iterate all open reviews for a given repository,
parse out the new commit hash of each diff in the review,
and list any reviews with all commit hashes already merged
into master (or another specified branch).

i.e. try to list all reviews that have been merged but
not yet marked as submitted.

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
    :param masterbranch: the ref spec for the master branch to diff against, in format remote/branch
    :type masterbranch: string
    :param verbose: print verbose output to STDOUT
    :type verbose: boolean (default False)

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
    remote.fetch()
    uri = remote.url
    if verbose:
        print("\tremote uri is %s" % uri)

    return (repo, uri)

def is_diff_in_branch(diff, repo, masterbranch, verbose=False):
    """
    Return True if the given diff is already in (merged into)
    the specified branch, else return False.

    :param diff: ReviewBoard diff object
    :type diff: rbtools.api.resource.DiffResource
    :param repo: Git Repository to check
    :type repo: git.repo.base.Repo
    :param masterbranch: the ref spec for the master branch to diff against, in format remote/branch
    :type masterbranch: string
    :param verbose: print verbose output to STDOUT
    :type verbose: boolean (default False)

    :rtype: boolean
    :returns: True if diff is merged into branch_name, False otherwise
    """
    remote_name, remote_branch_name = masterbranch.split("/")
    ref = repo.remote(remote_name).refs[remote_branch_name]
    for f in diff.get_files():
        p = f.get_patch().data
        fname = f.fields['dest_file'] # there's also source_file, that we need for removed files
        file_sha = f.fields['dest_detail']
        src_rev = f.fields['source_revision'] # "PRE-CREATION" if new file
        # TODO - LEFT OFF HERE
        if verbose:
            print("\tfile %s (%s)" % (fname, file_sha))
        if fname not in ref.commit.tree:
            if verbose:
                print("\t-> not in git tree; return False")
            return False
        break
    return False

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

    rb_repo = get_repository_by_uri(root, repo_uri, match_path_end=options.pathend, verbose=VERBOSE)
    if rb_repo is None:
        raise SystemExit("Could not find ReviewBoard repository with uri '%s'" % repo_uri)

    reviews = get_reviews_for_repo(root, rb_repo.id, only_open=True, verbose=VERBOSE)

    if len(reviews) == 0:
        print("No open reviews found for repository %s (%s)" % (repo_origin, options.git_path))
        return True

    for rev in reviews:
        if VERBOSE:
            print("checking review %d" % rev.id)
        diff = get_latest_diff_for_review(rev, verbose=VERBOSE)
        res = is_diff_in_branch(diff, repo, options.master_branch, verbose=VERBOSE)
        if res:
            print("MERGED: Review %d appears to be merged to %s but not submitted." % (rev.id, options.master_branch))
            continue
        if VERBOSE:
            print("Review %d does NOT appear to be merged yet." % rev.id)
        return True # DEBUG - only look at one
    return True

if __name__ == '__main__':
    # if the program is executed directly parse the command line options
    # and read the text to paste from stdin
    main()
