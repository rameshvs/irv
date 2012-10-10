#!/usr/bin/env python

import string
import sys

HELP = """\
python %s vote_file <manual-mode>
Runs instant-runoff voting on the ballots in vote_file, and prints
a full ranking of all eligible candidates to standard output.

The first line of vote_file should be a tab-separated list of candidate 
names, and each following line should contain unique positive integers 
for votes and 0s for abstentions.

If a second argument is NOT given, the script will run in semiautomatic mode,
where it runs all non-unbreakable-tie eliminations automatically.\
"""

# I'll assume we don't have more than 10 candidates
PLACES = ['1st','2nd','3rd','4th','5th','6th','7th','8th','9th','10th']
def int_or_none(string):
    # returns None if it's "0", or the number otherwise
    return int(string) or None

def read_votes(filename):
    """
    Takes in a file formatted as described above,
    and returns a VoteTable object (see below).
    """

    with open(filename) as f:
        names = f.readline()[:-1].split('\t')
        lines = f.readlines()

    # table starts off as voters x candidates
    votes = []
    for line in lines:
        out = map(int_or_none,line.split())
        votes.append(out)
    return VoteTable(votes,names)

class VoteTable(object):
    """
    A table of votes that can handle common instant-runoff operations

    Instance variables:
        names : a list of candidate names
        votes : a list of ballots, where each ballot is a list with candidate
                ranks
        counts : a collapsed representation of each candidate's votes. Each
                element corresponds to one candidate, and is a list containing
                [# of first place votes, # of second place votes, ... ]
    """

    def __init__(self,votes,names):
        self.votes = votes
        self.names = names

        self.maintain()

    def copy(self):
        return VoteTable(self.votes,self.names)

    def compute_winner(self):
        # if (the strongest candidate)'s # of first place votes is more than
        # half of the total, they win
        if self.counts[-1][0] > self.N_votes/2:
            return self.names[-1]
        else:
            return None

    def check_tied(self):
        """ Checks if the remaining candidates are tied (unbreakably) """
        counts_equal = (self.counts[-1] == self.counts[-2])
        # if they're "tied" at all zeros, then they can't win and their
        # ballots won't affect anyone else, so it doesn't matter how
        # we break the tie.
        counts_nonzero = sum(self.counts[-1]) > 0
        return (counts_equal and counts_nonzero)

    def maintain(self):
        self.N_votes = len(self.votes)
        self.N_candidates = len(self.names)

        self.reduce_ranks()
        self.update_counts()

    def update_counts(self):
        """
        Updates/maintains self.counts (see above for description)
        """
        counts = []
        # computes [<# 1st place votes>, <# 2nd place votes>, ...]
        for (candidate,votes) in zip(self.names,self.votes_by_candidate()):
            counter = {}
            for i in xrange(1,self.N_candidates+1):
                counter[i] = 0 # don't use defaultdict: we need all keys
            for vote in votes:
                if vote is not None: # don't count abstentions
                    counter[vote] += 1
            counts.append([count for (rank,count) in sorted(counter.iteritems())])

        # now keep things sorted: the 3 lists are sorted from
        # weakest candidate to strongest candidate
        (counts,votes_by_candidate,names) = zip(*sorted(zip(counts,self.votes_by_candidate(),self.names)))
        # we want to store votes by ballot, not by candidate:
        self.votes = zip(*votes_by_candidate)
        self.counts = counts
        self.names = names

    def votes_by_candidate(self):
        return zip(*self.votes) # transpose, since we store by ballot

    def reduce_ranks(self):
        """ Makes all ballots contain sequential votes starting from 1. """
        self.votes = map(get_rank_order,self.votes)

    def set_votes_by_candidate(self,votesT):
        self.votes = zip(*votesT)
        self.maintain()

    def set_by_voter(self,votes):
        self.votes = votes
        self.maintain()

    def print_table(self):
        """ Prints out collapsed vote table (see update_counts) """
        firstcol_string = "# of votes in rank:"
        max_length = max([len(name) for name in self.names+(firstcol_string,)])
        print("**************************************")
        firstcol_string_ljust = string.ljust(firstcol_string, max_length+1)
        ranks = ' '.join([str(x+1) for x in xrange(self.N_candidates)])
        print("   %s: %s" % (firstcol_string_ljust, ranks))
        print("**************************************")
        for (i, (name, v)) in enumerate(zip(self.names,self.counts)):
            name_ljust = string.ljust(name,max_length + 1)
            print("%d: %s: %s"%(i,name_ljust, ' '.join(map(str,v))))
        print("**************************************")

    def with_candidate_eliminated(self,index):
        """ returns a new table with candidate at index eliminated """
        votes = self.votes_by_candidate()
        new_votes = votes[:index] + votes[index+1:]
        new_names = self.names[:index] + self.names[index+1:]
        return VoteTable(zip(*new_votes),new_names)

def get_rank_order(list):
    """ Takes something like [5,1,4] and gives [3,1,2] """
    # this line gives us the indices we would use to sort the list
    indices = [i for (v, i) in sorted((v, i) for (i, v) in enumerate(list)) if v is not None]
    out = [None] * len(list)
    for (rank,index) in enumerate(indices):
        out[index] = rank+1 # start at 1 instead of 0
    return out

def print_ranking(ranking,ineligible_candidates):
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    for (candidate,description) in zip(ranking,PLACES):
        print("%s place: %s"%(description,candidate))
    if ineligible_candidates != []:
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("Ineligible candidates:")
        print('\n'.join(ineligible_candidates))
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

def instant_runoff(table,is_automated):
    """
    Runs instant-runoff voting on a VoteTable object. Can
    run in semiautomatic mode (all non-tie eliminations are automatic).
    """
    ranking = []
    N = table.N_candidates
    ineligible_candidates = [] # list of candidates w/too many abstains to win
    for rank in xrange(N):
        # keep these so we don't clobber them below
        full_table = table.copy()
        while True:
            ineligibility_found = False
            winner = table.compute_winner()
            if winner is None: # no candidate has enough 1st place votes
                if table.N_candidates == 1:
                    ineligibility_found = True
                    (unlucky_soul,) = table.names
                    ineligible_candidates.append(unlucky_soul)
                    if not is_automated:
                        _ = raw_input("Determined that %s is ineligible to win. Press enter to continue..."%unlucky_soul)
                    break

                if not is_automated:
                    table.print_table()
                    loser_index = input("Which candidate to eliminate? Please enter a number: ")
                else:
                    # automatically choose lowest one when lex. sorted
                    if not table.check_tied():
                        loser_index = 0
                    else:
                        table.print_table()
                        loser_index = input("** I found an unbreakable tie. Which candidate do you want to eliminate? ")
                if not is_automated:
                    print("OK, I'm eliminating %s..."%table.names[loser_index])
                #maybe_loser = compute_loser(votes,names)
                table = table.with_candidate_eliminated(loser_index)
            else: # got it!
                if not is_automated:
                    _ = raw_input("Determined that %s is rank %d. Press enter to continue..."%(winner,rank+1))
                break
        if ineligibility_found:
            winner = unlucky_soul # eliminate from the table (not actually a winner)
        else:
            ranking.append(winner)
        if rank != N-1:
            table = full_table.with_candidate_eliminated(full_table.names.index(winner))

    print_ranking(ranking,ineligible_candidates)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(HELP % sys.argv[0])
        sys.exit(-1)
    table = read_votes(sys.argv[1])
    is_automated = (len(sys.argv) <= 2)
    instant_runoff(table,is_automated)
