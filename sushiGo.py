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


def game(nplayers):
    deck = 14 * [TEMPURA] +\
           14 * [SASHIMI] +\
           14 * [DUMPLING] +\
           12 * [MAKI2] +\
            8 * [MAKI3] +\
            6 * [MAKI1] +\
           10 * [SALMON] +\
            5 * [SQUID] +\
            5 * [EGG] +\
           10 * [PUDDING] +\
            6 * [WASABI] +\
            4 * [CHOPSTICKS]
    random.shuffle(deck)

    # Number of cards per hand each round
    ncards = {2: 10, 3: 9, 4: 8, 5: 7}[nplayers]
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


if __name__ == '__main__':

    # Test the scoring for a random hand.
    print('=== TEST ===')
    deck = 14 * [TEMPURA] +\
           14 * [SASHIMI] +\
           14 * [DUMPLING] +\
           12 * [MAKI2] +\
            8 * [MAKI3] +\
            6 * [MAKI1] +\
           10 * [SALMON] +\
            5 * [SQUID] +\
            5 * [EGG] +\
           10 * [PUDDING] +\
            6 * [WASABI] +\
            4 * [CHOPSTICKS]
    random.shuffle(deck)

    hand = ''.join(deck[0:8])
    print('hand:    \t', hand)
    print('tempura: \t', tempurascore(hand))
    print('sashimi: \t', sashimiscore(hand))
    print('dumpling:\t', dumplingscore(hand))
    print('nigiri:  \t', nigiriscore(hand))
    print('=== ==== ===')

    
    # Evaluate a histogram of player scores per round.
    ngames = 100000
    
    rounds = []
    scores = []
    for i in range(ngames):
        s, r = game(4)
        rounds.append(r)
        scores.append(s)

    rounds = np.array(rounds)
    print ("Mean score by round across %d games:" % ngames)
    print(rounds.mean(axis=0).mean(axis=-1))

    scores = np.array(scores)
    print ("Mean final score across %d games:" % ngames)
    print(scores.mean())
   
    import matplotlib.pyplot as plt
    plt.hist(rounds.flatten(), bins=int( sub(rounds.max(), rounds.min()) ))
    plt.hist(scores.flatten(), bins=int( sub(scores.max(), scores.min()) ))
    plt.show()