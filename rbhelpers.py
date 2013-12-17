# helper methods to work with RBTools API

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

def get_reviews_for_branch(root, repo, branch, verbose=False):
    """
    Gets a list of reviews for the given branch in the given repo

    @param root RBClient root
    @param repo string, repo to get reviews for
    @param branch string, branch to get reviews for
    """
    # get open reviews to a specified user, group, etc.
    args = {}
    args['repository'] = repo

    req = root.get_review_requests(**args)
    reviews = []
    if verbose:
        print("\tfound %d open reviews for repository %s" % (req.total_results, repo))
    for review in req:
        if review.branch.lower() == branch.lower():
            reviews.append(review)
            if verbose:
                print("\t\tfound review %s for branch %s" % (review.id, branch))
    return reviews
