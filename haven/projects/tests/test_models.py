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

    def test_add_dataset(self, programme_manager, user1):
        project = recipes.project.make()
        dataset = recipes.dataset.make(default_representative=user1)
        project.add_user(user1, ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, programme_manager)

        project.add_dataset(dataset, user1, programme_manager)

        assert project.projectdataset_set.first().representative == user1

    def test_add_dataset_wrong_role(self, programme_manager, user1):
        project = recipes.project.make()
        dataset = recipes.dataset.make(default_representative=user1)
        project.add_user(user1, ProjectRole.INVESTIGATOR.value, programme_manager)

        with pytest.raises(ValidationError):
            project.add_dataset(dataset, user1, programme_manager)


@pytest.mark.django_db
class TestWorkPackage:
    def test_classify_work_package(self):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)
        investigator = recipes.participant.make(
            role=ProjectRole.INVESTIGATOR.value, project=project)
        data_rep = recipes.participant.make(
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, project=project)

        work_package.classify_as(0, investigator.user)
        work_package.classify_as(0, data_rep.user)

        assert work_package.is_classification_ready
        assert not work_package.tier_conflict
        assert work_package.has_tier
        assert work_package.tier == 0

    def test_classification_not_ready(self):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)
        data_rep = recipes.participant.make(
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, project=project)

        work_package.classify_as(0, data_rep.user)

        assert not work_package.is_classification_ready
        assert not work_package.has_tier

    def test_classify_work_package_multiple_dprs(self):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)
        investigator = recipes.participant.make(
            role=ProjectRole.INVESTIGATOR.value, project=project)
        data_rep = recipes.participant.make(
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, project=project)
        data_rep2 = recipes.participant.make(
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, project=project)

        work_package.classify_as(0, investigator.user)
        work_package.classify_as(0, data_rep.user)

        assert not work_package.is_classification_ready
        assert not work_package.has_tier

        work_package.classify_as(0, data_rep2.user)

        assert work_package.is_classification_ready
        assert not work_package.tier_conflict
        assert work_package.has_tier
        assert work_package.tier == 0

    def test_classify_work_package_tier2(self):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)
        investigator = recipes.participant.make(
            role=ProjectRole.INVESTIGATOR.value, project=project)
        data_rep = recipes.participant.make(
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, project=project)
        ref = recipes.participant.make(
            role=ProjectRole.REFEREE.value, project=project)

        work_package.classify_as(2, investigator.user)
        work_package.classify_as(2, data_rep.user)
        work_package.classify_as(2, ref.user)

        assert work_package.is_classification_ready
        assert not work_package.tier_conflict
        assert work_package.has_tier
        assert work_package.tier == 2

    def test_classification_not_ready_tier2(self):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)
        investigator = recipes.participant.make(
            role=ProjectRole.INVESTIGATOR.value, project=project)
        data_rep = recipes.participant.make(
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, project=project)

        work_package.classify_as(2, investigator.user)
        work_package.classify_as(2, data_rep.user)

        assert not work_package.is_classification_ready
        assert not work_package.has_tier

    def test_tier_conflict(self):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)
        investigator = recipes.participant.make(
            role=ProjectRole.INVESTIGATOR.value, project=project)
        data_rep = recipes.participant.make(
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, project=project)
        rc = recipes.participant.make(
            role=ProjectRole.PROJECT_MANAGER.value, project=project)

        work_package.classify_as(0, investigator.user)
        work_package.classify_as(1, data_rep.user)
        work_package.classify_as(1, rc.user)

        assert work_package.is_classification_ready
        assert work_package.tier_conflict
        assert not work_package.has_tier

    def test_classify_work_package_not_partipant(self):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)
        other_project = recipes.project.make()
        investigator = recipes.participant.make(
            role=ProjectRole.INVESTIGATOR.value, project=other_project)

        with pytest.raises(ValidationError):
            work_package.classify_as(0, investigator.user)

    def test_classify_work_package_role_changed(self):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)
        investigator = recipes.participant.make(
            role=ProjectRole.INVESTIGATOR.value, project=project)
        data_rep = recipes.participant.make(
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, project=project)

        work_package.classify_as(0, investigator.user)
        investigator.role = ProjectRole.RESEARCHER.value
        investigator.save()

        work_package.classify_as(0, data_rep.user)

        assert work_package.is_classification_ready
        assert not work_package.tier_conflict
        assert work_package.has_tier
        assert work_package.tier == 0

    def test_classify_work_package_participant_removed(self):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)
        investigator = recipes.participant.make(
            role=ProjectRole.INVESTIGATOR.value, project=project)
        data_rep = recipes.participant.make(
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, project=project)

        work_package.classify_as(0, investigator.user)
        investigator.delete()

        work_package.classify_as(0, data_rep.user)

        assert work_package.is_classification_ready
        assert not work_package.tier_conflict
        assert work_package.has_tier
        assert work_package.tier == 0

    def test_classify_work_package_store_questions(self):
        insert_initial_questions(ClassificationQuestion)
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)
        investigator = recipes.participant.make(
            role=ProjectRole.INVESTIGATOR.value, project=project)

        questions = []
        q = ClassificationQuestion.objects.get_starting_question()
        questions.append((q, True))
        q = q.answer_yes()
        questions.append((q, False))
        q = q.answer_no()
        questions.append((q, True))
        tier = q.answer_yes()
        work_package.classify_as(tier, investigator.user, questions)

        for q in ClassificationQuestion.objects.all():
            q.name = q.name + '_v2'
            q.save()

        classification = work_package.classification_for(investigator.user).first()
        expected = [
            ('public_and_open', True),
            ('open_identify_living', False),
            ('open_publication', True),
        ]

        saved_questions = classification.questions.order_by('order')
        assert expected == [(q.question_at_time.name, q.answer) for q in saved_questions]

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

    def test_work_package_policy_tier0(self, classified_work_package):
        insert_initial_policies(PolicyGroup, Policy, PolicyAssignment)
        work_package = classified_work_package(0)
        assert work_package.has_tier

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
        table = [[p.policy.group.name, p.policy.name] for p in work_package.get_policies()]
        assert table == expected

    def test_work_package_policy_tier1(self, classified_work_package):
        insert_initial_policies(PolicyGroup, Policy, PolicyAssignment)
        work_package = classified_work_package(1)
        assert work_package.has_tier

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
        table = [[p.policy.group.name, p.policy.name] for p in work_package.get_policies()]
        assert table == expected

    def test_work_package_policy_tier2(self, classified_work_package):
        insert_initial_policies(PolicyGroup, Policy, PolicyAssignment)
        work_package = classified_work_package(2)
        assert work_package.has_tier

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
        table = [[p.policy.group.name, p.policy.name] for p in work_package.get_policies()]
        assert table == expected

    def test_work_package_policy_tier3(self, classified_work_package):
        insert_initial_policies(PolicyGroup, Policy, PolicyAssignment)
        work_package = classified_work_package(3)
        assert work_package.has_tier

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
        table = [[p.policy.group.name, p.policy.name] for p in work_package.get_policies()]
        assert table == expected

    def test_work_package_policy_tier4(self, classified_work_package):
        insert_initial_policies(PolicyGroup, Policy, PolicyAssignment)
        work_package = classified_work_package(4)
        assert work_package.has_tier

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
        table = [[p.policy.group.name, p.policy.name] for p in work_package.get_policies()]
        assert table == expected
