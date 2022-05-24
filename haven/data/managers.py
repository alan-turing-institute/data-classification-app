from collections import defaultdict

from django.db import models


class ClassificationQuestionQuerySet(models.QuerySet):
    def get_starting_question(self, question_set=1):
        return self.get_ordered_questions(question_set=question_set)[0]

    def get_ordered_questions(self, question_set=1):
        """
        Return the classification questions, ordered in such a way
        that earlier questions do not have any dependency on earlier
        questions.

        This method will fail if there are any cycles in the
        classification questions.
        """
        incoming = defaultdict(list)
        ordered = []
        for q in self.filter(hidden=False, question_set=question_set):
            incoming.setdefault(q, [])
            if q.yes_question:
                incoming[q.yes_question].append(q)
            if q.no_question:
                incoming[q.no_question].append(q)
        for q, incoming_questions in incoming.items():
            if not incoming_questions:
                ordered.append(q)
        i = 0
        while i < len(ordered):
            q = ordered[i]
            incoming.pop(q)
            for other_q in [q.yes_question, q.no_question]:
                if other_q:
                    incoming[other_q].remove(q)
                    if not incoming[other_q]:
                        ordered.append(other_q)
            i += 1

        assert not incoming
        return ordered
