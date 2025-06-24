from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from .models import Post, Category


POSTS_PER_PAGE = 5


def get_base_queryset():
    """Возвращает базовый кверисет для постов с общими фильтрами."""
    return Post.objects.select_related(
        'category', 'location', 'author'
    ).filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True
    )


def index(request):
    """Отображает главную страницу с постами, отсортированными по дате."""
    template = 'blog/index.html'
    post_list = get_base_queryset()[:POSTS_PER_PAGE]
    context = {'post_list': post_list}
    return render(request, template, context)


def post_detail(request, id):
    """Отображает детальную страницу опубликованного поста с указанным id."""
    template = 'blog/detail.html'
    post = get_object_or_404(get_base_queryset(), pk=id)
    context = {'post': post}
    return render(request, template, context)


def category_posts(request, category_slug):
    """Отображает страницу с опубликованными постами указанной категории."""
    template = 'blog/category.html'
    category = get_object_or_404(
        Category.objects.filter(is_published=True),
        slug=category_slug
    )
    post_list = get_base_queryset().filter(category=category)
    context = {
        'category': category,
        'post_list': post_list
    }
    return render(request, template, context)
