$(document).ready(function () {
    let currentAction = null;

    // ==================== نمایش مدال تأیید ====================
    function showConfirmModal(options) {
        const {
            type = 'toggle',
            appLabel,
            modelName,
            objectId,
            fieldName,
            displayTitle = "این آیتم",
            customConfirmText = "",
            isCurrentlyActive = false,
            $element = null,
            reloadOnSuccess = false
        } = options;

        currentAction = {
            type,
            appLabel,
            modelName,
            objectId,
            fieldName,
            displayTitle,
            $element,
            reloadOnSuccess
        };

        const isActivating = type === 'toggle' ? !isCurrentlyActive : true;
        const actionText = type === 'delete' ? "حذف" : (isActivating ? "فعال" : "غیرفعال");
        const actionColor = type === 'delete' || !isActivating ? "danger" : "success";

        $("#modalTitle")
            .removeClass("text-success text-danger")
            .addClass(`text-${actionColor}`)
            .html(`آیا از ${actionText} کردن ${displayTitle} اطمینان دارید؟`);

        $("#modalMessage").text(
            customConfirmText || 
            (type === 'delete' 
                ? `این ${displayTitle} به صورت نرم حذف خواهد شد.` 
                : `این ${displayTitle} ${actionText} خواهد شد.`)
        );

        $("#modalActionBtn")
            .text(`بله، ${actionText} شود`)
            .removeClass("btn-success btn-danger")
            .addClass(`btn-${actionColor}`);

        $("#modalIcon").attr("class", 
            type === 'delete' || !isActivating
                ? "icon icon-close fs-70 text-danger lh-1 my-4 d-inline-block"
                : "icon icon-check fs-70 text-success lh-1 my-4 d-inline-block"
        );

        new bootstrap.Modal(document.getElementById("alertModal")).show();
    }

    // ==================== انجام عملیات AJAX ====================
    function performAction() {
        if (!currentAction) return;

        const { type, appLabel, modelName, objectId, fieldName, displayTitle, $element,reloadOnSuccess } = currentAction;

        $.ajax({
            headers: { "X-CSRFToken": getCookie("csrftoken") },
            url: `/boolean/${appLabel}/${modelName}/${fieldName}/${objectId}/`,
            type: "POST",
            data: {
                csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val()
            },

            success: function (response) {
                if (response.success) {
                    const newValue = response.new_value;

                    if (type === 'toggle' && $element) {
                        if ($element.hasClass('status-switch') || $element.hasClass('toggle')) {
                            $element.toggleClass('active', newValue);
                        } else if ($element.is('input[type="checkbox"]')) {
                            $element.prop("checked", newValue);
                        }

                        $element.closest('tr').toggleClass('active', newValue);
                    }
                    else if (type === 'delete') {
                        const $row = $(`tr[data-id="${objectId}"]`);
                        $row.fadeOut(400, () => $row.remove());
                    }

                    Growl.success({
                        title: "موفقیت",
                        message: response.message || `${displayTitle} با موفقیت تغییر یافت.`,
                        duration: 3000,
                        style: "success1"
                    });
                    if (reloadOnSuccess) {
                        setTimeout(function () {
                            location.reload();
                        }, 500); // یا 1000 برای اینکه پیام Growl کمی دیده شود
                    }
                } else {
                    Growl.error({
                        title: "خطا",
                        message: response.message,
                        duration: 4000,
                        style: "error1"
                    });
                }
            },

            error: function () {
                Growl.error({
                    title: "خطا",
                    message: "خطا در ارتباط با سرور",
                    duration: 4000,
                    style: "error1"
                });

                // برگرداندن وضعیت در صورت خطا
                if ($element && (type === 'toggle')) {
                    $element.toggleClass('active');
                }
            },

            complete: function () {
                const modal = bootstrap.Modal.getInstance(document.getElementById("alertModal"));
                if (modal) modal.hide();
                currentAction = null;
            }
        });
    }

    // ==================== EVENT HANDLERS ====================

    // کلیک روی همه سوئیچ‌ها (display_config + boolean fields)
    $(document).on("click", ".status-switch, .boolean-toggle", function (e) {
        e.preventDefault();
        e.stopImmediatePropagation();

        const $this = $(this);
        const isCurrentlyActive = $this.hasClass('active');

        showConfirmModal({
            type: 'toggle',
            appLabel: $this.data("app"),
            modelName: $this.data("model"),
            objectId: $this.data("id"),
            fieldName: $this.data("field"),
            displayTitle: $this.data("title") || "آیتم",
            customConfirmText: $this.data("confirm") || "",
            isCurrentlyActive,
            $element: $this,
            reloadOnSuccess: $this.hasClass("reload-on-success")
        });
    });

    // کلیک روی دکمه حذف (در صورت نیاز)
    $(document).on("click", ".delete", function (e) {
        e.preventDefault();
        e.stopImmediatePropagation();

        const $this = $(this);

        showConfirmModal({
            type: 'delete',
            appLabel: $this.data("app"),
            modelName: $this.data("model"),
            objectId: $this.data("id"),
            fieldName: $this.data("field") || "is_deleted",
            displayTitle: $this.data("title") || "آیتم",
            customConfirmText: $this.data("confirm") || "",
            reloadOnSuccess: $this.hasClass("reload-on-success")
        });
    });

    $(document).on("click", "#modalActionBtn", performAction);
});

// تابع CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}