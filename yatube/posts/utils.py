from django.conf import settings
from django.core.paginator import Paginator

POSTS_LMT = settings.POSTS_ON_PAGE_LMT


def paginate_me(request, post_list):
    paginator = Paginator(post_list, POSTS_LMT)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def paginate_comments(request, comment_list):
    paginator = Paginator(comment_list, POSTS_LMT)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
