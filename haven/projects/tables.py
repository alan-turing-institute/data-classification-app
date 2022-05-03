from operator import attrgetter

import bleach
import django_tables2 as tables
from django.urls import reverse
from django.utils.html import format_html
from django_bleach.utils import get_bleach_default_options


def bleach_no_links(value):
    kwargs = dict(get_bleach_default_options())
    value = bleach.clean(value, **kwargs)

    kwargs["tags"] = [t for t in kwargs["tags"] if t != "a"]
    kwargs["strip"] = True
    value = bleach.clean(value, **kwargs)
    return value


class ParticipantTable(tables.Table):
    username = tables.Column(
        "Username",
        accessor="user__display_name",
        linkify=lambda table, record: table.link_username(record),
    )
    role = tables.Column("Role", accessor="role")
    created_at = tables.DateTimeColumn(verbose_name="Added", short=False)
    created_by = tables.Column(verbose_name="Added by")

    def __init__(self, *args, show_edit_links=False, **kwargs):
        super().__init__(*args, **kwargs)

        self.show_edit_links = show_edit_links

    def link_username(self, record):
        if self.show_edit_links:
            return reverse("projects:edit_participant", args=[record.project.id, record.id])
        return None


class WorkPackageParticipantTable(tables.Table):
    username = tables.Column("Username", accessor="participant__user__display_name")
    role = tables.Column("Role", accessor="participant__role")
    approved = tables.BooleanColumn()
    approved_by_you = tables.BooleanColumn()

    class Meta:
        orderable = False
        empty_text = "No participants to display"

    def __init__(self, *args, work_package=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.work_package = work_package
        self.user = user

    def before_render(self, request):
        if self.work_package is None:
            self.columns.hide("approved")
            self.columns.hide("approved_by_you")
        elif self.user is None:
            self.columns.hide("approved_by_you")
        else:
            perms = self.user.project_permissions(self.work_package.project)
            if not perms.can_approve_participants:
                self.columns.hide("approved_by_you")


class WorkPackageTable(tables.Table):
    name = tables.Column("Name", linkify=True)
    status = tables.Column("Classification Status")
    tier = tables.Column("Tier")
    created_at = tables.DateTimeColumn(verbose_name="Created", short=False)

    class Meta:
        orderable = False
        empty_text = "No work packages to display"


class ProjectDatasetTable(tables.Table):
    name = tables.Column("Name", accessor="dataset__name", linkify=True)
    unique_id = tables.Column(
        "Unique ID",
        accessor="dataset__unique_id",
    )
    representative = tables.Column("Representative")
    created_at = tables.DateTimeColumn(verbose_name="Created", short=False)

    class Meta:
        orderable = False
        empty_text = "No datasets to display"


class WorkPackageDatasetTable(tables.Table):
    name = tables.Column("Name", accessor="dataset__name")
    created_at = tables.DateTimeColumn(verbose_name="Created", short=False)

    class Meta:
        orderable = False
        empty_text = "No datasets to display"


class HistoryTable(tables.Table):
    datetime = tables.Column("Timestamp")
    event_type = tables.Column("Type")
    user = tables.Column("User")
    object_repr = tables.Column("Subject")
    object_json_repr = tables.Column("Details")
    changed_fields = tables.Column("Changes")

    class Meta:
        orderable = False


class PolicyTable(tables.Table):
    group = tables.Column("Policy", accessor="policy__group__description")
    policy = tables.Column("Description", accessor="policy__description")

    class Meta:
        orderable = False


class ClassificationOpinionQuestionTable(tables.Table):
    question = tables.Column("Question", linkify=lambda record: record.get("modify_url"))

    class Meta:
        orderable = False

    def __init__(self, classifications, *args, current_user=None, **kwargs):
        all_questions = self._get_all_questions(classifications)
        columns = []
        unique_questions = {}

        for questions in all_questions:
            column_name, column = self._create_column(questions[0].opinion)
            columns.append((column_name, column))
            self._populate_column_data(column_name, questions, unique_questions, current_user)

        data = self._get_sorted_data(all_questions, unique_questions)

        super().__init__(
            data,
            extra_columns=columns,
            *args,
            **kwargs,
        )

    @staticmethod
    def _get_all_questions(classifications):
        all_questions = []
        for classification in sorted(classifications, key=attrgetter("created_at")):
            q = list(classification.questions.all())
            if q:
                all_questions.append(q)
        return all_questions

    @classmethod
    def _create_column(cls, classification):
        user = classification.created_by
        column_name = "user_{}".format(user.id)
        column = tables.BooleanColumn(
            verbose_name=user.username,
            yesno=("Yes", "No"),
            null=True,
            # This maybe doesn't belong in the footer, but it can't be data because it's
            # not a boolean
            footer="Tier {}".format(classification.tier),
        )
        return (column_name, column)

    @staticmethod
    def _populate_column_data(column_name, questions, unique_questions, current_user):
        for question in questions:
            key = question.question_at_time.question
            row = unique_questions.setdefault(
                key,
                {
                    "question": key,
                },
            )
            row[column_name] = question.answer
            if current_user == question.opinion.created_by:
                args = [
                    question.opinion.work_package.project.id,
                    question.opinion.work_package.id,
                    question.question.id,
                ]
                url = reverse("projects:classify_data", args=args)
                url += "?modify=1"
                row["modify_url"] = url

    @staticmethod
    def _get_sorted_data(all_questions, unique_questions):
        # There's no perfect way to sort the data, e.g. if user A was asked Q1 then Q2 and user
        # B was asked Q2 then Q1.
        # The code below ensures that the first user's questions are shown in order, then any
        # missing questions for the next user are inserted at the appropriate point /if possible/,
        # and at the end otherwise, and so on for all users.
        data = []
        for questions in all_questions:
            pending = []
            for question in sorted(questions, key=attrgetter("order")):
                key = question.question_at_time.question
                row = unique_questions[key]
                try:
                    i = data.index(row)
                    for p in pending:
                        data.insert(i, p)
                        i += 1
                    pending = []
                except ValueError:
                    pending.append(row)
            data.extend(pending)
        return data

    def render_question(self, value):
        value = bleach_no_links(value)
        value = format_html(value)
        return value
