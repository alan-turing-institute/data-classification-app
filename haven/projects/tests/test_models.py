import pytest
from django.core.exceptions import ValidationError

from core import recipes
from data.classification import insert_initial_questions
from data.models import ClassificationQuestion
from projects.models import Policy, PolicyAssignment, PolicyGroup
from projects.policies import insert_initial_policies
from projects.roles import ProjectRole


@pytest.mark.django_db
class TestProject:
    def test_add_new_user(self, programme_manager, project_participant):
        project = recipes.project.make()

        part = project.add_user(
            project_participant,
            ProjectRole.RESEARCHER.value,
            programme_manager
        )

        assert project.participant_set.count() == 1
        assert project.participant_set.first() == part
        assert part.user.username == 'project_participant@example.com'
        assert part.role == 'researcher'
        assert part.created_by == programme_manager

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
            role=ProjectRole.PROJECT_MANAGER.value, project=project)

        project.classify_as(0, investigator.user)
        project.classify_as(1, data_rep.user)
        project.classify_as(1, rc.user)

        assert project.is_classification_ready
        assert project.tier_conflict
        assert not project.has_tier

    def test_classify_project_not_partipant(self):
        project = recipes.project.make()
        other_project = recipes.project.make()
        investigator = recipes.participant.make(
            role=ProjectRole.INVESTIGATOR.value, project=other_project)

        with pytest.raises(ValidationError):
            project.classify_as(0, investigator.user)

    def test_classify_project_role_changed(self):
        project = recipes.project.make()
        investigator = recipes.participant.make(
            role=ProjectRole.INVESTIGATOR.value, project=project)
        data_rep = recipes.participant.make(
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, project=project)

        project.classify_as(0, investigator.user)
        investigator.role = ProjectRole.RESEARCHER.value
        investigator.save()

        project.classify_as(0, data_rep.user)

        assert project.is_classification_ready
        assert not project.tier_conflict
        assert project.has_tier
        assert project.tier == 0

    def test_classify_project_participant_removed(self):
        project = recipes.project.make()
        investigator = recipes.participant.make(
            role=ProjectRole.INVESTIGATOR.value, project=project)
        data_rep = recipes.participant.make(
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, project=project)

        project.classify_as(0, investigator.user)
        investigator.delete()

        project.classify_as(0, data_rep.user)

        assert project.is_classification_ready
        assert not project.tier_conflict
        assert project.has_tier
        assert project.tier == 0

    def test_classify_project_store_questions(self):
        project = recipes.project.make()
        investigator = recipes.participant.make(
            role=ProjectRole.INVESTIGATOR.value, project=project)

        questions = [
            ('Is the data open?', True),
            ('Is the data personal?', False),
            ('Will you be working in an open fashion?', True),
        ]
        project.classify_as(0, investigator.user, questions)

        classification = project.classification_for(investigator.user).first()
        saved_questions = classification.questions.order_by('order')
        assert questions == [(q.question, q.answer) for q in saved_questions]

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

    def test_project_policy_tier0(self, classified_project):
        insert_initial_policies(PolicyGroup, Policy, PolicyAssignment)
        project = classified_project(0)
        assert project.has_tier

        expected = [
            ['tier', 'tier_0'],
            ['mirror', 'mirror_open'],
            ['inbound', 'inbound_open'],
            ['outbound', 'outbound_open'],
            ['device', 'device_open'],
            ['physical', 'physical_open'],
            ['user', 'user_open'],
            ['connection', 'connection_ssh'],
            ['internet', 'internet_allowed'],
            ['software', 'software_open'],
            ['ingress', 'ingress_open'],
            ['copy', 'copy_allowed'],
            ['ref_class', 'ref_class_open'],
            ['ref_reclass', 'ref_reclass_open'],
            ['egress', 'egress_allowed'],
        ]
        table = [[p.policy.group.name, p.policy.name] for p in project.get_policies()]
        assert table == expected

    def test_project_policy_tier1(self, classified_project):
        insert_initial_policies(PolicyGroup, Policy, PolicyAssignment)
        project = classified_project(1)
        assert project.has_tier

        expected = [
            ['tier', 'tier_1'],
            ['mirror', 'mirror_open'],
            ['inbound', 'inbound_open'],
            ['outbound', 'outbound_open'],
            ['device', 'device_open'],
            ['physical', 'physical_open'],
            ['user', 'user_open'],
            ['connection', 'connection_ssh'],
            ['internet', 'internet_allowed'],
            ['software', 'software_open'],
            ['ingress', 'ingress_open'],
            ['copy', 'copy_allowed'],
            ['ref_class', 'ref_class_open'],
            ['ref_reclass', 'ref_reclass_open'],
            ['egress', 'egress_allowed'],
        ]
        table = [[p.policy.group.name, p.policy.name] for p in project.get_policies()]
        assert table == expected

    def test_project_policy_tier2(self, classified_project):
        insert_initial_policies(PolicyGroup, Policy, PolicyAssignment)
        project = classified_project(2)
        assert project.has_tier

        expected = [
            ['tier', 'tier_2'],
            ['mirror', 'mirror_delay'],
            ['inbound', 'inbound_institution'],
            ['outbound', 'outbound_restricted'],
            ['device', 'device_open'],
            ['physical', 'physical_open'],
            ['user', 'user_open'],
            ['connection', 'connection_rdp'],
            ['internet', 'internet_forbidden'],
            ['software', 'software_airlock'],
            ['ingress', 'ingress_open'],
            ['copy', 'copy_restricted'],
            ['ref_class', 'ref_class_required'],
            ['ref_reclass', 'ref_reclass_open'],
            ['egress', 'egress_allowed'],
        ]
        table = [[p.policy.group.name, p.policy.name] for p in project.get_policies()]
        assert table == expected

    def test_project_policy_tier3(self, classified_project):
        insert_initial_policies(PolicyGroup, Policy, PolicyAssignment)
        project = classified_project(3)
        assert project.has_tier

        expected = [
            ['tier', 'tier_3'],
            ['mirror', 'mirror_whitelist'],
            ['inbound', 'inbound_restricted'],
            ['outbound', 'outbound_restricted'],
            ['device', 'device_managed'],
            ['physical', 'physical_medium'],
            ['user', 'user_signoff'],
            ['connection', 'connection_rdp'],
            ['internet', 'internet_forbidden'],
            ['software', 'software_signoff'],
            ['ingress', 'ingress_secure'],
            ['copy', 'copy_forbidden'],
            ['ref_class', 'ref_class_required'],
            ['ref_reclass', 'ref_reclass_required'],
            ['egress', 'egress_signoff'],
        ]
        table = [[p.policy.group.name, p.policy.name] for p in project.get_policies()]
        assert table == expected

    def test_project_policy_tier4(self, classified_project):
        insert_initial_policies(PolicyGroup, Policy, PolicyAssignment)
        project = classified_project(4)
        assert project.has_tier

        expected = [
            ['tier', 'tier_4'],
            ['mirror', 'mirror_whitelist'],
            ['inbound', 'inbound_restricted'],
            ['outbound', 'outbound_restricted'],
            ['device', 'device_managed'],
            ['physical', 'physical_high'],
            ['user', 'user_signoff'],
            ['connection', 'connection_rdp'],
            ['internet', 'internet_forbidden'],
            ['software', 'software_signoff'],
            ['ingress', 'ingress_secure'],
            ['copy', 'copy_forbidden'],
            ['ref_class', 'ref_class_required'],
            ['ref_reclass', 'ref_reclass_required'],
            ['egress', 'egress_signoff'],
        ]
        table = [[p.policy.group.name, p.policy.name] for p in project.get_policies()]
        assert table == expected
