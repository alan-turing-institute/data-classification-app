from crispy_forms.helper import FormHelper


class InlineFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_tag = False
        self.template = 'includes/table_inline_formset.html'
