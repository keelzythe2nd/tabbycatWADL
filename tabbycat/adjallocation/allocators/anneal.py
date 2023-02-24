import logging
import math
import random

from .base import BaseAdjudicatorAllocator, register
from .hungarian import VotingHungarianAllocator
from ..allocation import AdjudicatorAllocation

logger = logging.getLogger(__name__)


@register
class SAAllocator(BaseAdjudicatorAllocator):

    key = "simanneal"

    SCORE_ADJ_TEAM_CONFLICT = 10000
    SCORE_TARGET_PANEL = 800
    SCORE_ADJ_TEAM_HISTORY = 100
    SCORE_ADJ_ADJ_HISTORY = 30

    MAX_TRIES = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        t = self.tournament
        self.conflict_penalty = t.pref('adj_conflict_penalty')
        self.history_penalty = t.pref('adj_history_penalty')

    def allocate(self, initial=None):

        if initial is None:
            initial = VotingHungarianAllocator(self.debates, self.adjudicators, self.round).allocate()

        pairs = [(aa.container, tuple(aa.all())) for aa in initial]

        top_bracket = pairs[0][0].bracket
        bot_bracket = pairs[-1][0].bracket

        # 4-0 - 5 brackets, needs 6 gaps
        # 5-2

        gaps = (top_bracket - bot_bracket) + 2

        div = 3.0 / gaps

        for debate, panel in pairs:
            setattr(debate, 'target_panel', 2 + (debate.bracket - bot_bracket +
                                                 1) * div)

        logger.info([d.target_panel for d, p in pairs])

        self.state = dict(pairs)

        self.anneal(800, 1, 1e4, self.state)

        # i = 0
        # while self.best_energy > 0 and i < self.MAX_TRIES:
        #    self.anneal(100, 1, 1e3, self.best_state)
        #    i += 1

        result = []
        for debate, panel in list(self.best_state.items()):
            aa = AdjudicatorAllocation(debate)
            panel = list(panel)
            panel.sort(key=lambda x: x.score, reverse=True)

            aa.chair = panel.pop(0)
            aa.panellists = panel
            result.append(aa)

        return result, ""

    def save_best(self):
        self.best_energy = self.energy
        self.best_state = dict(self.state)

    def anneal(self, steps, min_temp, max_temp, state):

        self.energy = self.calc_energy(state)
        logger.info("start energy %.2f", self.energy)
        self.save_best()
        tf = -math.log(float(max_temp) / min_temp)

        accepts = 0
        improves = 0

        for i in range(steps):

            temp = max_temp * math.exp(tf * i/steps)

            diff, swap = self.candidate_swap()
            if diff < 0 or math.exp(-diff / temp) > random.random():
                accepts += 1
                self.energy += diff
                self.apply_swap(swap)

                if diff < 0:
                    improves += 1

                    if self.energy < self.best_energy:
                        self.save_best()
                        if self.energy == 0:
                            break

        logger.info("accepts %d improves %d", accepts, improves)
        logger.info("end energy %.2f", self.best_energy)
        logger.info("end energy %.2f", self.calc_energy(self.best_state))
        logger.info(self.best_state)

    def calc_energy(self, state):
        return sum(self.score(debate, panel) for debate, panel in list(state.items()))

    def candidate_swap(self):
        meth = random.choice((self.panel_swap, self.member_swap))
        return meth()

    def member_swap(self):
        d1 = random.choice(list(self.state.keys()))
        panel1 = self.state[d1]
        a1 = random.choice(panel1)

        d2 = d1
        panel2 = self.state[d2]

        while d1 == d2 or len(panel1) != len(panel2):
            d2 = random.choice(list(self.state.keys()))
            panel2 = self.state[d2]
            a2 = random.choice(panel2)

        assert len(panel1) == len(panel2)

        idx1 = panel1.index(a1)
        new_panel1 = panel1[:idx1] + (a2,) + panel1[idx1+1:]
        idx2 = panel2.index(a2)
        new_panel2 = panel2[:idx2] + (a1,) + panel2[idx2+1:]

        curr_score = self.score(d1, panel1) + self.score(d2, panel2)
        new_score = self.score(d1, new_panel1) + self.score(d2, new_panel2)
        diff = new_score - curr_score
        swap = ((d1, new_panel1), (d2, new_panel2))

        return diff, swap

    def panel_swap(self):

        # panel swap
        d1 = random.choice(list(self.state.keys()))
        d2 = d1
        panel1 = self.state[d1]
        panel2 = self.state[d2]

        while d2 == d1 or len(panel1) != len(panel2):
            d2 = random.choice(list(self.state.keys()))
            panel2 = self.state[d2]

        curr_score = self.score(d1, panel1) + self.score(d2, panel2)
        new_score = self.score(d2, panel1) + self.score(d1, panel2)

        diff = new_score - curr_score
        swap = ((d2, panel1), (d1, panel2))

        return diff, swap

    def apply_swap(self, swap):
        for debate, panel in swap:
            self.state[debate] = panel

    def score(self, debate, panel):
        score = sum(getattr(self, f)(debate, panel) for f in dir(self) if f.startswith('score_'))
        return score

    def score_adj_team_conflict(self, debate, panel):
        score = 0

        for adj in panel:
            for team in debate.teams:
                score += self.conflict_penalty * self.conflicts.conflict_adj_team(adj, team)
        return score

    def score_adj_team_history(self, debate, panel):
        score = 0

        for adj in panel:
            for team in debate.teams:
                score += self.history_penalty * self.history.seen_adj_team(adj, team)

        return score

    def score_adj_adj_history(self, debate, panel):
        score = 0

        for i, adj in enumerate(panel):
            for j in range(i+1, len(panel)):
                score += self.history_penalty * self.history.seen_adj_adj(adj, panel[j])

        return score

    def score_target_panel_strength(self, debate, panel):
        avg = sum(p.score for p in panel) / len(panel)
        diff = abs(debate.target_panel - avg)

        return self.SCORE_TARGET_PANEL * diff * debate.target_panel * avg
