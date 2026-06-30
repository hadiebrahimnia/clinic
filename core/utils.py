from django.utils.safestring import mark_safe
from django.urls import reverse
from urllib.parse import urlencode  

# ====================== Helper Functions ======================

def render_pagination(page_obj, search_query='', specialty_filter=''):
    """دقیقاً همان تابعی که نوشتی"""
    if page_obj.paginator.num_pages <= 1:
        return ''

    items = []
    if page_obj.has_previous():
        items.append(_page_link(page_obj.previous_page_number(), 'قبلی', search_query, specialty_filter))

    for num in page_obj.paginator.page_range:
        if num == page_obj.number:
            items.append(f'<li class="page-item active"><span class="page-link">{num}</span></li>')
        else:
            items.append(_page_link(num, num, search_query, specialty_filter))

    if page_obj.has_next():
        items.append(_page_link(page_obj.next_page_number(), 'بعدی', search_query, specialty_filter))

    return mark_safe('<nav><ul class="pagination">' + ''.join(items) + '</ul></nav>')


def _page_link(page, text, search_query, specialty_filter):
    """تابع کمکی داخلی"""
    params = {}
    if page != 1:
        params['page'] = page
    if search_query:
        params['search'] = search_query
    if specialty_filter:
        params['specialty'] = specialty_filter

    query_string = urlencode(params)
    full_url = f"?{query_string}" if query_string else "?"

    return f'<li class="page-item"><a class="page-link" href="#" data-page-url="{full_url}">{text}</a></li>'