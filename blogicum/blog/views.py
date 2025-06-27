from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, reverse
from django.utils import timezone
from django.db.models import Count
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.db import models

from .models import Post, Category, Comment
from .forms import PostForm, CommentForm


class PostListView(ListView):
    """Отображает главную страницу с постами, отсортированными по дате."""

    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'page_obj'
    paginate_by = 10
    ordering = ['-pub_date']

    def get_queryset(self):
        return Post.objects.select_related(
            'category', 'author', 'location'
        ).filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        paginator = Paginator(queryset, self.paginate_by)
        page_number = self.request.GET.get('page')
        context['page_obj'] = paginator.get_page(page_number)
        return context


class PostDetailView(DetailView):
    """Отображает детальную страницу опубликованного поста с указанным id."""

    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'
    pk_url_kwarg = 'post_id'

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_authenticated:
            queryset = queryset.filter(
                models.Q(is_published=True, pub_date__lte=timezone.now(), category__is_published=True) |
                models.Q(author=user)
            )
        else:
            queryset = queryset.filter(
                is_published=True,
                pub_date__lte=timezone.now(),
                category__is_published=True
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.all().order_by('created_at')
        context['form'] = CommentForm()
        return context


class CategoryPostsView(ListView):
    """Отображает страницу с опубликованными постами указанной категории."""

    template_name = 'blog/category.html'
    context_object_name = 'page_obj'
    paginate_by = 10

    def get_queryset(self):
        self.category = get_object_or_404(
            Category.objects.filter(is_published=True),
            slug=self.kwargs['category_slug']
        )
        return Post.objects.select_related(
            'category', 'location', 'author'
        ).filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category=self.category
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    """Отображает страницу создания постов."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.pub_date = timezone.now()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'user:profile',
            kwargs={'username': self.request.user}
        )


class PostUpdateView(LoginRequiredMixin, UpdateView):
    """Добавляет возможность редактирования постов."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != self.request.user:
            return redirect('blog:post_detail', post_id=obj.id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.object.id}
        )


class PostDeleteView(LoginRequiredMixin, DeleteView):
    """Добавляет возможность удаления поста с подтверждением."""

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != self.request.user:
            return redirect('blog:post_detail', post_id=obj.id)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['confirm_delete'] = True
        context['form'] = CommentForm()
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Добавляет возможность комментировать посты."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/detail.html'

    def dispatch(self, request, *args, **kwargs):
        self.post_object = get_object_or_404(Post, pk=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.post_object
        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = self.post_object
        return context


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    """Добавляет возможность редактировать комментарии постов."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != self.request.user:
            return redirect('blog:post_detail', post_id=obj.post.id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.object.post.id}
        )


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    """Добавляет возможность удалять комментарии постов."""

    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != self.request.user:
            return redirect('blog:post_detail', post_id=obj.post.id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.object.post.id}
        )
