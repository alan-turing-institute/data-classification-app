import pytest

from core import recipes
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
