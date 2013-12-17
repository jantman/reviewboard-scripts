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

from rbtools.api.client import RBClient
import optparse
import sys
import datetime
import re
import subprocess

from git import *

from rbconfig import RB_USER, RB_PASSWORD
from rbhelpers import get_reviews_for_branch, get_repository_id_by_name

def get_git_diffs(branchname, path, masterbranch, verbose=False):
    """
    Get a git diff against masterbranch. Uses GitPython to fetch and
    pull, then Popen to run "git diff masterbranch", since GitPython
    can't give us a unified diff.

    NOTE that this does a git fetch and pull.

    @param branchname string, name of the branch to diff
    @param path string, path to the local git checkout to use
    @param mastername string, name of the branch to diff against

    @return a dict of filename => patch
    """
    repo = Repo(path)
    if repo.bare:
        print("ERROR: repo at %s is bare, failing." % path)
        sys.exit(2)

    if repo.is_dirty():
        print("Specified repository '%s' is dirty, cannot run tests." % path)
        sys.exit(2)

    remote_name, remote_branch_name = masterbranch.split("/")

    # find our remote, and fetch
    if verbose > 0:
        print("\tadding and fetching remote repo %s" % remote_name)
    remote = repo.remote(remote_name)
    remote.fetch()

    # make sure we have the target branch in the remote
    have_ref = False
    for r in remote.refs:
        if str(r) == "%s/%s" % (remote_name, branchname):
            have_ref = True
    if have_ref is False:
        print("ERROR: remote does not seem to have '%s' branch." % branchname)
        sys.exit(2)

    if verbose > 0:
        print("\tchecking out master branch %s, current head is %s" % (remote_branch_name, repo.head.commit))
    # checkout master branch
    repo.heads[remote_branch_name].checkout()
    if verbose > 0:
        print("\tchecked out, head is at %s" % repo.head.commit)
    # pull from remote
    if verbose > 0:
        print("\tpulling from remote")
    remote.pull()
    if verbose > 0:
        print("\tpulled, head is at %s" % repo.head.commit)
    # switch back to our branch
    if verbose > 0:
        print("\tchecking out local branch %s, current head is at %s" % (branchname, repo.head.commit))
    repo.heads[branchname].checkout()
    if verbose > 0:
        print("\tchecked out, head is at %s" % repo.head.commit)

    # now get a diff
    cmd = "git diff --name-only %s 2>/dev/null" % masterbranch
    if verbose > 0:
        print("\t running command: %s" % cmd)
    output = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, cwd=path).communicate()[0]
    if verbose > 0:
        print("\treceived output with length %d" % len(output))

    diffs = {}

    lines = output.split("\n")
    for line in lines:
        fname = line.strip()
        if fname == "":
            continue
        # get a diff of the file
        cmd = "git diff --full-index %s %s 2>/dev/null" % (masterbranch, fname)
        if verbose > 0:
            print("\t running command: %s" % cmd)
        output = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, cwd=path).communicate()[0]
        if verbose > 0:
            print("\treceived output with length %d" % len(output))
        diffs[fname] = output

    return diffs

def parse_rb_time_string(s):
    """
    Unfortunately, the RB API gives us back "timestamps"
    in a non-standard string format, something like:
        2013-09-26T17:22:45.108Z
    AFAIK python can't easily parse this, so we do
    a bit of massaging before we parse it.

    @param s string, time representation to parse

    @return datetime.datetime object
    """
    tz = s[23:]
    if tz == "Z":
        tz = "UTC"
    s = s[0:23] + "000" + tz
    dt = datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f%Z")
    return dt

def compare_diffs(git_diff, rb_diff, verbose=False):
    """
    Compare two diffs (well, patches);
    return True if they're the same, false if they're not.

    For now we're just doing pure string comparison, but this
    provides an extension point if we need to deal with any special cases.

    @param git_diff string, the per-file diff (patch) from git
    @param rb_diff string, the per-file diff (patch) from reviewboard

    @return boolean, True if same, False otherwise
    """

    if git_diff != rb_diff:
        if verbose:
            print("#### git diff of %s ####" % f)
            print(git_diffs[f])
            print("\n#### reviewboard diff of %s ####" % f)
            print(diffs['patches'][f])
            print("\n#### END DIFFS for file %s ####" % f)
        return False
    return True

def get_latest_diffs_for_review(review, verbose=False):
    """
    Return a dict containing the timestamp of the latest diff for a review,
    and a dict of all file paths in the diff, with their patches.

    @param review a RBClient Review resource
    @return dict, 'timestamp' => string timestamp for the diff
                  'patches'   => {'filename': 'patch', ...}
    """
    diffs = review.get_diffs()
    ndiffs = diffs.total_results
    if ndiffs == 0:
        return None

    latest_diff = None
    for diff in diffs:
        if diff.revision == ndiffs:
            if verbose:
                print("\tfound %s diffs, returning the last one (revision %d)" % (ndiffs, diff.revision))
            latest_diff = diff
    if latest_diff is None:
        return None
    # we have a latest diff
    ret = {'patches': {}}
    ret['timestamp'] = latest_diff.timestamp

    # build array of patches for each file
    for f in latest_diff.get_files():
        ret['patches'][f.fields['dest_file']] = f.get_patch().data
    return ret

if __name__ == '__main__':
    # if the program is executed directly parse the command line options
    # and read the text to paste from stdin

    parser = optparse.OptionParser()
    parser.add_option('-r', '--repo', dest='repo', action="store", type="string",
                      help='find reviews for this repository')

    parser.add_option('-b', '--branch', dest='branch', action="store", type="string",
                       help='find reviews for this branch')

    parser.add_option('-c', '--commit', dest='commit', action="store", type="string",
                       help='find reviews at this commit')

    parser.add_option('-s', '--shipits', dest='shipits', default=2, action="store", type="int",
                      help='require at least this many shipits (default 2)')

    parser.add_option('-v', '--verbose', dest='verbose', action="store_true", default=False,
                       help='verbose/debug output')

    parser.add_option('-u', '--url', dest='url', action="store", type="string",
                       help='reviewboard server url')

    parser.add_option('-g', '--git-dir', dest='git_path', action="store", type="string",
                      help='absolute path to current checkout of this git branch')

    parser.add_option('-m', '--master-branch', dest='master_branch', action="store", type="string",
                      default="origin/master",
                      help='master branch to diff against, default origin/master')

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

    # get the latest diff for the review
    diffs = get_latest_diffs_for_review(review, verbose=VERBOSE)
    diff_time = parse_rb_time_string(diffs['timestamp'])
    if diff_time is None:
        print("ERROR: could not parse timestamp for diff %d" % diff.id)
        sys.exit(2)

    # check that it's shipped x{options.shipits} since the last update
    shipits = []
    reviews = review.get_reviews()
    for r in reviews:
        if r.ship_it is False:
            continue
        ts = parse_rb_time_string(r.timestamp)
        if ts <= diff_time:
            if VERBOSE:
                print("\tskipping review %d, timestamp (%s) before last diff upload (%s)" % (r.id, ts, diff_time))
            continue
        if r.public is False:
            continue
        user = r.get_user().username
        if VERBOSE:
            print("\tfound shipped review since last diff, id %d, user %s" % (r.id, user))
        shipits.append("%s (%d)" % (user, r.id))

    # note that this implicitly does a fetch and pull
    git_diffs = get_git_diffs(options.branch, options.git_path, options.master_branch, verbose=VERBOSE)

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
