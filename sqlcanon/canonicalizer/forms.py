from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class LastStatementsForm(forms.Form):
    minutes = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = 'form-inline'

        self.helper.add_input(Submit('view_last_statements', 'View last statements'))
        super(LastStatementsForm, self).__init__(*args, **kwargs)


class TopQueriesForm(forms.Form):
    limit = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = 'form-inline'

        self.helper.add_input(Submit('view_top_queries', 'View top queries'))
        super(TopQueriesForm, self).__init__(*args, **kwargs)