from django.shortcuts import render


def handler404(request, exception, template_name="404.html"):
    """404 error handler"""
    return render(request, template_name, status=404)


def handler500(request):
    """500 error handler"""
    return render(request, "500.html", status=500)
