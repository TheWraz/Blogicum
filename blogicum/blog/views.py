from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Count
from django.core.paginator import Paginator
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings

from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, ProfileEditForm
from .mixins import CommentSecurityMixin


def get_posts_queryset(apply_filters=False, apply_annotations=False):
    """Позволяет добавлять фильтры публикаций и количество комментариев."""
    queryset = Post.objects.select_related('category', 'author', 'location')

    if apply_filters:
        queryset = queryset.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')

    if apply_annotations:
        queryset = queryset.annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')

    return queryset


class PostListView(ListView):
    """Отображает главную страницу с постами, отсортированными по дате."""

    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'page_obj'
    paginate_by = settings.POSTS_PER_PAGE
    queryset = get_posts_queryset(
        apply_filters=True,
        apply_annotations=True
    )


class PostDetailView(DetailView):
    """Отображает детальную страницу опубликованного поста с указанным id."""

    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'

    def get_object(self):
        """Получает объект поста с проверкой прав доступа."""
        post = get_object_or_404(
            Post.objects.select_related('author', 'category', 'location'),
            pk=self.kwargs['post_id']
        )
        user = self.request.user

        if post.author != user and any([
            post.is_published is False,
            post.category.is_published is False,
            post.pub_date > timezone.now()
        ]):
            raise Http404("Пост не найден или недоступен")

        return post

    def get_context_data(self, **kwargs):
        """Добавляет в контекст комментарии с оптимизацией запроса."""
        context = super().get_context_data(**kwargs)
        context['comments'] = (
            self.object.comments
            .select_related('author')
            .order_by('created_at')
        )
        context['form'] = CommentForm()
        return context


class CategoryPostsView(ListView):
    """Отображает страницу с опубликованными постами указанной категории."""

    template_name = 'blog/category.html'
    context_object_name = 'page_obj'
    paginate_by = settings.POSTS_PER_PAGE

    def get_category(self):
        """Получает объект категории."""
        return get_object_or_404(
            Category.objects.filter(is_published=True),
            slug=self.kwargs['category_slug']
        )

    def get_queryset(self):
        """Использует универсальную функцию и фильтрует по категории."""
        return get_posts_queryset(
            apply_filters=True,
            apply_annotations=True
        ).filter(category=self.get_category())

    def get_context_data(self, **kwargs):
        """Добавляет категорию в контекст."""
        context = super().get_context_data(**kwargs)
        context['category'] = self.get_category()
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    """Отображает страницу создания постов."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        """Обрабатывает валидную форму поста."""
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """URL для перенаправления после успешного создания поста."""
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostUpdateView(LoginRequiredMixin, UpdateView):
    """Добавляет возможность редактирования постов."""
    
    model = Post
    pk_url_kwarg = 'post_id'
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        """Проверяет, что пользователь - автор поста."""
        obj = self.get_object()
        if obj.author != request.user:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        """URL для перенаправления после успешного редактирования."""
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )


class PostDeleteView(LoginRequiredMixin, DeleteView):
    """Добавляет возможность удаления поста с подтверждением."""
    
    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/detail.html'
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request, *args, **kwargs):
        """Проверяет, что пользователь - автор поста."""
        obj = self.get_object()
        if obj.author != request.user:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Добавляет комментарии в контекст."""
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Добавляет возможность комментировать посты."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/detail.html'

    def form_valid(self, form):
        """Обработка валидной формы комментария."""
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return super().form_valid(form)

    def get_success_url(self):
        """URL для перенаправления после создания комментария."""
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )


class CommentUpdateView(CommentSecurityMixin, UpdateView):
    """Добавляет возможность редактировать комментарии постов."""

    form_class = CommentForm


class CommentDeleteView(CommentSecurityMixin, DeleteView):
    """Добавляет возможность удалять комментарии постов."""

    pass


def profile_view(request, username):
    """Отображает страницу профиля пользователя."""
    template = 'blog/profile.html'
    profile = get_object_or_404(User, username=username)
    post_list = get_posts_queryset(
        apply_filters=(request.user != profile),
        apply_annotations=True
    ).filter(author=profile)
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'profile': profile, 'page_obj': page_obj}
    return render(request, template, context)


@login_required
def edit_profile(request):
    """Отображает страницу редактирования профиля пользователя."""
    template = 'blog/user.html'
    user_edit = request.user
    form = ProfileEditForm(request.POST or None, instance=user_edit)

    if form.is_valid():
        form.save()
        return redirect('blog:profile', username=user_edit.username)

    context = {'form': form, 'profile': user_edit}
    return render(request, template, context)
