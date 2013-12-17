#!/usr/bin/env python2
#
# A script using the ReviewBoard API Client
#   <https://pypi.python.org/pypi/RBTools/0.2>
#   <http://www.reviewboard.org/docs/rbtools/dev/api/>
# to get all pending reviews targeting a specific user or group
#

from rbtools.api.client import RBClient
from rbconfig import RB_URL
import optparse
import sys

MAX_RESULTS = 5

def get_open_reviews(args):
    # get open reviews to a specified user, group, etc.
    args['status'] = 'pending'
    args['max_results'] = MAX_RESULTS

    client = RBClient(RB_URL)
    root = client.get_root()
    if not root:
        print "Error - could not get RBClient root."
        return False

    req = root.get_review_requests(**args)
    print "\n\nGot %d pending/unsubmitted reviews" % req.total_results
    for review in req:
        print "%d - %s - %s" % (review.id, review.get_submitter().username, review.summary)

if __name__ == '__main__':
    # if the program is executed directly parse the command line options
    # and read the text to paste from stdin

    parser = optparse.OptionParser()
    parser.add_option('-u', '--user', dest='user',
                      help='find reviews targeting this user or a group they are in')

    parser.add_option('-g', '--group', dest='group',
                       help='find reviews targeting this group')

    options, args = parser.parse_args()

    if options.user:
        foo = get_open_reviews({'to_users': options.user})
    elif options.group:
        foo = get_open_reviews({'to_groups': options.group})
    else:
        print "ERROR: You must specify either a user (-u) or group (-g) to find reviews for"
        sys.exit(2)

    if foo == False:
        print "ERROR - could not get results."
        sys.exit(1)

    print foo
