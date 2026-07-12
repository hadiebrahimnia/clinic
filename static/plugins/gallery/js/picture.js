document.addEventListener('DOMContentLoaded', function () {
    window.showImageModal = function(imageSrc, title = '') {
        const modal = document.getElementById('alertModal');
        if (!modal) return;
        const modalTitle = document.getElementById('modalTitle');
        const modalIcon = document.getElementById('modalIcon');
        const modalMessage = document.getElementById('modalMessage');
        const actionBtn = document.getElementById('modalActionBtn');
        // === تنظیمات مخصوص مدال تصویر ===
        modalTitle.textContent = title || 'تصویر';
        modalTitle.className = 'text-dark mb-4 fw-semibold';
        // مخفی کردن آیکون فقط برای این مدال
        const originalIconDisplay = modalIcon.style.display; // ذخیره حالت قبلی
        const actionBtnIconDisplay = actionBtn.style.display; // ذخیره حالت قبلی
        modalIcon.style.setProperty('display', 'none', 'important');
        actionBtn.style.setProperty('display', 'none', 'important');

        modalMessage.innerHTML = `
            <img src="${imageSrc}"
                 class="img-fluid rounded my-3 shadow"
                 style="max-height: 70vh; width: auto;"
                 alt="${title || 'تصویر'}">
        `;

        // نمایش مدال
        const bsModal = new bootstrap.Modal(modal, {
            backdrop: true,
            keyboard: true
        });

        // وقتی مدال بسته شد، آیکون رو به حالت قبلی برگردون
        modal.addEventListener('hidden.bs.modal', function handler() {
            modalIcon.style.setProperty('display', originalIconDisplay || '', 'important');
            actionBtn.style.setProperty('display', actionBtnIconDisplay || '', 'important');
            modal.removeEventListener('hidden.bs.modal', handler); // پاک کردن listener
        }, { once: true });

        bsModal.show();
    };
});