import re

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from haven.core import recipes
from haven.data.classification import insert_initial_questions
from haven.data.models import ClassificationGuidance, ClassificationQuestion
from haven.projects.models import (
    Policy,
    PolicyAssignment,
    PolicyGroup,
    Project,
    ProjectDataset,
    WorkPackageParticipant,
    WorkPackageStatus,
    a_or_an,
)
from haven.projects.policies import insert_initial_policies
from haven.projects.roles import ProjectRole


@pytest.mark.django_db
class TestProject:
    def test_add_default_work_packages(self, programme_manager):
        project = recipes.project.make()
        assert project.work_packages.count() == 0

        project.add_default_work_packages(programme_manager)
        assert project.work_packages.count() == 3
        packages = project.work_packages.all()
        assert packages[0].name == "Egress – Full"
        assert packages[1].name == "Egress – Reports"
        assert packages[2].name == "Egress – Full"

    def test_add_new_user(self, programme_manager, project_participant):
        project = recipes.project.make()

        part = project.add_user(
            project_participant, ProjectRole.RESEARCHER.value, programme_manager
        )

        assert project.participants.count() == 1
        assert project.participants.first() == part
        assert part.user.username == "project_participant@example.com"
        assert part.role == "researcher"
        assert part.created_by == programme_manager

    def test_add_dataset(self, programme_manager, user1):
        project = recipes.project.make()
        dataset = recipes.dataset.make(default_representative=user1)
        project.add_user(
            user1, ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, programme_manager
        )

        project.add_dataset(dataset, user1, programme_manager)

        assert project.get_representative(dataset) == user1

    def test_add_dataset_wrong_role(self, programme_manager, user1):
        project = recipes.project.make()
        dataset = recipes.dataset.make(default_representative=user1)
        project.add_user(user1, ProjectRole.INVESTIGATOR.value, programme_manager)

        with pytest.raises(ValidationError):
            project.add_dataset(dataset, user1, programme_manager)

    def test_new_investigator_added_to_wp(self, programme_manager, project_participant):
        project = recipes.project.make()
        work_package = recipes.work_package.make(project=project)

        participant = project.add_user(
            project_participant, ProjectRole.INVESTIGATOR.value, programme_manager
        )

        assert project.participants.count() == 1
        assert work_package.participants.count() == 1
        assert participant == work_package.participants.first()

    def test_investigator_added_to_new_wp(self, programme_manager, project_participant):
        project = recipes.project.make()

        participant = project.add_user(
            project_participant, ProjectRole.INVESTIGATOR.value, programme_manager
        )

        work_package = recipes.work_package.make()
        project.add_work_package(work_package, programme_manager)

        assert project.participants.count() == 1
        assert work_package.participants.count() == 1
        assert participant == work_package.participants.first()


@pytest.mark.django_db
class TestWorkPackage:
    def test_new_permissions(self, classified_work_package):
        work_package = classified_work_package(None)
        work_package.status = WorkPackageStatus.NEW.value

        assert work_package.can_edit_work_package
        assert work_package.can_delete_work_package
        assert work_package.can_add_participants
        assert work_package.can_list_participants
        assert work_package.can_edit_participants
        assert not work_package.can_approve_participants
        assert work_package.can_add_datasets
        assert work_package.can_edit_datasets
        assert work_package.can_edit_datasets_dpr
        assert work_package.can_delete_datasets
        assert not work_package.can_classify_data
        assert work_package.can_open_classification
        assert not work_package.can_close_classification

    def test_underway_permissions(self, classified_work_package):
        work_package = classified_work_package(0)
        work_package.status = WorkPackageStatus.UNDERWAY.value

        assert not work_package.can_edit_work_package
        assert not work_package.can_delete_work_package
        assert work_package.can_add_participants
        assert work_package.can_list_participants
        assert work_package.can_edit_participants
        assert work_package.can_approve_participants
        assert not work_package.can_add_datasets
        assert not work_package.can_edit_datasets
        assert work_package.can_edit_datasets_dpr
        assert not work_package.can_delete_datasets
        assert work_package.can_view_classification
        assert work_package.can_classify_data
        assert not work_package.can_open_classification
        assert work_package.can_close_classification

    def test_classified_permissions(self, classified_work_package):
        work_package = classified_work_package(0)
        work_package.status = WorkPackageStatus.CLASSIFIED.value

        assert not work_package.can_edit_work_package
        assert not work_package.can_delete_work_package
        assert work_package.can_add_participants
        assert work_package.can_list_participants
        assert work_package.can_edit_participants
        assert work_package.can_approve_participants
        assert not work_package.can_add_datasets
        assert not work_package.can_edit_datasets
        assert work_package.can_edit_datasets_dpr
        assert not work_package.can_delete_datasets
        assert work_package.can_view_classification
        assert not work_package.can_classify_data
        assert not work_package.can_open_classification
        assert not work_package.can_close_classification

    def test_add_dataset(self, programme_manager, user1):
        project = recipes.project.make()
        dataset = recipes.dataset.make()
        participant = project.add_user(
            user1, ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, programme_manager
        )
        work_package = recipes.work_package.make(project=project)

        project.add_dataset(dataset, user1, programme_manager)
        work_package.add_dataset(dataset, programme_manager)

        assert work_package.datasets.count() == 1
        assert dataset == work_package.datasets.first()
        assert work_package.participants.count() == 1
        assert participant == work_package.participants.first()

    def test_add_dataset_multiple_times(self, programme_manager, user1):
        project = recipes.project.make()
        dataset = recipes.dataset.make()
        project.add_user(
            user1, ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, programme_manager
        )
        work_package = recipes.work_package.make(project=project)

        project.add_dataset(dataset, user1, programme_manager)
        work_package.add_dataset(dataset, programme_manager)

        with pytest.raises(ValidationError):
            work_package.add_dataset(dataset, programme_manager)

        assert work_package.datasets.count() == 1
        assert dataset == work_package.datasets.first()

    def test_add_dataset_not_on_project(self, programme_manager, user1):
        project = recipes.project.make()
        dataset = recipes.dataset.make()
        work_package = recipes.work_package.make(project=project)

        with pytest.raises(ValidationError):
            work_package.add_dataset(dataset, programme_manager)

    def test_classification_reset(
        self, classified_work_package, investigator, data_provider_representative
    ):
        work_package = classified_work_package(None)
        dataset = work_package.datasets.first()

        work_package.classify_as(3, investigator.user)
        work_package.classify_as(3, data_provider_representative.user)

        assert work_package.classifications.count() == 2
        assert work_package.missing_classification_requirements == [
            "Each Data Provider Representative for this Work Package needs to approve the Referee."
        ]

        work_package.clear_classifications()
        assert work_package.status == WorkPackageStatus.NEW.value
        assert work_package.classifications.count() == 0
        assert work_package.missing_classification_requirements == [
            "An Investigator still needs to classify this Work Package.",
            f"A Data Provider Representative for dataset {dataset.name} still needs to classify "
            f"this Work Package.",
        ]

    def test_classify_work_package_no_dataset(
        self, classified_work_package, investigator, data_provider_representative
    ):
        work_package = classified_work_package(None)
        work_package.datasets.clear()

        with pytest.raises(ValidationError):
            work_package.classify_as(0, investigator.user)

    def test_classify_work_package(
        self, classified_work_package, investigator, data_provider_representative
    ):
        work_package = classified_work_package(None)

        assert not work_package.has_user_classified(investigator.user)
        work_package.classify_as(0, investigator.user)
        assert work_package.has_user_classified(investigator.user)

        assert not work_package.has_user_classified(data_provider_representative.user)
        work_package.classify_as(0, data_provider_representative.user)
        assert work_package.has_user_classified(data_provider_representative.user)

        assert work_package.missing_classification_requirements == []
        assert work_package.is_classification_ready
        assert not work_package.tier_conflict

        work_package.close_classification()
        assert work_package.has_tier
        assert work_package.tier == 0

    def test_classification_not_ready(
        self, classified_work_package, data_provider_representative
    ):
        work_package = classified_work_package(None)

        work_package.classify_as(0, data_provider_representative.user)

        assert work_package.missing_classification_requirements == [
            "An Investigator still needs to classify this Work Package."
        ]
        assert not work_package.is_classification_ready
        assert not work_package.has_tier

    def test_classification_not_ready_dpr(self, classified_work_package, investigator):
        work_package = classified_work_package(None)

        work_package.classify_as(0, investigator.user)

        assert work_package.missing_classification_requirements == [
            "A Data Provider Representative for dataset "
            + work_package.datasets.first().name
            + " still needs to classify this Work Package."
        ]
        assert not work_package.is_classification_ready
        assert not work_package.has_tier

    def test_classification_not_ready_multiple_dprs(
        self, classified_work_package, investigator, data_provider_representative
    ):
        work_package = classified_work_package(None)

        project = work_package.project
        dataset2 = recipes.dataset.make(name="Dataset 2")
        data_rep2 = recipes.participant.make(
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, project=project
        )

        project.add_dataset(dataset2, data_rep2.user, investigator.user)
        work_package.add_dataset(dataset2, investigator.user)

        work_package.classify_as(0, investigator.user)
        work_package.classify_as(0, data_provider_representative.user)
        assert work_package.missing_classification_requirements == [
            "A Data Provider Representative for dataset Dataset 2 still needs to classify this "
            "Work Package."
        ]
        assert not work_package.is_classification_ready
        assert not work_package.has_tier

    def test_classify_work_package_multiple_dprs(
        self, classified_work_package, investigator, data_provider_representative
    ):
        work_package = classified_work_package(None)

        project = work_package.project
        dataset2 = recipes.dataset.make(name="Dataset 2")
        data_rep2 = recipes.participant.make(
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, project=project
        )

        project.add_dataset(dataset2, data_rep2.user, investigator.user)
        work_package.add_dataset(dataset2, investigator.user)

        work_package.classify_as(0, investigator.user)
        work_package.classify_as(0, data_provider_representative.user)

        assert work_package.missing_classification_requirements == [
            "A Data Provider Representative for dataset Dataset 2 still needs to classify this "
            "Work Package."
        ]
        assert not work_package.is_classification_ready
        assert not work_package.has_tier

        work_package.classify_as(0, data_rep2.user)

        assert work_package.missing_classification_requirements == []
        assert work_package.is_classification_ready
        assert not work_package.tier_conflict

        work_package.close_classification()
        assert work_package.has_tier
        assert work_package.tier == 0

    def test_classification_uninvolved_dataset(
        self, classified_work_package, investigator, data_provider_representative
    ):
        work_package = classified_work_package(None)

        project = work_package.project
        dataset2 = recipes.dataset.make()
        data_rep2 = recipes.participant.make(
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, project=project
        )

        project.add_dataset(dataset2, data_rep2.user, investigator.user)

        work_package.classify_as(0, investigator.user)
        work_package.classify_as(0, data_provider_representative.user)

        assert work_package.missing_classification_requirements == []
        assert work_package.is_classification_ready
        assert not work_package.tier_conflict

        work_package.close_classification()
        assert work_package.has_tier
        assert work_package.tier == 0

    def test_classification_dpr_change(
        self, classified_work_package, investigator, data_provider_representative
    ):
        work_package = classified_work_package(None)
        project = work_package.project

        work_package.classify_as(0, data_provider_representative.user)

        data_rep2 = recipes.participant.make(
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, project=project
        )

        pd = ProjectDataset.objects.filter(project=project).first()
        pd.representative = data_rep2.user
        pd.save()

        work_package.classify_as(0, investigator.user)

        assert work_package.missing_classification_requirements == []
        assert work_package.is_classification_ready

        work_package.close_classification()
        assert work_package.has_tier
        assert work_package.tier == 0

    def test_classify_work_package_tier2(
        self,
        classified_work_package,
        investigator,
        data_provider_representative,
        referee,
    ):
        work_package = classified_work_package(None)

        work_package.classify_as(2, investigator.user)
        work_package.classify_as(2, data_provider_representative.user)
        work_package.classify_as(2, referee.user)

        assert work_package.missing_classification_requirements == []
        assert work_package.is_classification_ready
        assert not work_package.tier_conflict

        work_package.close_classification()
        assert work_package.has_tier
        assert work_package.tier == 2

    def test_classification_not_ready_tier2(
        self, classified_work_package, investigator, data_provider_representative
    ):
        work_package = classified_work_package(None)

        work_package.classify_as(2, investigator.user)
        work_package.classify_as(2, data_provider_representative.user)

        assert work_package.missing_classification_requirements == [
            "A Referee still needs to classify this Work Package.",
        ]
        assert not work_package.is_classification_ready
        assert not work_package.has_tier

    def test_classify_work_package_tier3(
        self, classified_work_package, investigator, data_provider_representative
    ):
        work_package = classified_work_package(None)

        referee = work_package.project.get_participant(ProjectRole.REFEREE.value)
        p = referee.get_work_package_participant(work_package)
        p.approve(data_provider_representative.user)

        work_package.classify_as(3, investigator.user)
        work_package.classify_as(3, data_provider_representative.user)
        work_package.classify_as(3, referee.user)

        assert work_package.missing_classification_requirements == []
        assert work_package.is_classification_ready
        assert not work_package.tier_conflict

        work_package.close_classification()
        assert work_package.has_tier
        assert work_package.tier == 3

    def test_classification_not_ready_tier3(
        self, classified_work_package, investigator, data_provider_representative
    ):
        work_package = classified_work_package(None)

        referee = work_package.project.get_participant(ProjectRole.REFEREE.value)

        work_package.classify_as(3, investigator.user)
        work_package.classify_as(3, data_provider_representative.user)

        assert work_package.missing_classification_requirements == [
            "Each Data Provider Representative for this Work Package needs to approve the Referee."
        ]
        assert not work_package.is_classification_ready
        assert not work_package.has_tier

        work_package.classify_as(3, referee.user)

        assert work_package.missing_classification_requirements == [
            "Each Data Provider Representative for this Work Package needs to approve the Referee."
        ]
        assert not work_package.is_classification_ready
        assert not work_package.has_tier

        p = referee.get_work_package_participant(work_package)
        p.approve(data_provider_representative.user)
        work_package = p.work_package

        assert work_package.missing_classification_requirements == []
        assert work_package.is_classification_ready
        assert not work_package.tier_conflict

        work_package.close_classification()
        assert work_package.has_tier
        assert work_package.tier == 3

    def test_referee_not_added_tier3(
        self, investigator, data_provider_representative, programme_manager, referee
    ):

        project = recipes.project.make(created_by=programme_manager)
        work_package = recipes.work_package.make(project=project)
        dataset = recipes.dataset.make()

        project.add_user(
            user=investigator.user,
            role=ProjectRole.INVESTIGATOR.value,
            created_by=programme_manager,
        )
        project.add_user(
            user=data_provider_representative.user,
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
            created_by=programme_manager,
        )
        work_package.add_user(data_provider_representative.user, programme_manager)
        project.add_user(
            user=referee.user,
            role=ProjectRole.REFEREE.value,
            created_by=programme_manager,
        )

        project.add_dataset(
            dataset, data_provider_representative.user, investigator.user
        )
        work_package.add_dataset(dataset, investigator.user)

        work_package.classify_as(3, investigator.user)
        work_package.classify_as(3, data_provider_representative.user)

        assert work_package.missing_classification_requirements == [
            "A Referee needs to be added to this Work Package."
        ]
        assert not work_package.is_classification_ready
        assert not work_package.has_tier

        work_package.add_user(referee.user, programme_manager)
        work_package.classify_as(3, referee.user)

        assert work_package.missing_classification_requirements == [
            "Each Data Provider Representative for this Work Package needs to approve the Referee."
        ]
        assert not work_package.is_classification_ready
        assert not work_package.has_tier

        referee = work_package.project.get_participant(ProjectRole.REFEREE.value)
        p = referee.get_work_package_participant(work_package)
        p.approve(data_provider_representative.user)
        work_package = p.work_package

        assert work_package.missing_classification_requirements == []
        assert work_package.is_classification_ready
        assert not work_package.tier_conflict

        work_package.close_classification()
        assert work_package.has_tier
        assert work_package.tier == 3

    def test_referee_not_added_tier2(
        self, investigator, data_provider_representative, programme_manager, referee
    ):

        project = recipes.project.make(created_by=programme_manager)
        work_package = recipes.work_package.make(project=project)
        dataset = recipes.dataset.make()

        project.add_user(
            user=investigator.user,
            role=ProjectRole.INVESTIGATOR.value,
            created_by=programme_manager,
        )
        project.add_user(
            user=data_provider_representative.user,
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
            created_by=programme_manager,
        )
        work_package.add_user(data_provider_representative.user, programme_manager)
        project.add_user(
            user=referee.user,
            role=ProjectRole.REFEREE.value,
            created_by=programme_manager,
        )

        project.add_dataset(
            dataset, data_provider_representative.user, investigator.user
        )
        work_package.add_dataset(dataset, investigator.user)

        work_package.classify_as(2, investigator.user)
        work_package.classify_as(2, data_provider_representative.user)

        assert work_package.missing_classification_requirements == [
            "A Referee needs to be added to this Work Package."
        ]
        assert not work_package.is_classification_ready
        assert not work_package.has_tier

        work_package.add_user(referee.user, programme_manager)
        work_package.classify_as(2, referee.user)

        assert work_package.missing_classification_requirements == []
        assert work_package.is_classification_ready
        assert not work_package.tier_conflict

        work_package.close_classification()
        assert work_package.has_tier
        assert work_package.tier == 2

    def test_tier_conflict(
        self,
        classified_work_package,
        investigator,
        data_provider_representative,
        referee,
    ):
        work_package = classified_work_package(None)

        work_package.classify_as(0, investigator.user)
        work_package.classify_as(1, data_provider_representative.user)
        work_package.classify_as(1, referee.user)

        assert work_package.missing_classification_requirements == []
        assert work_package.is_classification_ready
        assert work_package.tier_conflict
        assert not work_package.has_tier

    def test_classify_work_package_not_partipant(
        self, classified_work_package, system_manager
    ):
        work_package = classified_work_package(None)

        with pytest.raises(ValidationError):
            work_package.classify_as(0, system_manager)

        work_package.project.add_user(
            system_manager, ProjectRole.REFEREE.value, created_by=system_manager
        )

        with pytest.raises(ValidationError):
            work_package.classify_as(0, system_manager)

    def test_classify_work_package_role_changed(
        self, classified_work_package, investigator, data_provider_representative
    ):
        work_package = classified_work_package(None)

        work_package.classify_as(0, investigator.user)
        investigator.role = ProjectRole.RESEARCHER.value
        investigator.save()

        work_package.classify_as(0, data_provider_representative.user)

        assert work_package.missing_classification_requirements == []
        assert work_package.is_classification_ready
        assert not work_package.tier_conflict

        work_package.close_classification()
        assert work_package.has_tier
        assert work_package.tier == 0

    def test_classify_work_package_participant_removed(
        self, classified_work_package, investigator, data_provider_representative
    ):
        work_package = classified_work_package(None)

        work_package.classify_as(0, investigator.user)
        investigator.delete()

        work_package.classify_as(0, data_provider_representative.user)

        assert work_package.missing_classification_requirements == []
        assert work_package.is_classification_ready
        assert not work_package.tier_conflict

        work_package.close_classification()
        assert work_package.has_tier
        assert work_package.tier == 0

    def test_classify_work_package_store_questions(
        self, classified_work_package, investigator
    ):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        work_package = classified_work_package(None)

        questions = []
        q = ClassificationQuestion.objects.get_starting_question()
        questions.append((q, False))
        q = q.answer_no()
        questions.append((q, False))
        q = q.answer_no()
        questions.append((q, False))
        q = q.answer_no()
        questions.append((q, True))
        tier = q.answer_yes()
        work_package.classify_as(tier, investigator.user, questions)

        for q in ClassificationQuestion.objects.all():
            q.name = q.name + "_v2"
            q.save()

        classification = work_package.classification_for(investigator.user).first()
        expected = [
            ("open_generate_new", False),
            ("closed_personal", False),
            ("include_commercial", False),
            ("open_publication", True),
        ]

        saved_questions = classification.questions.order_by("order")
        assert expected == [
            (q.question_at_time.name, q.answer) for q in saved_questions
        ]

    def test_ordered_questions(self):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        questions = ClassificationQuestion.objects.get_ordered_questions()
        assert len(questions) == 14

        ordered = [
            "open_generate_new",
            "closed_personal",
            "public_and_open",
            "no_reidentify",
            "no_reidentify_absolute",
            "substantial_threat",
            "include_commercial",
            "no_reidentify_strong",
            "financial_low",
            "open_publication",
            "include_commercial_personal",
            "publishable",
            "financial_low_personal",
            "sophisticated_attack",
        ]
        assert [q.name for q in questions] == ordered

    def test_default_guidance(self):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)

        num_questions = 0
        num_question_links = 0
        num_guidance_links = 0

        # This should match what's in WorkPackageClassifyData.get_context_data()
        pattern = re.compile('href="#([^"]+)"')

        all_guidance = {g.name: g for g in ClassificationGuidance.objects.all()}
        for question in ClassificationQuestion.objects.all():
            assert question.name in all_guidance, "Question does not have explanation"
            num_questions += 1

            for name in pattern.findall(question.question):
                assert name in all_guidance, "Question links to missing guidance"
                num_question_links += 1

        for guidance in all_guidance.values():
            for name in pattern.findall(guidance.guidance):
                assert name in all_guidance, "Guidance links to missing guidance"
                num_guidance_links += 1

        # These mostly just exist to make sure the regex is finding *something*
        assert num_questions == 14
        assert num_question_links == 7
        assert num_guidance_links == 1

    def test_classify_questions_tier0(self):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        q = ClassificationQuestion.objects.get_starting_question()
        assert q.name == "open_generate_new"
        q = q.answer_no()
        assert q.name == "closed_personal"
        q = q.answer_no()
        assert q.name == "include_commercial"
        q = q.answer_no()
        assert q.name == "open_publication"
        tier = q.answer_no()
        assert tier == 0

    def test_classify_questions_tier1(self):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        q = ClassificationQuestion.objects.get_starting_question()
        assert q.name == "open_generate_new"
        q = q.answer_no()
        assert q.name == "closed_personal"
        q = q.answer_yes()
        assert q.name == "public_and_open"
        q = q.answer_yes()
        assert q.name == "include_commercial"
        q = q.answer_yes()
        assert q.name == "financial_low"
        q = q.answer_yes()
        assert q.name == "publishable"
        tier = q.answer_yes()
        assert tier == 1

    def test_classify_questions_tier2(self):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        q = ClassificationQuestion.objects.get_starting_question()
        assert q.name == "open_generate_new"
        q = q.answer_no()
        assert q.name == "closed_personal"
        q = q.answer_yes()
        assert q.name == "public_and_open"
        q = q.answer_no()
        assert q.name == "no_reidentify"
        q = q.answer_yes()
        assert q.name == "no_reidentify_absolute"
        q = q.answer_no()
        assert q.name == "no_reidentify_strong"
        q = q.answer_yes()
        assert q.name == "include_commercial_personal"
        q = q.answer_yes()
        assert q.name == "financial_low_personal"
        tier = q.answer_yes()
        assert tier == 2

    def test_classify_questions_tier3(self):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        q = ClassificationQuestion.objects.get_starting_question()
        assert q.name == "open_generate_new"
        q = q.answer_no()
        assert q.name == "closed_personal"
        q = q.answer_no()
        assert q.name == "include_commercial"
        q = q.answer_yes()
        assert q.name == "financial_low"
        q = q.answer_no()
        assert q.name == "sophisticated_attack"
        tier = q.answer_no()
        assert tier == 3

    def test_classify_questions_tier4(self):
        insert_initial_questions(ClassificationQuestion, ClassificationGuidance)
        q = ClassificationQuestion.objects.get_starting_question()
        assert q.name == "open_generate_new"
        q = q.answer_yes()
        assert q.name == "substantial_threat"
        tier = q.answer_yes()
        assert tier == 4

    def test_work_package_policy_tier0(self, classified_work_package):
        insert_initial_policies(PolicyGroup, Policy, PolicyAssignment)
        work_package = classified_work_package(0)
        assert work_package.has_tier

        expected = [
            ["tier", "tier_0"],
            ["mirror", "mirror_open"],
            ["inbound", "inbound_open"],
            ["outbound", "outbound_open"],
            ["device", "device_open"],
            ["physical", "physical_open"],
            ["user", "user_open"],
            ["connection", "connection_ssh"],
            ["internet", "internet_allowed"],
            ["software", "software_open"],
            ["ingress", "ingress_open"],
            ["copy", "copy_allowed"],
            ["ref_class", "ref_class_open"],
            ["ref_reclass", "ref_reclass_open"],
            ["egress", "egress_allowed"],
        ]
        table = [
            [p.policy.group.name, p.policy.name] for p in work_package.get_policies()
        ]
        assert table == expected

    def test_work_package_policy_tier1(self, classified_work_package):
        insert_initial_policies(PolicyGroup, Policy, PolicyAssignment)
        work_package = classified_work_package(1)
        assert work_package.has_tier

        expected = [
            ["tier", "tier_1"],
            ["mirror", "mirror_open"],
            ["inbound", "inbound_open"],
            ["outbound", "outbound_open"],
            ["device", "device_open"],
            ["physical", "physical_open"],
            ["user", "user_open"],
            ["connection", "connection_ssh"],
            ["internet", "internet_allowed"],
            ["software", "software_open"],
            ["ingress", "ingress_open"],
            ["copy", "copy_allowed"],
            ["ref_class", "ref_class_open"],
            ["ref_reclass", "ref_reclass_open"],
            ["egress", "egress_allowed"],
        ]
        table = [
            [p.policy.group.name, p.policy.name] for p in work_package.get_policies()
        ]
        assert table == expected

    def test_work_package_policy_tier2(self, classified_work_package):
        insert_initial_policies(PolicyGroup, Policy, PolicyAssignment)
        work_package = classified_work_package(2)
        assert work_package.has_tier

        expected = [
            ["tier", "tier_2"],
            ["mirror", "mirror_delay"],
            ["inbound", "inbound_institution"],
            ["outbound", "outbound_restricted"],
            ["device", "device_open"],
            ["physical", "physical_open"],
            ["user", "user_open"],
            ["connection", "connection_rdp"],
            ["internet", "internet_forbidden"],
            ["software", "software_airlock"],
            ["ingress", "ingress_open"],
            ["copy", "copy_restricted"],
            ["ref_class", "ref_class_required"],
            ["ref_reclass", "ref_reclass_open"],
            ["egress", "egress_allowed"],
        ]
        table = [
            [p.policy.group.name, p.policy.name] for p in work_package.get_policies()
        ]
        assert table == expected

    def test_work_package_policy_tier3(self, classified_work_package):
        insert_initial_policies(PolicyGroup, Policy, PolicyAssignment)
        work_package = classified_work_package(3)
        assert work_package.has_tier

        expected = [
            ["tier", "tier_3"],
            ["mirror", "mirror_whitelist"],
            ["inbound", "inbound_restricted"],
            ["outbound", "outbound_restricted"],
            ["device", "device_managed"],
            ["physical", "physical_medium"],
            ["user", "user_signoff"],
            ["connection", "connection_rdp"],
            ["internet", "internet_forbidden"],
            ["software", "software_signoff"],
            ["ingress", "ingress_secure"],
            ["copy", "copy_forbidden"],
            ["ref_class", "ref_class_required"],
            ["ref_reclass", "ref_reclass_required"],
            ["egress", "egress_signoff"],
        ]
        table = [
            [p.policy.group.name, p.policy.name] for p in work_package.get_policies()
        ]
        assert table == expected

    def test_work_package_policy_tier4(self, classified_work_package):
        insert_initial_policies(PolicyGroup, Policy, PolicyAssignment)
        work_package = classified_work_package(4)
        assert work_package.has_tier

        expected = [
            ["tier", "tier_4"],
            ["mirror", "mirror_whitelist"],
            ["inbound", "inbound_restricted"],
            ["outbound", "outbound_restricted"],
            ["device", "device_managed"],
            ["physical", "physical_high"],
            ["user", "user_signoff"],
            ["connection", "connection_rdp"],
            ["internet", "internet_forbidden"],
            ["software", "software_signoff"],
            ["ingress", "ingress_secure"],
            ["copy", "copy_forbidden"],
            ["ref_class", "ref_class_required"],
            ["ref_reclass", "ref_reclass_required"],
            ["egress", "egress_signoff"],
        ]
        table = [
            [p.policy.group.name, p.policy.name] for p in work_package.get_policies()
        ]
        assert table == expected

    def test_add_participant(self, programme_manager, user1):
        project = recipes.project.make()
        participant = project.add_user(
            user1, ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, programme_manager
        )
        work_package = recipes.work_package.make(project=project)

        work_package.add_user(user1, programme_manager)

        assert work_package.participants.count() == 1
        assert participant == work_package.participants.first()

    def test_add_participant_repeated(self, programme_manager, user1):
        project = recipes.project.make()
        participant = project.add_user(
            user1, ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, programme_manager
        )
        work_package = recipes.work_package.make(project=project)

        work_package.add_user(user1, programme_manager)

        with pytest.raises(IntegrityError):
            WorkPackageParticipant.objects.create(
                work_package=work_package,
                participant=participant,
                created_by=programme_manager,
            )

    def test_add_participant_not_on_project(self, programme_manager, user1):
        project1 = recipes.project.make()
        project2 = recipes.project.make()
        project1.add_user(
            user1, ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value, programme_manager
        )
        work_package = recipes.work_package.make(project=project2)

        with pytest.raises(ValidationError):
            work_package.add_user(user1, programme_manager)


@pytest.mark.django_db
class TestParticipant:
    def assert_participants_with_approval(self, work_package, approver, expected):
        participants = work_package.get_participants_with_approval(approver)
        actual = [
            [p.participant.role, p.approved, p.approved_by_you] for p in participants
        ]
        assert expected == actual

    def test_participant_not_approved_for_unassigned_work_package(
        self, classified_work_package, user1, programme_manager
    ):
        work_package = classified_work_package(None)
        participant = work_package.project.add_user(
            user1, ProjectRole.RESEARCHER.value, programme_manager
        )
        dpr = work_package.project.get_participant(
            ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value
        )
        assert not work_package.is_participant_approved(participant)
        self.assert_participants_with_approval(
            work_package,
            dpr.user,
            [
                ["investigator", True, True],
                ["data_provider_representative", True, True],
                ["referee", False, False],
            ],
        )

    def test_cannot_approve_participant_for_unassigned_work_package(
        self, classified_work_package, user1, programme_manager
    ):
        work_package = classified_work_package(None)
        participant = work_package.project.add_user(
            user1, ProjectRole.RESEARCHER.value, programme_manager
        )
        dpr = work_package.project.get_participant(
            ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value
        )
        assert participant.get_work_package_participant(work_package) is None
        self.assert_participants_with_approval(
            work_package,
            dpr.user,
            [
                ["investigator", True, True],
                ["data_provider_representative", True, True],
                ["referee", False, False],
            ],
        )

    def test_participant_approved_for_low_tier_work_package(
        self, classified_work_package, user1, programme_manager
    ):
        work_package = classified_work_package(2)
        participant = work_package.project.add_user(
            user1, ProjectRole.RESEARCHER.value, programme_manager
        )
        work_package.add_user(user1, programme_manager)
        dpr = work_package.project.get_participant(
            ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value
        )
        assert work_package.is_participant_approved(participant)
        assert work_package.get_users_to_approve(dpr.user) == []
        self.assert_participants_with_approval(
            work_package,
            dpr.user,
            [
                ["investigator", True, True],
                ["data_provider_representative", True, True],
                ["referee", True, True],
                ["researcher", True, True],
            ],
        )

    def test_participant_not_approved_for_high_tier_work_package(
        self, classified_work_package, user1, programme_manager
    ):
        work_package = classified_work_package(3)
        participant = work_package.project.add_user(
            user1, ProjectRole.RESEARCHER.value, programme_manager
        )
        dpr = work_package.project.get_participant(
            ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value
        )
        work_package.add_user(user1, programme_manager)
        assert not work_package.is_participant_approved(participant)
        assert work_package.get_users_to_approve(dpr.user) == [participant.user]
        self.assert_participants_with_approval(
            work_package,
            dpr.user,
            [
                ["investigator", True, True],
                ["data_provider_representative", True, True],
                ["referee", True, True],
                ["researcher", False, False],
            ],
        )

    def test_participant_approved_by_dpr(self, classified_work_package):
        work_package = classified_work_package(3)
        referee = work_package.project.get_participant(ProjectRole.REFEREE.value)
        dpr = work_package.project.get_participant(
            ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value
        )
        p = referee.get_work_package_participant(work_package)
        p.approve(dpr.user)
        assert work_package.is_participant_approved(referee)
        assert work_package.get_users_to_approve(dpr.user) == []
        self.assert_participants_with_approval(
            work_package,
            dpr.user,
            [
                ["investigator", True, True],
                ["data_provider_representative", True, True],
                ["referee", True, True],
            ],
        )

    def test_participant_not_approved_by_multiple_dprs(
        self, classified_work_package, user1, programme_manager
    ):
        work_package = classified_work_package(3)
        referee = work_package.project.get_participant(ProjectRole.REFEREE.value)
        dpr = work_package.project.get_participant(
            ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value
        )
        p = referee.get_work_package_participant(work_package)
        p.approve(dpr.user)

        dataset = recipes.dataset.make()
        dpr2 = work_package.project.add_user(
            user=user1,
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
            created_by=programme_manager,
        )
        work_package.add_user(user1, programme_manager)
        work_package.project.add_dataset(dataset, dpr2.user, programme_manager)
        work_package.add_dataset(dataset, programme_manager)

        assert not work_package.is_participant_approved(referee)
        assert work_package.get_users_to_approve(dpr.user) == []
        assert work_package.get_users_to_approve(dpr2.user) == [referee.user]
        self.assert_participants_with_approval(
            work_package,
            dpr.user,
            [
                ["investigator", True, True],
                ["data_provider_representative", True, True],
                ["referee", False, True],
                ["data_provider_representative", True, True],
            ],
        )
        self.assert_participants_with_approval(
            work_package,
            dpr2.user,
            [
                ["investigator", True, True],
                ["data_provider_representative", True, True],
                ["referee", False, False],
                ["data_provider_representative", True, True],
            ],
        )

    def test_participant_approved_by_multiple_dprs(
        self, classified_work_package, user1, programme_manager
    ):
        work_package = classified_work_package(3)
        referee = work_package.project.get_participant(ProjectRole.REFEREE.value)
        dpr = work_package.project.get_participant(
            ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value
        )
        p = referee.get_work_package_participant(work_package)
        p.approve(dpr.user)

        dataset = recipes.dataset.make()
        dpr2 = work_package.project.add_user(
            user=user1,
            role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value,
            created_by=programme_manager,
        )
        work_package.add_user(user1, programme_manager)
        work_package.project.add_dataset(dataset, dpr2.user, programme_manager)
        work_package.add_dataset(dataset, programme_manager)
        p = referee.get_work_package_participant(work_package)
        p.approve(dpr2.user)

        assert work_package.is_participant_approved(referee)
        assert work_package.get_users_to_approve(dpr.user) == []
        assert work_package.get_users_to_approve(dpr2.user) == []
        self.assert_participants_with_approval(
            work_package,
            dpr.user,
            [
                ["investigator", True, True],
                ["data_provider_representative", True, True],
                ["referee", True, True],
                ["data_provider_representative", True, True],
            ],
        )
        self.assert_participants_with_approval(
            work_package,
            dpr2.user,
            [
                ["investigator", True, True],
                ["data_provider_representative", True, True],
                ["referee", True, True],
                ["data_provider_representative", True, True],
            ],
        )

    def test_participant_approved_for_multiple_datasets(
        self, classified_work_package, user1, programme_manager
    ):
        work_package = classified_work_package(3)
        referee = work_package.project.get_participant(ProjectRole.REFEREE.value)
        dpr = work_package.project.get_participant(
            ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value
        )

        dataset = recipes.dataset.make()
        work_package.project.add_dataset(dataset, dpr.user, programme_manager)
        work_package.add_dataset(dataset, programme_manager)

        p = referee.get_work_package_participant(work_package)
        p.approve(dpr.user)

        assert work_package.is_participant_approved(referee)
        assert work_package.get_users_to_approve(dpr.user) == []
        self.assert_participants_with_approval(
            work_package,
            dpr.user,
            [
                ["investigator", True, True],
                ["data_provider_representative", True, True],
                ["referee", True, True],
            ],
        )

    def test_participant_not_approved_added_dataset(
        self, classified_work_package, user1, programme_manager
    ):
        work_package = classified_work_package(3)
        referee = work_package.project.get_participant(ProjectRole.REFEREE.value)
        dpr = work_package.project.get_participant(
            ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value
        )

        p = referee.get_work_package_participant(work_package)
        p.approve(dpr.user)

        assert work_package.is_participant_approved(referee)
        assert work_package.get_users_to_approve(dpr.user) == []
        self.assert_participants_with_approval(
            work_package,
            dpr.user,
            [
                ["investigator", True, True],
                ["data_provider_representative", True, True],
                ["referee", True, True],
            ],
        )

        dataset = recipes.dataset.make()
        work_package.project.add_dataset(dataset, dpr.user, programme_manager)
        work_package.add_dataset(dataset, programme_manager)

        assert not work_package.is_participant_approved(referee)
        assert work_package.get_users_to_approve(dpr.user) == [referee.user]
        self.assert_participants_with_approval(
            work_package,
            dpr.user,
            [
                ["investigator", True, True],
                ["data_provider_representative", True, True],
                ["referee", False, False],
            ],
        )


class TestUtils:
    def test_a_or_an(self):
        assert a_or_an("Investigator") == "An Investigator"
        assert a_or_an("investigator") == "An investigator"
        assert (
            a_or_an("Data Provider Representative") == "A Data Provider Representative"
        )
        assert a_or_an("Referee", capitalize=True) == "A Referee"
        assert a_or_an("referee", capitalize=False) == "a referee"
        assert a_or_an("Referee", capitalize=False) == "a Referee"
