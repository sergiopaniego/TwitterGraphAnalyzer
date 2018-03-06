from django import forms

class HashtagForm(forms.Form):
    hashtag = forms.CharField(label='hashtag', max_length=50)