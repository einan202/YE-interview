"""Context processors for blog app (global template variables)."""
from django.db.models import Count, Q
from django.utils.text import slugify

from .models import Catagory


def _ensure_category_slugs():
    """Ensure all categories have a slug (for topic URLs and nav links)."""
    for cat in Catagory.objects.filter(Q(slug__isnull=True) | Q(slug='')):
        if cat.name:
            cat.slug = slugify(cat.name) or f'category-{cat.id}'
            cat.save(update_fields=['slug'])


def globalVariable(request):
    """Expose top categories by post count for nav (max 4)."""
    _ensure_category_slugs()
    category = (
        Catagory.objects.all()
        .annotate(post_count=Count('blog'))
        .filter(blog__isnull=False)
        .order_by('-post_count')[:4]
    )
    return {
        'category': category,
        'cat_count': category.count(),
    }
