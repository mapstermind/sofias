from django.conf import settings


def brand(request):
    """`brand`: the product's name, logo and meaning."""
    return {"brand": settings.BRAND}
