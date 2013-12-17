"""
Module to query reviewboard pending reviews targeted at a user, group
or channel (using a channel-to-group mapping).
"""

from rbtools.api.client import RBClient
from rbconfig import RB_URL
import re

MAX_RESULTS_CHANNEL = 5
MAX_RESULTS_PM = 10

CHANNEL_GROUP_MAPPING = {'#tech-ops': 'Ops', '#automation': 'automation'}

def get_open_reviews(args):
    """
    get open reviews to a specified user, group, etc.
    """
    args['status'] = 'pending'
    if 'max_results' not in args:
        args['max_results'] = 100

    client = RBClient(RB_URL)
    root = client.get_root()
    if not root:
        print "Error - could not get RBClient root."
        return False

    req = root.get_review_requests(**args)
    ret = {'total': req.total_results, 'reviews': []}
    for review in req:
        ret['reviews'].append("(%s) %s <%s/r/%d/>" % (review.get_submitter().username, review.summary, RB_URL, review.id))
    return ret

def get_res_limit(sender):
    """
    Gets the integer results limit, depending on whether
    sender is a channel or a user (PM).

    @param sender string, trigger.sender
    """
    if sender[0] == '#':
        return MAX_RESULTS_CHANNEL
    return MAX_RESULTS_PM

def reviews_get(willie, trigger, for_type, spec):
    """
    Return a list of reviews for a user or group
    """
    max_res = get_res_limit(trigger.sender)
    if for_type == 'user':
        l = get_open_reviews({'to_users': spec, 'max_results': max_res})
    else:
        l = get_open_reviews({'to_groups': spec, 'max_results': max_res})

    if l is False:
        willie.say("Error getting reviews for %s %s." % (for_type, spec))
        return True
    if l['total'] < 1:
        willie.say("Found %d pending reviews for %s '%s'." % (l['total'], for_type, spec))
        return True
    if l['total'] < max_res:
        willie.say("Found %d pending reviews for %s '%s':" % (l['total'], for_type, spec))
    else:
        willie.say("Found %d pending reviews for %s '%s'. First %s:" % (l['total'], for_type, spec, max_res))
    for r in l['reviews']:
        willie.say(r)

def reviews(willie, trigger):
    """
    In channel, display pending reviews for the group that the channel maps to.
    In PM, display pending reviews for the asking user.
    """
    if trigger.sender[0] == '#':
        # in channel
        if trigger.sender not in CHANNEL_GROUP_MAPPING:
            willie.say("Error: no channel-to-group mapping for channel %s." % trigger.sender)
            return True
        # else do the lookup for the channel
        reviews_get(willie, trigger, 'group', CHANNEL_GROUP_MAPPING[trigger.sender])
    else:
        # just a user in PM
        reviews_get(willie, trigger, 'user', trigger.nick)

def reviews_user(willie, trigger):
    """
    Display pending reviews for a specified user
    """
    reviews_get(willie, trigger, 'user', trigger.group(1))

def reviews_me(willie, trigger):
    """
    Display pending reviews for the asking user
    """
    reviews_get(willie, trigger, 'user', trigger.nick)

def reviews_group(willie, trigger):
    """
    Display pending reviews for a RB group name
    """
    reviews_get(willie, trigger, 'group', trigger.group(1))

def reviews_display_help(willie, trigger):
    willie.say("Usage:  reviews (in channel) - list open reviews for this channel's group.   reviews (private) - list open reviews for your user.   reviews me - list open reviews for your user.   reviews user <username> - show open reviews for RB user <username>.   reviews group <group> - show open reviews for RB group <group>.")
    willie.say("All lists limited to %d results in public channels and %d results in private messages." % (MAX_RESULTS_CHANNEL, MAX_RESULTS_PM))

reviews_display_help.rule = r'^reviews help\??$'
reviews_display_help.priority = "medium"

reviews.rule = r'^reviews$'
reviews.priority = 'medium'

reviews_user.rule = r'^reviews user (.*)$'
reviews_user.priority = 'medium'

reviews_me.rule = r'^reviews me$'
reviews_me.priority = 'medium'

reviews_group.rule = r'^reviews group (.*)$'
reviews_group.priority = 'medium'
