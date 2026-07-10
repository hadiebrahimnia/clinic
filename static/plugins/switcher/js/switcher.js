
$(document).ready(function () {
    let currentAction = null; // { type: 'toggle' | 'delete', data: {...} }

    // ==================== GENERIC MODAL HANDLER ====================
    function showConfirmModal(options) {
        const {
            type,     
            appLabel,
            modelName,
            objectId,
            fieldName = "is_active",
            displayTitle = "این آیتم",
            customConfirmText = "",
            isCurrentlyActive = false,
            $checkbox = null   // ← جدید: المان دقیق
        } = options;

        currentAction = {
            type,
            appLabel,
            modelName,
            objectId,
            fieldName,
            displayTitle,
            checkbox: $checkbox   // استفاده از المان دقیق به جای re-select
        };

        const isActivating = type === 'toggle' ? !isCurrentlyActive : true;
        const actionText = type === 'delete' ? "حذف" : (isActivating ? "فعال" : "غیرفعال");
        const actionColor = type === 'delete' || !isActivating ? "danger" : "success";

        // تنظیم عنوان مدال
        $("#modalTitle")
            .removeClass("text-success text-danger")
            .addClass(`text-${actionColor}`)
            .html(`آیا از ${actionText} کردن ${displayTitle} اطمینان دارید؟`);

        // تنظیم پیام
        $("#modalMessage").text(
            customConfirmText || 
            (type === 'delete' 
                ? `این ${displayTitle} به صورت نرم حذف خواهد شد.` 
                : `این ${displayTitle} ${actionText} خواهد شد.`)
        );

        // تنظیم دکمه
        $("#modalActionBtn")
            .text(`بله، ${actionText} شود`)
            .removeClass("btn-success btn-danger")
            .addClass(`btn-${actionColor}`);

        // تنظیم آیکون
        $("#modalIcon").attr("class", 
            type === 'delete' || !isActivating
                ? "icon icon-close fs-70 text-danger lh-1 my-4 d-inline-block"
                : "icon icon-check fs-70 text-success lh-1 my-4 d-inline-block"
        );

        new bootstrap.Modal(document.getElementById("alertModal")).show();
    }

    function closeModal() {
        const modal = bootstrap.Modal.getInstance(document.getElementById("alertModal"));
        if (modal) modal.hide();
        currentAction = null;
    }

    // ==================== AJAX PERFORMER ====================
    function performAction() {
        if (!currentAction) return;

        const { type, appLabel, modelName, objectId, fieldName, displayTitle, checkbox } = currentAction;

        $.ajax({
            headers: { "X-CSRFToken": getCookie("csrftoken") },
            url: `/boolean/${appLabel}/${modelName}/${fieldName}/${objectId}/`,
            type: "POST",
            data: {
                display_title: displayTitle,
                csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val()
            },

            success: function (response) {
                if (response.success) {
                    if (type === 'toggle' && checkbox) {
                        const newValue = response.new_value;
                        
                        checkbox.prop("checked", newValue); // حتی اگر button باشد
                        
                        if (newValue) {
                            checkbox.addClass('active');
                            checkbox.closest('tr').addClass('active'); // فقط tr فعلی
                        } else {
                            checkbox.removeClass('active');
                            checkbox.closest('tr').removeClass('active');
                        }
                    }
                    else if (type === 'delete') {
                        const $row = $(`tr[data-id="${objectId}"]`);
                        $row.fadeOut(400, () => $row.remove());
                    }

                    Growl.success({
                        title: "موفقیت",
                        message: response.message || `${displayTitle} با موفقیت ${type === 'delete' ? 'حذف' : 'به‌روزرسانی'} شد.`,
                        duration: 3000,
                        style: "success1"
                    });
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

                // برگرداندن وضعیت در صورت خطا (فقط toggle)
                if (type === 'toggle' && checkbox) {
                    checkbox.toggleClass('active'); // یا منطق دقیق‌تر
                }
            },

            complete: function () {
                closeModal();
            }
        });
    }

    // ==================== EVENT HANDLERS ====================

    // کلیک روی سوئیچ وضعیت
    $(document).on("click", ".status-switch", function (e) {
        e.preventDefault();
        e.stopImmediatePropagation();
        
        const $this = $(this);
        const isCurrentlyActive = $this.hasClass('active');

        showConfirmModal({
            type: 'toggle',
            appLabel: $this.data("app"),
            modelName: $this.data("model"),
            objectId: $this.data("id"),
            fieldName: $this.data("field") || "is_active",
            displayTitle: $this.data("title") || "آیتم",
            customConfirmText: $this.data("confirm") || "",
            isCurrentlyActive,
            $checkbox: $this   // ← المان دقیق را پاس بده
        });
    });

    // کلیک روی دکمه حذف
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
            displayTitle: $this.data("title") || "متخصص",
            customConfirmText: $this.data("confirm") || ""
        });
    });

    // کلیک روی دکمه تأیید مدال
    $(document).on("click", "#modalActionBtn", performAction);
});


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
