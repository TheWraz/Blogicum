from django import forms
from django.contrib.auth import get_user_model

from .models import Comment, Post


User = get_user_model()


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ('author',)
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
            'birthday': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            )
        }
        input_formats = ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y']



class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')