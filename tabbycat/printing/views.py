import json

import qrcode
from qrcode.image import svg

from django.db.models import Q
from django.utils.translation import gettext as _
from django.views.generic.base import TemplateView

from adjfeedback.models import AdjudicatorFeedbackQuestion
from adjfeedback.utils import expected_feedback_targets
from checkins.models import DebateIdentifier
from checkins.utils import create_identifiers
from draw.models import Debate, DebateTeam
from options.utils import use_team_code_names
from participants.models import Person
from results.utils import side_and_position_names
from tournaments.mixins import (CurrentRoundMixin, OptionalAssistantTournamentPageMixin,
                                RoundMixin, TournamentMixin)
from tournaments.models import Tournament
from utils.misc import reverse_tournament
from utils.mixins import AdministratorMixin
from venues.models import VenueCategory


class MasterSheetsListView(AdministratorMixin, RoundMixin, TemplateView):
    template_name = 'division_sheets_list.html'

    def get_context_data(self, **kwargs):
        kwargs['standings'] = VenueCategory.objects.all()
        kwargs['venue_categories'] = VenueCategory.objects.all()
        return super().get_context_data(**kwargs)


class MasterSheetsView(AdministratorMixin, RoundMixin, TemplateView):
    template_name = 'master_sheets_view.html'

    def get_context_data(self, **kwargs):
        venue_category_id = self.kwargs['venue_category_id']
        base_venue_category = VenueCategory.objects.get(id=venue_category_id)
        active_tournaments = Tournament.objects.filter(active=True)
        for tournament in list(active_tournaments):
            tournament.debates = Debate.objects.select_related(
                'division', 'division__venue_category', 'round',
                'round__tournament').filter(
                    # All Debates, with a matching round, at the same venue category name
                    round__seq=self.round.seq,
                    round__tournament=tournament,
                    # Hack - remove when venue category are unified
                    division__venue_category__name=base_venue_category.name
            ).order_by('round', 'division__venue_category__name', 'division')

        kwargs['base_venue_category'] = base_venue_category
        kwargs['active_tournaments'] = active_tournaments
        return super().get_context_data(**kwargs)


class RoomSheetsView(AdministratorMixin, RoundMixin, TemplateView):
    template_name = 'room_sheets_view.html'

    def get_context_data(self, **kwargs):
        venue_category_id = self.kwargs['venue_category_id']
        base_venue_category = VenueCategory.objects.get(id=venue_category_id)
        venues_list = []

        # Get a unique list of venue names (avoid getting duplicates across tournaments)
        for venue in set(base_venue_category.venues.order_by('name').values_list('name', flat=True)):
            venues_list.append({'name': venue, 'debates': []})
            # All Debates, with a matching round, at the same venue category
            venues_list[-1]['debates'] = Debate.objects.filter(
                round__seq=self.round.seq, venue__name=venue).order_by('round__tournament__seq').all()
            print(venues_list[-1])

        kwargs['base_venue_category'] = base_venue_category
        kwargs['venues'] = venues_list
        return super().get_context_data(**kwargs)


class BasePrintFeedbackFormsView(RoundMixin, TemplateView):

    template_name = 'feedback_list.html'

    def add_defaults(self):
        default_questions = []

        if self.tournament.pref('feedback_introduction'):
            default_scale_info = AdjudicatorFeedbackQuestion(
                text=self.tournament.pref('feedback_introduction'), seq=0,
                answer_type='comment', # Custom type just for print display
                required=True, from_team=True, from_adj=True
            )
            default_questions.append(default_scale_info.serialize())

        default_scale_question = AdjudicatorFeedbackQuestion(
            text=_("Overall Score"), seq=0,
            answer_type=AdjudicatorFeedbackQuestion.ANSWER_TYPE_INTEGER_SCALE,
            required=True, from_team=True, from_adj=True,
            min_value=self.tournament.pref('adj_min_score'),
            max_value=self.tournament.pref('adj_max_score')
        )
        default_questions.append(default_scale_question.serialize())

        return default_questions

    def questions_dict(self):
        questions = self.add_defaults()
        for question in self.tournament.adj_feedback_questions:
            questions.append(question.serialize())

        return questions

    def construct_info(self, venue, source, source_p, target, target_p):
        if hasattr(source, 'name'):
            source_n = source.name
        elif use_team_code_names(self.tournament, False):
            source_n = source.code_name
        else:
            source_n = source.short_name

        return {
            'venue': venue.serialize() if venue else '',
            'authorInstitution': source.institution.code if source.institution else _("Unaffiliated"),
            'author': source_n, 'authorPosition': source_p,
            'target': target.name, 'targetPosition': target_p,
        }

    def get_team_feedbacks(self, debate, team):
        if len(debate.adjudicators) == 0:
            return []

        team_paths = self.tournament.pref('feedback_from_teams')
        ballots = []

        if team_paths == 'orallist' and debate.adjudicators.chair:
            ballots.append(self.construct_info(debate.venue, team, _("Team"),
                                               debate.adjudicators.chair, ""))
        elif team_paths == 'all-adjs':
            for target in debate.adjudicators.all():
                ballots.append(self.construct_info(debate.venue, team, _("Team"), target, ""))

        return ballots

    def get_adj_feedbacks(self, debate):
        adj_paths = self.tournament.pref('feedback_paths')
        ballots = []

        debateadjs = debate.debateadjudicator_set.all()
        for debateadj in debateadjs:
            sadj = debateadj.adjudicator
            spos = debate.adjudicators.get_position(sadj)
            targets = expected_feedback_targets(debateadj, feedback_paths=adj_paths, debate=debate)
            for tadj, tpos in targets:
                ballots.append(self.construct_info(debate.venue, sadj, spos, tadj, tpos))

        return ballots

    def get_context_data(self, **kwargs):
        draw = self.round.debate_set_with_prefetches(institutions=True)
        draw = sorted(draw, key=lambda d: d.venue.display_name if d.venue else "")

        ballots = []
        for debate in draw:
            for team in debate.teams:
                ballots.extend(self.get_team_feedbacks(debate, team))
            ballots.extend(self.get_adj_feedbacks(debate))

        kwargs['ballots'] = json.dumps(ballots)
        kwargs['questions'] = json.dumps(self.questions_dict())

        kwargs['team_questions_exist'] = self.tournament.adjudicatorfeedbackquestion_set.filter(from_team=True).exists()
        kwargs['adj_questions_exist'] = self.tournament.adjudicatorfeedbackquestion_set.filter(from_adj=True).exists()

        return super().get_context_data(**kwargs)


class AdminPrintFeedbackFormsView(AdministratorMixin, BasePrintFeedbackFormsView):
    pass


class AssistantPrintFeedbackFormsView(CurrentRoundMixin, OptionalAssistantTournamentPageMixin, BasePrintFeedbackFormsView):
    assistant_page_permissions = ['all_areas', 'results_draw']


class BasePrintScoresheetsView(RoundMixin, TemplateView):

    template_name = 'scoresheet_list.html'

    def get_ballots_dicts(self):
        draw = self.round.debate_set_with_prefetches(iron=True)

        # Create the DebateIdentifiers for the ballots if needed
        create_identifiers(DebateIdentifier, draw)
        identifiers = DebateIdentifier.objects.values('debate_id', 'barcode')

        draw = sorted(draw, key=lambda d: d.venue.display_name if d.venue else "")
        ballots_dicts = []

        # Force translation before JSON serialization
        sides_and_positions = [(side, [str(pos) for pos in positions])
            for side, positions in side_and_position_names(self.tournament)]

        for debate in draw:
            debate_dict = {}

            if debate.venue:
                debate_dict['venue'] = {'display_name': debate.venue.display_name}
            else:
                debate_dict['venue'] = None

            debate_dict['barcode'] = next((i['barcode'] for i in identifiers if i['debate_id'] == debate.id), None)

            debate_dict['debateTeams'] = []
            for side, (side_name, positions) in zip(self.tournament.sides, sides_and_positions):
                dt_dict = {'side_name': side_name, 'positions': positions}
                try:
                    team = debate.get_team(side)
                    dt_dict['team'] = {
                        'short_name': team.short_name,
                        'code_name': team.code_name,
                        'speakers': [{'name': s.name} for s in team.speakers],
                        'iron': debate.get_dt(side).iron_prev > 0,
                    }
                except DebateTeam.DoesNotExist:
                    dt_dict['team'] = None
                debate_dict['debateTeams'].append(dt_dict)

            debate_dict['debateAdjudicators'] = []
            for adj, pos in debate.adjudicators.with_positions():
                da_dict = {'position': pos}
                da_dict['adjudicator'] = {
                    'name': adj.name,
                    'institution': {'code': adj.institution.code if adj.institution else _("Unaffiliated")},
                }
                debate_dict['debateAdjudicators'].append(da_dict)

            if self.round.ballots_per_debate == 'per-adj':
                authors = list(debate.adjudicators.voting_with_positions())
            else:
                authors = [(debate.adjudicators.chair, debate.adjudicators.POSITION_CHAIR)]

            blank_author_dict = {
                'author': "_______________________________________________",
                'authorInstitution': "",
                'authorPosition': "",
            }

            # Add a ballot for each author
            for author, pos in authors:
                if author:
                    ballot_dict = {
                        'author': author.name,
                        'authorInstitution': author.institution.code if author.institution else _("Unaffiliated"),
                        'authorPosition': pos,
                    }
                else:
                    ballot_dict = blank_author_dict

                ballot_dict.update(debate_dict)
                ballots_dicts.append(ballot_dict)

            if len(authors) == 0:
                ballot_dict = blank_author_dict
                ballot_dict.update(debate_dict)
                ballots_dicts.append(ballot_dict)

        return ballots_dicts

    def get_context_data(self, **kwargs):
        kwargs['ballots'] = json.dumps(self.get_ballots_dicts())
        motions = self.round.motion_set.order_by('seq')
        kwargs['motions'] = json.dumps([{'seq': m.seq, 'text': m.text} for m in motions])
        kwargs['use_team_code_names'] = use_team_code_names(self.tournament, False)
        return super().get_context_data(**kwargs)


class AdminPrintScoresheetsView(AdministratorMixin, BasePrintScoresheetsView):
    pass


class AssistantPrintScoresheetsView(CurrentRoundMixin, OptionalAssistantTournamentPageMixin, BasePrintScoresheetsView):
    assistant_page_permissions = ['all_areas']


class PrintableRandomisedURLs(TournamentMixin, AdministratorMixin, TemplateView):

    template_name = 'randomised_url_sheets.html'

    def add_urls(self, participants):
        for participant in participants:
            url = reverse_tournament('privateurls-person-index', self.tournament, kwargs={'url_key': participant['url_key']})
            abs_url = self.request.build_absolute_uri(url)
            qr_code = qrcode.make(abs_url, image_factory=svg.SvgPathImage)

            participant['url'] = abs_url
            participant['qr'] = ' '.join(qr_code._generate_subpaths())

        return participants

    def get_context_data(self, **kwargs):

        if not self.tournament.pref('share_adjs'):
            participants = self.tournament.participants.filter(url_key__isnull=False)
        else:
            participants = Person.objects.filter(
                Q(speaker__team__tournament=self.tournament) | Q(adjudicator__tournament__isnull=True) & Q(url_key__isnull=False))

        participants_array = list(participants.select_related('speaker', 'speaker__team', 'adjudicator__institution', 'adjudicator')
            .values('name', 'speaker__team__short_name', 'adjudicator__institution__code', 'url_key'))
        kwargs['parts'] = self.add_urls(participants_array)

        kwargs['exists'] = self.tournament.participants.filter(url_key__isnull=False).exists()

        return super().get_context_data(**kwargs)
