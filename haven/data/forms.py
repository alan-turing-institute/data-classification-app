from django import forms


class SingleQuestionForm(forms.Form):
    question = forms.BooleanField(
        required=False,
        label="",
    )

    @classmethod
    def subclass_for_question(cls, question):
        name = question.name + "SingleQuestionForm"
        attrs = {
            "question_obj": question,
            "question_label": question.question,
            "yes_tier": question.yes_tier,
            "no_tier": question.no_tier,
            "yes_question": question.yes_question.name
            if question.yes_question
            else None,
            "no_question": question.no_question.name if question.no_question else None,
        }
        return type(name, (cls,), attrs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["question"].label = self.question_label

    def clean(self):
        """
        Decide whether the answers determine the data as Tier 0
        """
        answer = self.cleaned_data.get("question", False)
        if answer:
            if self.yes_tier is not None:
                self.cleaned_data["tier"] = self.yes_tier
            elif self.yes_question is not None:
                self.cleaned_data["next_step"] = self.yes_question
        else:
            if self.no_tier is not None:
                self.cleaned_data["tier"] = self.no_tier
            elif self.no_question is not None:
                self.cleaned_data["next_step"] = self.no_question
        return self.cleaned_data
