from django.db.models import Q
import math
from django.http import HttpResponse
from django.utils.safestring import mark_safe


# ====================== جستجو ======================
def apply_search(queryset, request, search_fields):
    """
    اعمال جستجو روی queryset یا لیست پاس داده شده
    search_fields: لیست فیلدهایی که جستجو شود
    """
    query = request.GET.get('q', '').strip()
    if not query or not search_fields:
        return queryset, query
    
    if hasattr(queryset, 'filter'):  # Django QuerySet
        q_objects = Q()
        for field in search_fields:
            q_objects |= Q(**{f"{field}__icontains": query})
        queryset = queryset.filter(q_objects)
    else:  
        # اگر لیست معمولی پاس دادی
        queryset = [item for item in queryset if any(
            query.lower() in str(getattr(item, field, '')).lower() 
            for field in search_fields
        )]
    
    return queryset, query


# ====================== فیلتر ======================
def apply_filters(queryset, request, filter_fields):
    """
    filter_fields: دیکشنری به شکل {'field_name': 'label'}
    """
    if not filter_fields:
        return queryset
    
    filters = {}
    for field in filter_fields.keys():
        value = request.GET.get(field)
        if value not in (None, ''):
            filters[field] = value
    
    if filters and hasattr(queryset, 'filter'):
        queryset = queryset.filter(**filters)
    
    return queryset


# ====================== صفحه‌بندی ======================
def apply_pagination(queryset, request, per_page=15):
    """صفحه‌بندی + برگرداندن اطلاعات صفحه"""
    page = int(request.GET.get('page', 1))
    
    if hasattr(queryset, 'count'):   # QuerySet
        total = queryset.count()
    else:                            # لیست معمولی
        total = len(queryset)
    
    total_pages = math.ceil(total / per_page) or 1
    page = max(1, min(page, total_pages))
    
    start = (page - 1) * per_page
    if hasattr(queryset, 'all'):   # QuerySet
        items = queryset[start:start + per_page]
    else:
        items = queryset[start:start + per_page]
    
    return items, page, total_pages, total


# ====================== اجزای HTML (مستقل) ======================
def render_search_form(query=''):
    return f"""
        <div class="card mb-4">
            <div class="card-header d-flex">
                <div class="card-title">جستجو</div>
                    <a href="javascript:void(0)" class=" btn btn-outline-danger border-0 mr-auto p-1">
                        <i class="fa fa-trash-o"></i>
                        <span>پاک کردن</span> 
                    </a>
            </div>
            <div class="card-body">
                <form method="get" class="d-flex align-items-center gap-3">
                    <div class="flex-grow-1">
                        <div class="input-group">
                            <input type="text" 
                                   name="q" 
                                   value="{query}"
                                   placeholder="جستجو کنید"
                                   class="form-control form-control-lg"
                                   style="font-size:16px;">
                            <span class="input-group-text">
                                <i class="fe fe-search"></i>
                            </span>
                            
                        </div>
                    </div>
                </form>
            </div>
        </div>
    """

def render_filter_form(filter_fields, request):
    if not filter_fields:
        return ""
    
    html = '''
    <div class="card">

        <div class="card-header d-flex">
            <div class="card-title">فیلترها</div>
                <a href="javascript:void(0)" class=" btn btn-outline-danger border-0 mr-auto p-1">
                    <i class="fa fa-trash-o"></i>
                    <span>پاک کردن</span> 
                </a>
            
        </div>

        <div class="card-body">
            <form method="get" id="filter-form">
    '''
    
    for field_name, config in filter_fields.items():
        if isinstance(config, str): 
            config = {'label': config, 'type': 'text'}
        
        label = config.get('label', field_name)
        field_type = config.get('type', 'text')
        current_value = request.GET.get(field_name, '')
        
        html += f'''
                <div class="form-group mb-3">
        '''
        
        if field_type == 'boolean' or field_type == 'select':
            choices = config.get('choices', [('', 'همه'), ('True', 'بله'), ('False', 'خیر')])
            html += f'<select name="{field_name}" title="{label}" class="form-control form-select" style="height: 3rem;">'
            for val, txt in choices:
                selected = 'selected' if str(val) == current_value else ''
                html += f'<option value="{val}">{txt}</option>'
            html += '</select>'
            
        elif field_type == 'date':
            html += f'''
                <input type="date" name="{field_name}" value="{current_value}" 
                       class="form-control">
            '''
            
        else: 
            html += f'''
                <input type="text" name="{field_name}" value="{current_value}" 
                       class="form-control" placeholder="جستجو در {label.lower()}...">
            '''
        
        html += '</div>'
    
    html += '''
                <div class="d-flex gap-2 mt-4">
                    <button type="submit" class="btn btn-primary">اعمال فیلتر</button>
                    
                </div>
            </form>
        </div>
    </div>
    '''
    
    return mark_safe(html)


def render_pagination(page, total_pages, extra_params=""):
    if total_pages <= 1:
        return ""
    
    html = '<div style="text-align:center; margin:30px 0; font-size:17px;">'
    for p in range(max(1, page-4), min(total_pages+1, page+5)):
        if p == page:
            html += f'<span style="font-weight:bold; color:#0066cc; margin:0 10px;">{p}</span>'
        else:
            html += f'<a href="?page={p}{extra_params}" style="margin:0 10px;">{p}</a>'
    html += '</div>'
    return html