from django.shortcuts import render


def csrf_failure(request, reason=""):
    """Добавляет стилизированную страницу ошибки 403"""
    return render(request, 'pages/403csrf.html', status=403)


def page_not_found(request, exception):
    """Добавляет стилизированную страницу ошибки 404"""
    return render(request, 'pages/404.html', status=404)


def server_error(request):
    """Добавляет стилизированную страницу ошибки 500"""
    return render(request, 'pages/500.html', status=500)
