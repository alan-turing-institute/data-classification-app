from operator import attrgetter

import bleach
import django_tables2 as tables
from django.utils.html import format_html
from django_bleach.utils import get_bleach_default_options


class ParticipantTable(tables.Table):
    username = tables.Column('Username', accessor='user.display_name')
    role = tables.Column('Role', accessor='role')

    class Meta:
        orderable = False
        empty_text = 'No participants to display'


class WorkPackageTable(tables.Table):
    name = tables.Column('Name', linkify=True)
    tier = tables.Column('Tier')

    class Meta:
        orderable = False
        empty_text = 'No work packages to display'


class DatasetTable(tables.Table):
    name = tables.Column('Name')

    class Meta:
        orderable = False
        empty_text = 'No datasets to display'


class HistoryTable(tables.Table):
    datetime = tables.Column('Timestamp')
    event_type = tables.Column('Type')
    user = tables.Column('User')
    object_repr = tables.Column('Subject')
    object_json_repr = tables.Column('Details')
    changed_fields = tables.Column('Changes')

    class Meta:
        orderable = False


class PolicyTable(tables.Table):
    group = tables.Column('Policy', accessor='policy.group.description')
    policy = tables.Column('Description', accessor='policy.description')

    class Meta:
        orderable = False


class ClassificationOpinionQuestionTable(tables.Table):
    question = tables.Column('Question')

    class Meta:
        orderable = False

    def __init__(self, classifications, *args, **kwargs):
        all_questions = self._get_all_questions(classifications)
        columns = []
        unique_questions = {}

        for questions in all_questions:
            column_name, column = self._create_column(questions[0].opinion)
            columns.append((column_name, column))
            self._populate_column_data(column_name, questions, unique_questions)

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
        for classification in sorted(classifications, key=attrgetter('created_at')):
            q = list(classification.questions.all())
            if q:
                all_questions.append(q)
        return all_questions

    @staticmethod
    def _create_column(classification):
        column_name = 'user_{}'.format(classification.user.id)
        column = tables.BooleanColumn(
            verbose_name=classification.user.username,
            null=True,
            # This maybe doesn't belong in the footer, but it can't be data because it's
            # not a boolean
            footer='Tier {}'.format(classification.tier)
        )
        return (column_name, column)

    @staticmethod
    def _populate_column_data(column_name, questions, unique_questions):
        for question in questions:
            key = question.question_at_time.question
            row = unique_questions.setdefault(key, {
                'question': key,
            })
            row[column_name] = question.answer

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
            for question in sorted(questions, key=attrgetter('order')):
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
        kwargs = dict(get_bleach_default_options())
        value = bleach.clean(value, **kwargs)

        # We don't want any of the links to be displayed, so we'll strip them out entirely
        kwargs['tags'] = [t for t in kwargs['tags'] if t != 'a']
        kwargs['strip'] = True
        value = bleach.clean(value, **kwargs)
        value = format_html(value)
        return value
