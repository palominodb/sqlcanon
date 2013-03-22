from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class LastStatementsForm(forms.Form):
    minutes = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = 'form-inline'
        self.helper.attrs['target'] = '_blank'

        self.helper.add_input(Submit('view_last_statements', 'View last statements'))
        super(LastStatementsForm, self).__init__(*args, **kwargs)


class TopQueriesForm(forms.Form):
    limit = forms.IntegerField()
    column = forms.ChoiceField(help_text='Column to initially sort by.')
    hostname = forms.ChoiceField(required=False, help_text='Select hostname to include in the result.')
    schema = forms.ChoiceField(required=False, help_text='Select schema to include in the result.')

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = 'form-inline'
        self.helper.attrs['target'] = '_blank'

        self.helper.add_input(Submit('view_top_queries', 'View top queries'))
        super(TopQueriesForm, self).__init__(*args, **kwargs)