from django import forms

from .classification import QuestionText
from .tiers import Tier


class Tier0Form(forms.Form):
    is_public_and_open = forms.BooleanField(
        required=False,
        label=QuestionText.PUBLIC_AND_OPEN,
    )

    def clean(self):
        is_public = self.cleaned_data.get('is_public_and_open', False)
        if is_public:
            self.cleaned_data['tier'] = Tier.ZERO
        return self.cleaned_data


class Tier1Form(forms.Form):
    publishable = forms.BooleanField(
        required=False,
        label=QuestionText.PUBLISHABLE,
    )

    does_not_describe_individuals = forms.BooleanField(
        required=False,
        label=QuestionText.DOES_NOT_DESCRIBE_INDIVIDUALS,
    )

    disclosure_termination = forms.BooleanField(
        required=False,
        label=QuestionText.DISCLOSURE_TERMINATION,
    )

    disclosure_embarrassment = forms.BooleanField(
        required=False,
        label=QuestionText.DISCLOSURE_EMBARRASSMENT,
    )

    def clean(self):
        publishable = self.cleaned_data.get('is_publishable', False)
        does_not_describe_individuals = self.cleaned_data.get(
            'does_not_describe_individuals', False)
        disclosure_termination = self.cleaned_data.get('disclosure_termination', False)
        disclosure_embarrassment = self.cleaned_data.get('disclosure_embarrassment', False)
        if ((publishable and
             does_not_describe_individuals and
             not disclosure_termination and
             not disclosure_embarrassment)):
            self.cleaned_data['tier'] = Tier.ONE
        return self.cleaned_data


class Tier2Form(forms.Form):
    individuals_are_anonymous = forms.BooleanField(
        required=False,
        label=QuestionText.INDIVIDUALS_ARE_ANONYMOUS,
    )

    disclosure_penalties = forms.BooleanField(
        required=False,
        label=QuestionText.DISCLOSURE_PENALTIES,
    )

    def clean(self):
        individuals_are_anonymous = self.cleaned_data.get('individuals_are_anonymous', False)
        disclosure_penalties = self.cleaned_data.get('disclosure_penalties', False)
        if not individuals_are_anonymous and not disclosure_penalties:
            self.cleaned_data['tier'] = Tier.TWO
        return self.cleaned_data


class Tier3Form(forms.Form):
    valuable_to_enemies = forms.BooleanField(
        required=False,
        label=QuestionText.VALUABLE_TO_ENEMIES,
    )

    def clean(self):
        valuable_to_enemies = self.cleaned_data.get('valuable_to_enemies', False)
        if valuable_to_enemies:
            self.cleaned_data['tier'] = Tier.FOUR
        else:
            self.cleaned_data['tier'] = Tier.THREE
        return self.cleaned_data
