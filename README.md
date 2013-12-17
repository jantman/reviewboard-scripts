reviewboard-scripts
===================

Collection of scripts that use the ReviewBoard python client (RBClient) to
perform various tasks with ReviewBoard.

Requirements
------------

Requirements differ by script, but in general, they require RBTools >= 0.5.2.
Some of the scripts use GitPython to access and manipulate git
repositories on disk. They require **GitPython >= 0.3.2.RC1**. Since this is a RC,
you must explicitly specify the version when you `pip install` it, or else
you'll end up with 0.1.7, which exposes an older, more limited API and will
fail with mysterious errors.

Scripts
=======

check_for_review.py
-------------------

Relatively complex review checking script, intended to be used in CI workflows
to approve or block a merge.

Given:

* the reviewboard name of a git repository
* the path to a local checkout of that repository
* the name of a branch in the repository
* optionally, a master/parent branch name (default "origin/master")

The script will:

* confirm that there is exactly one open review for that branch in that repo
* confirm that the review is shipped at least --shipits times **since the last change**
* find the git diff of that branch against the master branch and confirm that
  reviewboard and git diffs match (the files listed in them are the same, and
  the content of the actual diffs is identical)

Assuming all of these conditions are met, the script will exit 0. Otherwise,
it will exit non-0 with a (hopefully) informative message.

This script uses the rbconfig.py module for credentials.

list_mine.py
------------

Very simple utility script to list pending (open) reviews for a given user or
group, up to a maximum number (hard-coded default of 5). Outputs reviews with
the number, submitter and summary. Intended to be called by the
willie_reviews.py script.

rbconfig.py
-----------

A really simple module that defines three variables, RB_URL, RB_USER and RB_PASSWORD. In
order to authenticate to ReviewBoard, other scripts/modules just:

    from rbconfig import RB_URL, RB_USER, RB_PASSWORD

Unfortunately some scripts use the RB_URL variable, and some require a command
line argument with it. I suppose that's a bug to be fixed.

rbhelpers.py
------------

A module with helper methods for interacting with the RBClient package.

* get_repository_id_by_name(root, repo_name) - given a RBClient root resource,
  find and return a Repository object for the repository with the given name,
  iterating over the paged API results until it is found.
* get_reviews_for_branch(root, repo, branch) - given a RBClient root resource,
  a repository name string, and a branch name string, find and return all open
  reviews for that branch in that repository.

rb_submit_all.py
----------------

Script to list or close all open reviews for a given user. Handy for both
cleanup and off-boarding.

submit_review.py
----------------

Script to submit the (any open) review for a specific repository, with a
latest diff at a specific commit. Used by our Jenkins CI system to submit
reviews after a merge-to-master job runs.

willie_reviews.py
-----------------

A plugin for the [Willie](http://willie.dftba.net/) IRC bot to list open
reviews targeting a specific user or group, using a channel-to-group mapping
for the latter.

The Future
==========

Ideally, I'd like to combine all of the useful methods here into a reusable
module (probably rbhelpers.py), and base everything else off of that. It's
slowly moving in that direction, with the hope that "from rbhelpers import x"
could be useful to people other than me. I suppose it should be packaged too.

Copyright, Disclaimer
=====================

Most of these scripts were whipped up on the spot to complete a given task,
and may not even have been run a second time once the task was done. Some are
used on a daily basis. This is all warranty-free. It might work, it might
break your reviewboard server or git repo. You've been warned.

Most of this work was done at my current employer, [Cox Media Group Technology](http://cmgdigital.com/). 
With the exception of one or two scripts, none of it was an actual project or
ticket, just a means to an end. I've done my best to clearly delineate which
scripts were done at/for CMGT, and which I wrote on my own time.
