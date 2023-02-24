from django.db.models import Avg, Case, Count, Q, Sum, When

from adjallocation.models import DebateAdjudicator
from adjfeedback.models import AdjudicatorFeedback
from participants.models import Adjudicator, Team


def populate_win_counts(teams, round=None):
    """Populates the `_win_count` and `_points` attributes of the teams in
    `teams`. Operates in-place."""

    teams_by_id = {team.id: team for team in teams}

    annotation_filter = Q(debateteam__teamscore__ballot_submission__confirmed=True)
    if round is not None:
        annotation_filter &= Q(debateteam__debate__round__seq__lte=round.seq)

    teams_annotated = Team.objects.filter(id__in=teams_by_id.keys()).annotate(
        points_annotation=Sum('debateteam__teamscore__points', filter=annotation_filter),
        win_count_annotation=Count(Case(When(debateteam__teamscore__win=True, then=1)), filter=annotation_filter),
    )

    for team in teams_annotated:
        teams_by_id[team.id]._wins_count = team.win_count_annotation
        teams_by_id[team.id]._points = team.points_annotation

    for team in teams:
        if getattr(team, '_wins_count', None) is None:
            team._wins_count = 0
        if getattr(team, '_points', None) is None:
            team._points = 0


def populate_feedback_scores(adjudicators):
    """Populates the `_feedback_score_cache` attribute of the adjudicators
    in `adjudicators`.
    Operates in-place."""

    adjs_by_id = {adj.id: adj for adj in adjudicators}

    adjfeedbacks = AdjudicatorFeedback.objects.filter(
        adjudicator_id__in=adjs_by_id.keys(),
        confirmed=True,
        ignored=False,
    ).exclude(source_adjudicator__type=DebateAdjudicator.TYPE_TRAINEE)

    adjs_annotated = Adjudicator.objects.filter(
        id__in=adjs_by_id.keys(),
        adjudicatorfeedback__in=adjfeedbacks
    ).annotate(feedback_score_annotation=Avg('adjudicatorfeedback__score'))

    for adj in adjs_annotated:
        adjs_by_id[adj.id]._feedback_score_cache = adj.feedback_score_annotation

    for adj in adjudicators:
        if not hasattr(adj, '_feedback_score_cache'):
            adj._feedback_score_cache = None
