from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404

from .models import Comment


class CommentSecurityMixin(LoginRequiredMixin):
    """Миксин для проверки прав доступа к комментариям."""

    model = Comment
    template_name = 'blog/comment.html'

    def get_success_url(self):
        """URL для перенаправления после действий с комментарием."""
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )

    def dispatch(self, request, *args, **kwargs):
        """Проверка прав доступа перед обработкой запроса."""
        comment = self.get_object()
        if comment.author != request.user:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        """Получение комментария с проверкой принадлежности к посту."""
        return get_object_or_404(
            Comment,
            pk=self.kwargs['comment_id'],
            post_id=self.kwargs['post_id']
        )
