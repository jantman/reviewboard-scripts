#!/usr/bin/env python2

from rbtools.api.client import RBClient
from rbconfig import RB_URL
import sys
import optparse

def get_open_reviews(root, user):
    req = root.get_review_requests(from_user=user, status="pending", max_results=400)
    reviews = []
    for review in req:
        reviews.append(review)
    return reviews

def list_open_reviews(root, user):
    rev = get_open_reviews(root, user)
    for review in rev:
        try:
            repo = review.get_repository()
            repo = repo.path.split('/')[-1]
        except:
            repo = ""
        print "%d - %s (%s)" % (review.id, repo, review.last_updated)
        print "\t%s\n\t%s" % (review.url, review.summary)
    print "\n\nGot %d pending/unsubmitted reviews posted by %s" % (len(rev), user)

def close_open_reviews(root, user):
    reviews = get_open_reviews(root, user)
    print "Got %d pending/unsubmitted reviews posted by %s" % (len(reviews), user)
    for rev in reviews:
        print "Closing review %d (%s)" % (rev.id, rev.summary)
        rev.update(status='submitted')
    print "\n\nSubmitted %d pending/unsubmitted reviews posted by %s" % (len(reviews), user)
    return True

if __name__ == '__main__':
    # if the program is executed directly parse the command line options
    # and read the text to paste from stdin

    parser = optparse.OptionParser()
    parser.add_option('-u', '--user', dest='user',
                      help='user to check reviews for / limit to reviews posted by this user')

    parser.add_option('-l', '--list', dest='list', default=False, action='store_true',
                       help='list open reviews posted by user')

    parser.add_option('-c', '--close', dest='close', default=False, action='store_true',
                      help='close all open reviews posted by user')

    options, args = parser.parse_args()

    if not options.user:
        print "ERROR: You must specify a user to list/close reviews for (-u|--user)"
        sys.exit(2)

    if (options.list and options.close) or (not options.list and not options.close):
        print "ERROR: you must specify either -l|--list OR -c|--close"
        sys.exit(2)

    client = RBClient(RB_URL)
    root = client.get_root()

    if not root:
        print "Error - could not get RBClient root."
        sys.exit(1)

    if options.list:
        list_open_reviews(root, options.user)
    elif options.close:
        close_open_reviews(root, options.user)
