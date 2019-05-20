import pytest

from core import recipes
from data.classification import insert_initial_questions
from data.models import ClassificationQuestion
from projects.roles import ProjectRole


@pytest.mark.django_db
class TestProject:
    def test_add_new_user(self, research_coordinator):
        project = recipes.project.make()

        part = project.add_user(
            'newuser',
            ProjectRole.RESEARCHER.value,
            research_coordinator
        )

        assert project.participant_set.count() == 1
        assert project.participant_set.first() == part
        assert part.user.username == 'newuser'
        assert part.role == 'researcher'
        assert part.created_by == research_coordinator

    def test_add_existing_user(self, research_coordinator, project_participant):
        project = recipes.project.make()

        part = project.add_user(
            project_participant.username,
            ProjectRole.RESEARCHER.value,
            research_coordinator
        )

        assert project.participant_set.count() == 1
        assert project.participant_set.first() == part
        assert part.user == project_participant
        assert part.role == 'researcher'
        assert part.created_by == research_coordinator

    def test_classify_project(self):
        project = recipes.project.make()
        investigator = recipes.participant.make(
            role=ProjectRole.INVESTIGATOR.value, project=project)
        data_rep = recipes.participant.make(
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, project=project)

        project.classify_as(0, investigator.user)
        project.classify_as(0, data_rep.user)

        assert project.is_classification_ready
        assert not project.tier_conflict
        assert project.has_tier
        assert project.tier == 0

    def test_classification_not_ready(self):
        project = recipes.project.make()
        data_rep = recipes.participant.make(
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, project=project)

        project.classify_as(0, data_rep.user)

        assert not project.is_classification_ready
        assert not project.has_tier

    def test_classify_project_tier2(self):
        project = recipes.project.make()
        investigator = recipes.participant.make(
            role=ProjectRole.INVESTIGATOR.value, project=project)
        data_rep = recipes.participant.make(
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, project=project)
        ref = recipes.participant.make(
            role=ProjectRole.REFEREE.value, project=project)

        project.classify_as(2, investigator.user)
        project.classify_as(2, data_rep.user)
        project.classify_as(2, ref.user)

        assert project.is_classification_ready
        assert not project.tier_conflict
        assert project.has_tier
        assert project.tier == 2

    def test_classification_not_ready_tier2(self):
        project = recipes.project.make()
        investigator = recipes.participant.make(
            role=ProjectRole.INVESTIGATOR.value, project=project)
        data_rep = recipes.participant.make(
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, project=project)

        project.classify_as(2, investigator.user)
        project.classify_as(2, data_rep.user)

        assert not project.is_classification_ready
        assert not project.has_tier

    def test_tier_conflict(self):
        project = recipes.project.make()
        investigator = recipes.participant.make(
            role=ProjectRole.INVESTIGATOR.value, project=project)
        data_rep = recipes.participant.make(
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, project=project)
        rc = recipes.participant.make(
            role=ProjectRole.RESEARCH_COORDINATOR.value, project=project)

        project.classify_as(0, investigator.user)
        project.classify_as(1, data_rep.user)
        project.classify_as(1, rc.user)

        assert project.is_classification_ready
        assert project.tier_conflict
        assert not project.has_tier

    def test_ordered_questions(self):
        insert_initial_questions(ClassificationQuestion)
        questions = ClassificationQuestion.objects.get_ordered_questions()
        assert len(questions) == 13

        ordered = [
            'public_and_open',
            'open_identify_living',
            'publishable',
            'open_generate_new',
            'closed_personal',
            'open_publication',
            'closed_identify_living',
            'substantial_threat',
            'no_reidentify_absolute',
            'include_commercial',
            'no_reidentify_strong',
            'financial_low',
            'sophisticated_attack',
        ]
        assert [q.name for q in questions] == ordered

    def test_classify_questions_tier0(self):
        insert_initial_questions(ClassificationQuestion)
        q = ClassificationQuestion.objects.get_starting_question()
        assert q.name == 'public_and_open'
        q = q.answer_no()
        assert q.name == 'publishable'
        q = q.answer_yes()
        assert q.name == 'open_publication'
        tier = q.answer_yes()
        assert tier == 0

    def test_classify_questions_tier1(self):
        insert_initial_questions(ClassificationQuestion)
        q = ClassificationQuestion.objects.get_starting_question()
        assert q.name == 'public_and_open'
        q = q.answer_yes()
        assert q.name == 'open_identify_living'
        q = q.answer_yes()
        assert q.name == 'open_generate_new'
        q = q.answer_no()
        assert q.name == 'open_publication'
        tier = q.answer_no()
        assert tier == 1

    def test_classify_questions_tier2(self):
        insert_initial_questions(ClassificationQuestion)
        q = ClassificationQuestion.objects.get_starting_question()
        assert q.name == 'public_and_open'
        q = q.answer_no()
        assert q.name == 'publishable'
        q = q.answer_no()
        assert q.name == 'closed_personal'
        q = q.answer_yes()
        assert q.name == 'closed_identify_living'
        q = q.answer_no()
        assert q.name == 'no_reidentify_absolute'
        q = q.answer_no()
        assert q.name == 'no_reidentify_strong'
        tier = q.answer_yes()
        assert tier == 2

    def test_classify_questions_tier3(self):
        insert_initial_questions(ClassificationQuestion)
        q = ClassificationQuestion.objects.get_starting_question()
        assert q.name == 'public_and_open'
        q = q.answer_no()
        assert q.name == 'publishable'
        q = q.answer_no()
        assert q.name == 'closed_personal'
        q = q.answer_no()
        assert q.name == 'include_commercial'
        q = q.answer_yes()
        assert q.name == 'financial_low'
        q = q.answer_no()
        assert q.name == 'sophisticated_attack'
        tier = q.answer_no()
        assert tier == 3

    def test_classify_questions_tier4(self):
        insert_initial_questions(ClassificationQuestion)
        q = ClassificationQuestion.objects.get_starting_question()
        assert q.name == 'public_and_open'
        q = q.answer_yes()
        assert q.name == 'open_identify_living'
        q = q.answer_yes()
        assert q.name == 'open_generate_new'
        q = q.answer_yes()
        assert q.name == 'substantial_threat'
        tier = q.answer_yes()
        assert tier == 4
