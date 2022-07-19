from django.conf import settings
from django.core.paginator import Paginator

POSTS_LMT = settings.POSTS_ON_PAGE_LMT


def paginate_me(request, list_to_page):
    paginator = Paginator(list_to_page, POSTS_LMT)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)