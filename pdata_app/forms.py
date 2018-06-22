from __future__ import unicode_literals, division, absolute_import
from django import forms
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth.models import User

from .models import DataSubmission


class CreateSubmissionForm(forms.ModelForm):
    class Meta:
        model = DataSubmission
        fields = ('incoming_directory',)
        widgets = {'incoming_directory': forms.TextInput(attrs={
            'class': 'form-control', 'autofocus': ''})}


class PasswordChangeBootstrapForm(PasswordChangeForm):
    def __init__(self, user, *args, **kwargs):
        super(PasswordChangeBootstrapForm, self).__init__(user,*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class SetPasswordBootstrapForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super(SetPasswordBootstrapForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')


class UserBootstrapForm(UserForm):
    def __init__(self, *args, **kwargs):
        super(UserBootstrapForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
