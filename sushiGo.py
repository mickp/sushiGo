    #!/usr/bin/env python
# -*- coding: utf-8 -*-

## Copyright (C) 2018 Mick Phillips <mick.phillips@gmail.com>
##
## Copying and distribution of this file, with or without modification,
## are permitted in any medium without royalty provided the copyright
## notice and this notice are preserved.  This file is offered as-is,
## without any warranty.

import random
import re
import numpy as np
from operator import add, sub
import weakref

# Each type of card is represented by a single character. Hands
# are represented by strings.
TEMPURA = 't'
SASHIMI = 's'
DUMPLING = 'd'
MAKI3 = 'm'
MAKI2 = 'n'
MAKI1 = 'o'
SALMON = 'a'
SQUID = 'b'
EGG = 'c'
PUDDING = 'p'
WASABI = 'w'
CHOPSTICKS = 'f'

# A regular expression to search for paired wasabi and nigiri
# cards in a hand.
wasabimatch = WASABI + '[^' + SQUID + SALMON + EGG + ']*?'



def sashimiscore(hand):
    # 10 points for each complete set of 3 sashimi.
    return 10 * (hand.count(SASHIMI) // 3)


def tempurascore(hand):
    # 5 points for each complete pair of tempura cards.
    return 5 * (hand.count(TEMPURA) // 2)


def dumplingscore(hand):
    # 1 point for 1 dumpling, 3 points for 2, 6 points for 3, 
    # 10 points for 4, or 15 points for 5 or more.
    return [0, 1, 3, 6, 10, 15][min(hand.count(DUMPLING), 5)]


def nigiriscore(hand):
    # 3 for squid, 2 for salmon, 1 for egg, but tripled if
    # it's the first nigiri in the hand after a Wasabi card.
    score = 0
    nigiri = hand.count(SQUID)
    wnigiri = len(re.findall(wasabimatch + SQUID, hand))
    score += 3 * (2 * wnigiri + nigiri)
    # salmon
    nigiri = hand.count(SALMON)
    wnigiri = len(re.findall(wasabimatch + SALMON, hand))
    score += 2 * (2 * wnigiri + nigiri)
    # egg
    nigiri = hand.count(EGG)
    wnigiri = len(re.findall(wasabimatch + EGG, hand))
    score += 2 * wnigiri + nigiri
    return score


def basescore(hand):
    # The base score for a hand in isolation.
    score = 0
    score += tempurascore(hand) + sashimiscore(hand)
    score += dumplingscore(hand) + nigiriscore(hand)
    return score


def makiscores(hands):
    # Maki modifier scores for a set of hands.
    maki = [h.count(MAKI3)*3 + h.count(MAKI2)*2 + h.count(MAKI1) for h in hands]
    sortedmaki = sorted(set(maki))
    if len(sortedmaki) == 1:
        scores = len(hands) * [6/len(hands)]
    else:
        scores = len(hands) * [0]
        indices = [i for i, j in enumerate(maki) if j == sortedmaki[-1]]
        for i in indices:
            scores[i] += 6 / len(indices)
        indices = [i for i, j in enumerate(maki) if j == sortedmaki[-2]]
        for i in indices:
            scores[i] += 3 / len(indices)
    return scores

    
def puddingscores(puddings):
    # Pudding modifier scores applied at the end of a game.
    sortedpuddings = sorted(set(puddings))
    if len(sortedpuddings) == 1:
        scores = len(puddings) * [6/len(puddings)]
    else:
        scores = len(puddings) * [0]
        indices = [i for i, j in enumerate(puddings) if j == sortedpuddings[-1]]
        for i in indices:
            scores[i] += 6 / len(indices)
        indices = [i for i, j in enumerate(puddings) if j == sortedpuddings[0]]
        for i in indices:
            scores[i] -= 6 / len(indices)
    return scores


cardsPerPlayer = {2: 10,
                  3: 9,
                  4: 8,
                  5: 7}


deckCounts = {
    TEMPURA: 14,
    SASHIMI: 14,
    DUMPLING: 14,
    MAKI2: 12,
    MAKI3: 8,
    MAKI1: 6,
    SALMON: 10,
    SQUID: 5,
    EGG: 5,
    PUDDING: 10,
    WASABI: 6,
    CHOPSTICKS: 4
}

probabilities = {k:v / sum(deckCounts.values()) for k, v in deckCounts.items()}

def newDeck():
    from itertools import chain
    deck = list(chain.from_iterable([v * [k] for k, v in deckCounts.items()]))
    random.shuffle(deck)
    return deck


def simpleGame(nplayers):
    deck = newDeck()
    # Number of cards per hand each round
    ncards = cardsPerPlayer[nplayers]
    nrounds = 3

    roundscores = []

    puddings = nplayers * [0]
    for rnd in range(nrounds):
        hands = np.reshape(deck[rnd * ncards * nplayers:(rnd+1) * ncards * nplayers], (nplayers, ncards))
        hands = [''.join(h) for h in hands]
        puddings = list(map(add, puddings, [h.count(PUDDING) for h in hands]))
        bscore = [basescore(h) for h in hands]
        mscore = makiscores(hands)
        roundscores.append(list(map(add, bscore, mscore)))

    scores = [sum(r) for r in zip(*roundscores)]
    finalscores = list(map(add, scores, puddingscores(puddings)))

    return finalscores, roundscores


class Player(object):
    instances = []

    @classmethod
    def allHands(cls):
        return [p.hand for p in cls.instances]


    def __init__(self):
        self.__class__.instances.append(weakref.proxy(self))
        self.hand = '';
        self.takeFrom = self._takeFirstFrom
        self.pref = None
        self.puddings = 0


    def makiCount(self):
        c = self.hand.count
        return 3 * c(MAKI3) + 2 * c(MAKI2) + c(MAKI1)


    def newGame(self):
        self.puddings = 0
        self.hand = ''


    def newRound(self):
        self.puddings += self.hand.count(PUDDING)
        self.hand = ''


    def otherHands(self):
        return [p.hand for p in Player.instances if p != self]


    def otherMakiCounts(self):
        return[p.makiCount() for p in Player.instances if p != self]


    def setPreference(self, pref):
        if pref is None:
            self.takeFrom = self._takeFirstFrom
            self.pref = []
        elif type(pref) is str and len(pref):
            if pref.lower() == 'smart':
                self.takeFrom = self._takeSmart
                return
            elif pref.lower() == 'smarter':
                self.takeFrom = self._takeSmarter
                return
            prefs = pref.upper().split(',')
            expansions = {'MAKI': [MAKI3, MAKI2, MAKI1],
                          'NIGIRI': [SALMON, SQUID, EGG]}
            self.pref = []
            for p in prefs:
                if not p:
                    continue
                if p in expansions:
                    self.pref.extend(expansions[p])
                else:
                    self.pref.append(globals()[p])
            self.takeFrom = self._takePreferenceOrFirst


    def _takeSmarter(self, hand):
        if len(hand) == 1:
            self.hand += hand[0]
            return ''

        priorities = {k:0 for k in deckCounts.keys()}

        if re.match(wasabimatch + '$', self.hand):
            priorities[SQUID] += 9     # 9 points
            priorities[SALMON] += 6    # 6 points
            priorities[EGG] += 3       # 3 points
        else:
            priorities[SQUID] += 3
            priorities[SALMON] += 2
            priorities[EGG] += 1
        if self.hand.count(TEMPURA) % 2:
            priorities[TEMPURA] += 5   # 5 points
        else:
            priorities[TEMPURA] += 5 * len(hand) * probabilities[TEMPURA]
        if self.hand.count(SASHIMI) % 3 == 2:
            priorities[SASHIMI] += 10 # 10 points
        elif self.hand.count(SASHIMI) % 3 == 1:
            # Chance at 10 points - naive probability.
            priorities[SASHIMI] += 10 * len(hand) * probabilities[SASHIMI]
        else:
            priorities[SASHIMI] += 10 * len(hand) * probabilities[SASHIMI] * probabilities[SASHIMI]

        priorities[MAKI3] = 3 / 4
        priorities[MAKI2] = 2 / 4
        priorities[MAKI1] = 1 / 4

        priorities[WASABI] = len(hand) * (probabilities[SQUID] + probabilities[SALMON] + probabilities[EGG])

        priorities[CHOPSTICKS] = -1

        prlist = sorted(priorities, key=priorities.get, reverse=True)

        for p in prlist:
            if p in hand:
                index = hand.find(p)
                self.hand += p
                return hand[0:index] + hand[index+1:]


    def _takeSmart(self, hand):
        if len(hand) == 1:
            self.hand += hand[0]
            return ''

        exclude = CHOPSTICKS
        index = 0

        if len(hand) < 3 and self.hand.count(SASHIMI) % 3 < 2:
            exclude += SASHIMI
        if len(hand) < 3 and self.hand.count(TEMPURA) % 2 == 0:
            exclude += TEMPURA
        if MAKI2 in hand:
            exclude += MAKI1
        if MAKI3 in hand:
            exclude += MAKI1 + MAKI2
        if len(hand) < 3:
            exclude += WASABI
        if re.match(wasabimatch + '$', self.hand):
            exclude += WASABI
            if SQUID in hand:
                index = hand.find(SQUID)
        
        if index == 0:
            while(hand[index] in exclude and index < len(hand)-1):
                index += 1
        self.hand += hand[index]
        return hand[0:index] + hand[index+1:]


    def _takeFirstFrom(self, hand):
        self.hand += hand[0]
        return hand[1:]

    
    def _takePreferenceOrFirst(self, hand):
        index = -1    
        for p in self.pref:
            index = hand.find(p)
            if index != -1:
                break

        if index == -1:
            return self._takeFirstFrom(hand)
        else:
            self.hand += hand[index]
            return hand[0:index] + hand[index+1:]


def trial(players):
    from collections import deque
    nplayers = len(players)
    ncards = cardsPerPlayer[nplayers]
    deck = newDeck()
    
    [p.newGame() for p in players]

    roundscores = []
    for rnd in range(3):
        [p.newRound() for p in players]
        hands = np.reshape(deck[rnd * ncards * nplayers:(rnd+1) * ncards * nplayers], (nplayers, ncards))
        hands = deque([''.join(h) for h in hands])
        for n in range(ncards):
            hands = deque([p.takeFrom(hands[i]) for i, p in enumerate(players)])
            hands.rotate()
        bscore = [basescore(p.hand) for p in players]
        mscore = makiscores([p.hand for p in players])
        roundscores.append(list(map(add, bscore, mscore)))

    scores = [sum(r) for r in zip(*roundscores)]
    finalscores = list(map(add, scores, puddingscores([p.puddings for p in players])))

    return finalscores, roundscores


def testScoring():
    # Test the scoring for a random hand.
    print('=== TEST ===')
    deck = newDeck()

    hand = ''.join(deck[0:8])
    print('hand:    \t', hand)
    print('tempura: \t', tempurascore(hand))
    print('sashimi: \t', sashimiscore(hand))
    print('dumpling:\t', dumplingscore(hand))
    print('nigiri:  \t', nigiriscore(hand))
    print('=== ==== ===')


if __name__ == '__main__':
    import sys 
    import matplotlib.pyplot as plt
    
    if len(sys.argv) == 2 and sys.argv[1].lower() == 'test':
        testScoring()
        sys.exit()
    
    if len(sys.argv) == 2 and sys.argv[1].lower() == 'simple':
        # Evaluate a histogram of player scores per round.
        ngames = 10000

        rounds = []
        scores = []

        for i in range(ngames):
            s, r = simpleGame(4)
            rounds.append(r)
            scores.append(s)
        labels = [str(i+1) for i in range(4)]
        rounds = np.array(rounds)
        print (rounds.shape)
        print ("Mean score by player and round across %d games:" % ngames)
        [print(row) for row in rounds.mean(axis=0)]

        scores = np.array(scores)
        print ("Mean final score by player across %d games:" % ngames)
        print(scores.mean(axis=0))

        plt.hist(rounds.flatten(), bins=int( sub(rounds.max(), rounds.min()) ))
        plt.hist(scores.flatten(), bins=int( sub(scores.max(), scores.min()) ))
        plt.legend(prop={'size': 10})
        plt.show()

    elif len(sys.argv) > 1 and sys.argv[1].lower() == 'prefs':
        # Evaluate a histogram of player scores per round.
        ngames = 10000

        rounds = []
        scores = []

        players = []
        labels = []
        for i, arg in enumerate(sys.argv[2:]):
            players.append(Player())
            labels.append("%d: %s" % (i+1, arg))
            if arg.lower() != 'none':
                players[-1].setPreference(arg)
        for i in range(ngames):
            s, r = trial(players)
            rounds.append(r)
            scores.append(s)

        rounds = np.array(rounds)
        print (rounds.shape)
        print ("Mean score by player and round across %d games:" % ngames)
        [print(row) for row in rounds.mean(axis=0)]

        scores = np.array(scores)
        print ("Mean final score by player across %d games:" % ngames)
        print(scores.mean(axis=0))
   
        plt.hist(scores, bins=int(sub(scores.max(), scores.min())), histtype='step', label=labels, density=True)
        plt.legend(prop={'size': 10})
        plt.show()

    else:
        prefs = ['nigiri', 'maki', 'tempura', 'dumpling', 'pudding', 'sashimi', 'wasabi', 'smart', 'smarter']
        ngames = 10000
        players = [Player() for p in range(4)]
        fig, axs = plt.subplots(3, 3, sharex=True, sharey=True, tight_layout=True)
        fig.title = 'score probability distributions'

        from multiprocessing import Pool

        for i_p, pref in enumerate(prefs):
            pool = Pool()
            print ("Pref %d of %d: %s ..." % (i_p+1, len(prefs), pref))
            players[0].setPreference(pref)
            labels = [pref] + ['none'] * (len(players)-1)
            results = []
            for i_g in range(ngames):
                results.append(pool.apply_async(trial, [players]))
            pool.close()
            pool.join()
            scores=np.array([r.get()[0] for r in results])
            axs.flat[i_p].hist(scores, bins=int(sub(scores.max(), scores.min())), 
                               histtype='step', label=labels, density=True)
            axs.flat[i_p].legend(title='strategy', prop={'size':8})
        print('... done.')
        plt.show()
