# management_helpers.py
from django.utils.safestring import mark_safe
from django.template import Template, Context
from django.db.models import Q
import math

# ====================== جستجو ======================
def apply_search(queryset, request, search_fields):
    query = request.GET.get('q', '').strip()
    if not query or not search_fields:
        return queryset, query

    if hasattr(queryset, 'filter'):
        q_objects = Q()
        for field in search_fields:
            q_objects |= Q(**{f"{field}__icontains": query})
        queryset = queryset.filter(q_objects)
    return queryset, query


def render_search_form(query=''):
    return f"""
        <div class="card mb-4">
            <div class="card-header d-flex">
                <div class="card-title">جستجو</div>
                <a href="javascript:void(0)" onclick="clearSearch()" class="btn btn-outline-danger border-0 mr-auto p-1">
                    <i class="fa fa-trash-o"></i> پاک کردن
                </a>
            </div>
            <div class="card-body">
                <form method="get" class="d-flex align-items-center gap-3">
                    <div class="flex-grow-1">
                        <div class="input-group">
                            <input type="text" name="q" value="{query}" 
                                   placeholder="جستجو کنید..." 
                                   class="form-control form-control-lg">
                            <span class="input-group-text"><i class="fe fe-search"></i></span>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    """



# ====================== فیلتر ======================
def apply_filters(queryset, request, filter_fields):
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

def render_filter_form(filter_fields, request):
    if not filter_fields:
        return ""

    html = '''
    <div class="card mb-4">
        <div class="card-header d-flex">
            <div class="card-title">فیلترها</div>
            <a href="javascript:void(0)" onclick="clearFilters()" 
               class="btn btn-outline-danger border-0 mr-auto p-1">
                <i class="fa fa-trash-o"></i> پاک کردن
            </a>
        </div>
        <div class="card-body">
            <form method="get" id="filter-form">
    '''

    for field_name, config in filter_fields.items():
        label = config.get('label', field_name)
        field_type = config.get('type', 'text')
        current_value = request.GET.get(field_name, '')

        html += f'<div class="form-group mb-3"><label>{label}</label>'

        if field_type == 'boolean' or field_type == 'select':
            choices = config.get('choices', [('', 'همه'), ('True', 'بله'), ('False', 'خیر')])
            html += f'<select name="{field_name}" class="form-control form-select">'
            for val, txt in choices:
                selected = 'selected' if str(val) == current_value else ''
                html += f'<option value="{val}" {selected}>{txt}</option>'
            html += '</select>'
        else:
            html += f'''
                <input type="text" name="{field_name}" value="{current_value}" 
                       class="form-control" placeholder="{label}...">
            '''

        html += '</div>'

    html += '''
                <button type="submit" class="btn btn-primary mt-3">اعمال فیلتر</button>
            </form>
        </div>
    </div>
    '''
    return mark_safe(html)


# ====================== صفحه‌بندی ======================
def apply_pagination(queryset, request, per_page=15):
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', per_page))

    if hasattr(queryset, 'count'):
        total = queryset.count()
    else:
        total = len(queryset)

    total_pages = math.ceil(total / per_page) or 1
    page = max(1, min(page, total_pages))

    start = (page - 1) * per_page
    items = queryset[start:start + per_page] if hasattr(queryset, '__getitem__') else list(queryset)[start:start + per_page]

    return items, page, total_pages, total, per_page


# ====================== صفحه‌بندی ======================
def render_pagination(current_page, total_pages, extra_params=""):
    if total_pages <= 1:
        return ""

    html = '<div class="text-center mt-4"><ul class="pagination justify-content-center">'

    # صفحه قبلی
    if current_page > 1:
        html += f'<li class="page-item"><a class="page-link" href="?page={current_page-1}{extra_params}">قبلی</a></li>'

    for p in range(max(1, current_page-3), min(total_pages+1, current_page+4)):
        if p == current_page:
            html += f'<li class="page-item active"><span class="page-link">{p}</span></li>'
        else:
            html += f'<li class="page-item"><a class="page-link" href="?page={p}{extra_params}">{p}</a></li>'

    # صفحه بعدی
    if current_page < total_pages:
        html += f'<li class="page-item"><a class="page-link" href="?page={current_page+1}{extra_params}">بعدی</a></li>'

    html += '</ul></div>'
    return mark_safe(html)





# ====================== جدول عمومی (همان قبلی) ======================
def render_generic_table(
        queryset, 
        columns, 
        table_title="لیست", 
        actions=None,
        header_actions=None,
        model_name="", 
        extra_context=None,
        search_form="", 
        filter_form="", 
        pagination="",
        breadcrumb=None):
    
    if extra_context is None:
        extra_context = {}

    if header_actions is None:
        header_actions = []

    has_sidebar = bool(search_form.strip() or filter_form.strip())

    header_actions_html = ""
    for action in header_actions:
        if action["type"] == "create":
            header_actions_html += f"""
                <a href="{action['url']}"
                class="{action.get('class', 'btn btn-primary')} mr-2 py-0">
                    <i class="{action.get('icon', 'fe fe-plus')}"></i>
                    {action.get('title', 'افزودن')}
                </a>
            """

    # thead
    thead_parts = [f'<th style="width: {col.get("width", "auto")}">{col["title"]}</th>' for col in columns]
    if actions:
        thead_parts.append('<th style="width: 100px;">اقدامات</th>')
    thead = "".join(thead_parts)

    # tbody
    tbody = ""
    for obj in queryset:
        row = "<tr>"
        
        for col in columns:
            value = obj
            for part in col['field'].split('__'):
                value = getattr(value, part, '')

            display_config = col.get('display')
            
            if isinstance(display_config, dict) and display_config.get('type') == 'toggle':
                field_name = col['field']
                is_active = bool(value)
                title = display_config.get('title', 'تغییر وضعیت')
                if callable(title):
                    title = title(obj)

                confirm = display_config.get('confirm', 'تغییر وضعیت')
                if callable(confirm):
                    confirm = confirm(obj)

                extra_class = display_config.get('extra_class', '')
                if callable(extra_class):
                    extra_class = extra_class(obj)

                html = f'''
                    <button type="button" 
                            class="toggle toggle-sm status-switch mt-2 {'active' if is_active else ''} {extra_class}"
                            data-app="{display_config.get('app', 'accounts')}"
                            data-model="{display_config.get('model', model_name)}"
                            data-id="{getattr(obj, 'pk', getattr(obj, 'id', ''))}"
                            data-field="{field_name}"
                            data-title="{title}"
                            data-confirm="{confirm}">
                        <span class="thumb"></span>
                    </button>
                '''
                cell_value = html.strip()
            elif callable(display_config):
                cell_value = display_config(obj)
            elif isinstance(value, bool):
                cell_value = '<span class="badge bg-success">فعال</span>' if value else '<span class="badge bg-danger">غیرفعال</span>'
            else:
                cell_value = str(value) if value is not None else '—'
             
            row += f"<td>{cell_value}</td>"

        # ==================== ستون اقدامات ====================
        if actions:
            action_html = '<td class="py-0 "> <div class="card-options d-inline-flex">'
            
            for act in actions:
                pk = getattr(obj, 'pk', getattr(obj, 'id', ''))

                if act.get('type') == 'edit':
                    url = act['url'].format(pk=pk)
                    action_html += f'''
                        <a href="{url}" 
                           class="mx-3 email-icon text-success bg-success-transparent"
                           data-bs-toggle="tooltip" 
                           aria-label="ویرایش" 
                           data-bs-original-title="ویرایش">
                            <i class="fa fa-pencil-square-o"></i>
                        </a>
                    '''

                elif act.get('type') == 'delete':
                    title = act.get('title', 'حذف')
                    if callable(title):
                        title = title(obj)

                    confirm = act.get('confirm', 'حذف این مورد')
                    if callable(confirm):
                        confirm = confirm(obj)
                    
                    action_html += f'''
                        <button class="mx-3 email-icon text-danger bg-danger-transparent delete reload-on-success"
                                data-app="{act.get('app', 'accounts')}"
                                data-model="{act.get('model', model_name)}"
                                data-id="{pk}"
                                data-field="{act.get('field', 'is_deleted')}"
                                data-title="{title}"
                                data-confirm="{confirm}">
                            <i class="fe fe-trash-2"></i>
                        </button>
                    '''

                else:
                    # دکمه معمولی (جزئیات و ...)
                    url = act['url'].format(pk=pk)
                    action_html += f'<a href="{url}" class="btn btn-sm {act.get("class", "btn-primary")} me-1">{act["title"]}</a>'
            
            action_html += '</div></td>'
            row += action_html

        row += "</tr>"
        tbody += row

    # Breadcrumb + Template (باقی همان قبلی)
    if breadcrumb is None:
        breadcrumb = f"""
            <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
            <li class="breadcrumb-item"><a href="/dashboard/manager">داشبورد مدیریت</a></li>
            <li class="breadcrumb-item text-dark">{table_title}</li>
        """



    table_template = """{% load jdate %}
        <div class="main-content with-sidebar">
            <div class="side-app">
                <div class="main-container container-fluid">
                    <div class="page-header">
                        <ol class="breadcrumb">{{ breadcrumb|safe }}</ol>
                    </div>
    """

    if has_sidebar:
        table_template += """
                    <div class="row">
                        <div class="col-3">{{ search_form|safe }}{{ filter_form|safe }}</div>
                        <div class="col-9">
        """

    table_template += """
                            <div class="card">
                                <div class="card-header d-flex">
                                    <div class="card-title">{{ table_title }}</div>
                                    {{ header_actions|safe }}
                                    <div class="ms-auto">
                                        <label>نمایش
                                            <select name="per_page" class="form-select form-select fs-14 d-inline w-auto" onchange="this.form.submit()">
                                                <option value="10" {% if per_page == 10 %}selected{% endif %}>10</option>
                                                <option value="25" {% if per_page == 25 %}selected{% endif %}>25</option>
                                                <option value="50" {% if per_page == 50 %}selected{% endif %}>50</option>
                                                <option value="100" {% if per_page == 100 %}selected{% endif %}>100</option>
                                            </select>
                                        </label>
                                    </div>
                                </div>
                                <div class="card-body">
                                    <div class="table-responsive">
                                        <table id="dynamic-table" class="table table-bordered text-nowrap mb-0">
                                            <thead><tr>{{ thead }}</tr></thead>
                                            <tbody>{{ tbody }}</tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                            {{ pagination|safe }}
    """

    if has_sidebar:
        table_template += "                        </div></div>"

    table_template += """
                </div>
            </div>
        </div>
    """

    t = Template(table_template)
    ctx = Context({
        "header_actions": mark_safe(header_actions_html),
        'table_title': table_title,
        'thead': mark_safe(thead),
        'tbody': mark_safe(tbody),
        'per_page': extra_context.get('per_page', 15),
        'search_form': mark_safe(search_form),
        'filter_form': mark_safe(filter_form),
        'pagination': mark_safe(pagination),
        'breadcrumb': mark_safe(breadcrumb),
        **extra_context
    })
    return t.render(ctx)