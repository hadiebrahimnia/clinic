$(document).ready(function() {

    let itemToToggle = null;

    function showToggleModal(options) {
        const {
            modelName,
            objectId,
            fieldName = 'is_active',
            displayTitle = 'این آیتم',
            customConfirmText = ''
        } = options;

        const checkbox = $(`.status-switch[data-id="${objectId}"]`);
        const wasActive = checkbox.is(':checked');

        // ←←← مهم: بلافاصله وضعیت را به قبل برمی‌گردانیم
        checkbox.prop('checked', wasActive);

        const actionText = wasActive ? 'غیرفعال' : 'فعال';
        const actionColor = wasActive ? 'danger' : 'success';

        itemToToggle = {
            modelName,
            objectId,
            fieldName,
            checkbox,
            previousState: wasActive,
            newState: !wasActive,
            displayTitle
        };

        // تنظیم مدال
        $('#modalTitle')
            .removeClass('text-success text-danger')
            .addClass(`text-${actionColor}`)
            .html(`آیا از ${actionText} کردن ${displayTitle} اطمینان دارید؟`);

        $('#modalMessage').text(
            customConfirmText || `این ${displayTitle.toLowerCase()} ${actionText} خواهد شد.`
        );

        const btn = $('#modalActionBtn');
        btn.text(`بله، ${actionText} شود`)
           .removeClass('btn-success btn-danger')
           .addClass(wasActive ? 'btn-danger' : 'btn-success');

        $('#modalIcon')
            .attr('class', wasActive 
                ? "icon icon-close fs-70 text-danger lh-1 my-4 d-inline-block" 
                : "icon icon-check fs-70 text-success lh-1 my-4 d-inline-block");

        new bootstrap.Modal(document.getElementById('alertModal')).show();
    }

    // تأیید در مدال
    window.performToggleAfterConfirm = function() {
        if (!itemToToggle) return;

        const { modelName, objectId, fieldName, checkbox, previousState, newState, displayTitle } = itemToToggle;

        $.ajax({
            url: `/boolean/${modelName}/${fieldName}/${newState}/`,
            method: 'POST',
            data: {
                object_id: objectId,
                display_title: displayTitle,
                csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.success) {
                    checkbox.prop('checked', newState);   // تغییر وضعیت فقط اینجا
                    showSwal({
                        title: 'موفقیت‌آمیز',
                        text: response.message,
                        type: 'success',
                        timer: 2000,
                        showConfirmButton: false
                    });
                } else {
                    checkbox.prop('checked', previousState);
                    showSwal({ title: 'خطا', text: response.message, type: 'error' });
                }
            },
            error: function() {
                checkbox.prop('checked', previousState);
                showSwal({ title: 'خطا', text: 'خطا در ارتباط با سرور', type: 'error' });
            }
        });

        itemToToggle = null;
    };

    // رویداد کلیک روی سوئیچ
    $(document).on('change', '.status-switch', function(e) {
        const $this = $(this);

        const model = $this.data('model');
        const id = $this.data('id');
        const field = $this.data('field') || 'is_active';
        const title = $this.data('title') || 'آیتم';
        const confirmText = $this.data('confirm') || '';

        if (model && id) {
            // جلوگیری قوی از تغییر پیش‌فرض
            e.preventDefault();
            e.stopImmediatePropagation();

            showToggleModal({
                modelName: model,
                objectId: id,
                fieldName: field,
                displayTitle: title,
                customConfirmText: confirmText
            });
        }
    });
});