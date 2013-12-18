# helper methods to work with RBTools API

from rbtools.api.client import RBClient

def get_repository_id_by_name(root, repo_name, verbose=False):
    """
    Return the integer Repository ID for the given name.

    @param repo_name string, name of the repository
    @return integer
    """
    repositories = root.get_repositories()

    count = 0
    try:
        while True:
            for repo in repositories:
                count = count + 1
                if repo.name == repo_name:
                    if verbose:
                        print("\tfound repository id %d with name matching %s" % (repo.id, repo.name))
                    return repo.id
            repositories = repositories.get_next()
    except StopIteration:
        if verbose:
            print("\titerated through %d repositories" % count)
        return None
    if verbose:
        print("\titerated through %d repositories" % count)
    return None

def get_reviews_for_repo(root, repo_id, only_open=False, verbose=False):
    """
    Get a list of open Review objects for the specified repository.

    :param root: RBClient Root resource
    :type root: rbtools.api.resource.RootResource
    :param repo_id: ID of the repository to get reviews for
    :type repo_id: integer
    :param only_open: only get open/pending review requests
    :type only_open: boolean
    :returns: list of Review resources
    :rtype: list
    """
    # get open reviews to a specified user, group, etc.
    args = {}
    args['repository'] = repo_id
    if only_open:
        args['status'] = 'pending'

    ret = []

    requests = root.get_review_requests(**args)
    count = 0
    try:
        while True:
            for req in requests:
                count = count + 1
                ret.append(req)
            requests = requests.get_next()
    except StopIteration:
        if verbose:
            print("\titerated through %d review requests" % count)
        return ret
    if verbose:
        print("\titerated through %d review requests" % count)
    return ret

def get_reviews_for_branch(root, repo_id, branch, verbose=False):
    """
    Gets a list of reviews for the given branch in the given repo

    :param root: RBClient Root resource
    :type root: rbtools.api.resource.RootResource
    :param repo_id: ID of the repository to get reviews for
    :type repo_id: integer
    :param branch: branch to get reviews for
    :type branch: string
    :returns: list of Review resources
    :rtype: list
    """
    ret = []
    reviews = get_reviews_for_repo(root, repo_id, verbose=verbose)
    for review in reviews:
        if review.branch.lower() == branch.lower():
            ret.append(review)
            if verbose:
                print("\t\tfound review %s for branch %s" % (review.id, branch))
    return ret

def get_rb_root(url, username=None, password=None):
    """
    Return a rbclient root object, for the RB install at url

    raises SystemExit on failure

    :param url: URL to reviewboard
    :type url: string
    :returns: RBClient Root resource
    :rtype: rbtools.api.resource.RootResource
    """
    client = RBClient(url, username=username, password=password)
    root = client.get_root()
    if not root:
        raise SystemExit("Error - could not get RBClient root.")
    return root

def get_repository_by_uri(root, repo_uri, match_path_end=False, verbose=False):
    """
    Return the Repository resource for the RB repository with the given uri.

    Since some ReviewBoard servers don't seem to return the repository's
    "mirror path" in the API response, when match_path_end is true,
    a repository will also match if the specified repo_uri ends with the
    ReviewBoard Repository "path" parameter.

    :param root: RBClient Root resource
    :type root: rbtools.api.resource.RootResource
    :param repo_uri: the URI of the repo to find
    :type repo_uri: string
    :param match_path_end: also match if RB repo path matches end of URI
    :type match_path_end: boolean
    :returns: matching Repository object, or None if no match
    :rtype: rbtools.api.resource.ItemResource (Repository) or None
    """
    repositories = root.get_repositories()
    repo_uri = repo_uri.lower()

    count = 0
    try:
        while True:
            for repo in repositories:
                count = count + 1
                if repo.url.lower() == repo_uri:
                    if verbose:
                        print("\tfound repository id %d with url matching %s" % (repo.id, repo.url))
                    return repo
                if match_path_end and repo_uri.endswith(repo.path.lower()):
                    if verbose:
                        print("\tfound repository id %d with matching path %s" % (repo.id, repo.path))
                    return repo
            repositories = repositories.get_next()
    except StopIteration:
        if verbose:
            print("\titerated through %d repositories and found no matches" % count)
        return None
    if verbose:
        print("\titerated through %d repositories and found no matches" % count)
    return None
    
def get_latest_diff_for_review(review, verbose=False):
    """
    Return the newest Diff resource for a given Review resource,
    or None if there aren't any or on failure.

    :param review: review resource
    :type review: rbtools.api.resource.ReviewRequestResource
    :returns: newest diff, or None if no diffs or failure
    :rtype: rbtools.api.resource.DiffResource or None
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
    return latest_diff
