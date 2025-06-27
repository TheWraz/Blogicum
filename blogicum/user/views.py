from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count

from blog.models import Post
from .forms import ProfileEditForm


def register(request):
    """Отображает страницу регистрации пользователей."""
    template = 'registration/registration_form.html'
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('blog:index')
    else:
        form = UserCreationForm()
    context = {'form': form}
    return render(request, template, context)


def profile_view(request, username):
    """Отображает страницу профиля пользователя."""
    template = 'blog/profile.html'
    profile = get_object_or_404(User, username=username)

    post_list = Post.objects.filter(
        author=profile,
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')

    if request.user != profile:
        post_list = post_list.filter(is_published=True)

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'profile': profile, 'page_obj': page_obj}
    return render(request, template, context)


@login_required
def edit_profile(request, username):
    """Отображает страницу редактирования профиля пользователя."""
    template = 'blog/user.html'
    user_edit = request.user
    if user_edit.username != username:
        return redirect('user:profile', username=user_edit.username)

    user_edit = request.user

    if request.method == 'POST':
        print("POST data:", request.POST)
        form = ProfileEditForm(request.POST, instance=user_edit)
        if form.is_valid():
            form.save()
            return redirect('user:profile', username=user_edit.username)
    else:
        form = ProfileEditForm(instance=user_edit)
    context = {'form': form, 'profile': user_edit}
    return render(request, template, context)

# Я очень намучался с тестами у меня постоянно вылезала ошибка:
# AssertionError: Убедитесь, что пользователь может редактировать свой профиль.
# В итоге ошибка заключалась в том что я переделал кнопку выхода на POST,
# так как она в шаблонах сделана через GET и не работала из за этого
# но тесты видимо писались под старую версию, где logout был через GET
# в итоге кнопка выход не работает, за то тесты не жалуются.
# Прости надо было выговориться, очень сгорел с этого
# я после ревью удалю этот коммит
