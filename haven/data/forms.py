from django import forms


class Tier0Form(forms.Form):
    is_public_and_open = forms.BooleanField(
        required=False,
        label='Is the data public and open?',
    )

    def clean(self):
        is_public = self.cleaned_data.get('is_public_and_open', False)
        if is_public:
            self.cleaned_data['tier'] = 0
        return self.cleaned_data


class Tier1Form(forms.Form):
    publishable = forms.BooleanField(
        required=False,
        label='Is the data publishable?',
    )

    describes_individuals = forms.BooleanField(
        required=False,
        label='Does the data describe individuals?',
    )

    disclosure_termination = forms.BooleanField(
        required=False,
        label='Could disclosure result in contract termination?',
    )

    disclosure_embarrassment = forms.BooleanField(
        required=False,
        label='Could disclosure result in embarrassment?',
    )

    def clean(self):
        publishable = self.cleaned_data.get('is_publishable', False)
        describes_individuals = self.cleaned_data.get('describes_individuals', False)
        disclosure_termination = self.cleaned_data.get('disclosure_termination', False)
        disclosure_embarrassment = self.cleaned_data.get('disclosure_embarrassment', False)
        if ((publishable and
             not describes_individuals and
             not disclosure_termination and
             not disclosure_embarrassment)):
            self.cleaned_data['tier'] = 1
        return self.cleaned_data


class Tier2Form(forms.Form):
    could_be_identifiable = forms.BooleanField(
        required=False,
        label='Could individuals be identified?',
    )

    disclosure_penalties = forms.BooleanField(
        required=False,
        label='Could disclosure result in penalties?',
    )

    def clean(self):
        could_be_identifiable = self.cleaned_data.get('could_be_identiable', False)
        disclosure_penalties = self.cleaned_data.get('disclosure_penalties', False)
        if not could_be_identifiable and not disclosure_penalties:
            self.cleaned_data['tier'] = 2
        return self.cleaned_data


class Tier3Form(forms.Form):
    valuable_to_enemies = forms.BooleanField(
        required=False,
        label='Could data be valuable to enemies?'
    )

    def clean(self):
        valuable_to_enemies = self.cleaned_data.get('valuable_to_enemies', False)
        if valuable_to_enemies:
            self.cleaned_data['tier'] = 4
        else:
            self.cleaned_data['tier'] = 3
        return self.cleaned_data
