import git
import util

class Search(object):
    header_titles = ["author", "author-mail", "author-time", "author-tz",
                    "committer", "committer-mail", "committer-time", "committer-tz",
                    "summary", "previous", "filename", "\t"]
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path, odbt=git.GitDB)

        self.authors = []

    def find_author(self, name=None, email=None, add_author=False):
        """
        Find author with given name and/or email. If author does not exist,
        add the author if add_author is True.
        """

        for author in self.authors:
            if name and email and author.name == name and author.email == email:
                return author
            elif name and author.name == name:
                return author
            elif author.name == email:
                return author
        if add_author:
            person = Person(name, email)
            self.authors.append(person)
            return person
        return None

    def score_last_commit(author, block):
        # Git blame.
        pass

    def lines_contributed(self, block):
        """
        Given a block, return a hash {author: num lines contributed}.
        """

        contributions = {}      # author => num lines
        shas = set()

        blamestr = self.repo.git.blame(block, incremental=True)
        lines = blamestr.splitlines()

        num_lines_total = 0

        sha = None
        i = 0
        while i < len(lines):
            # We are at the first line of group or sub-group.
            sha, ln_orig, ln_final, ln_group = lines[i].split()
            ln_group = int(ln_group)

            if not shas.issuperset((sha,)):
                shas.add(sha)

                # We are at a new commit group. Figure out the author.
                author_name, author_email = None, None
                while not (author_name and author_email):
                    i += 1
                    components = lines[i].split(" ")
                    if components[0] == 'author':
                        author_name = " ".join(components[1:])
                    elif components[0] == 'author-mail':
                        author_email = " ".join(components[1:]).strip("<").strip(">")

                # Add line count to author.
                person = self.find_author(name=author_name, email=author_email,
                        add_author=True)
                if contributions.has_key(person):
                    contributions[person] += ln_group
                else:
                    contributions[person] = ln_group
                
                # We got the data we want. Spin until we get to 'filename', which
                # marks the end of this sub-group.
                i = util.spin_lines_until(lines, i, 'filename')

                # We are now one line past 'filename'. The next line should contain
                # a SHA.
            else:
                # We are in an old sub-group, so update author's contributions.
                contributions[person] += ln_group
                i = util.spin_lines_until(lines, i, 'filename')
        return contributions

class Person(object):
    def __init__(self, name=None, email=None):
        self.name = name
        self.email = email

    def __eq__(self, person):
        return self.name == person.name and self.email == person.email

    def __str__(self):
        return "Name: %s Email: %s" % (self.name, self.email)

class Block(object):
    """
    A Block is a git blob (file).
    """

    def __init__(self, filename):
        self.filename = filename
