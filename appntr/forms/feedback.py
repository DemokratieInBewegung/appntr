from django import forms
from django.forms import ModelForm
from appntr.models.feedback import Feedback


class FeedbackForm(ModelForm):

    class Meta:
        model = Feedback
        fields = [
            'interviewer_names',
            'feedback_type',
            'statement_yes',
            'statement_maybe',
            'statement_no',
        ]