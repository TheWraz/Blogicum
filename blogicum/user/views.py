from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login


def register(request):
    """Отображает страницу регистрации пользователей."""
    template = 'registration/registration_form.html'
    form = UserCreationForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('blog:index')
    context = {'form': form}
    return render(request, template, context)
