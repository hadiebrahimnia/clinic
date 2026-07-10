document.addEventListener('DOMContentLoaded', function () {
    window.showImageModal = function(imageSrc, title = '') {
        const modal = document.getElementById('alertModal');
        if (!modal) return;

        const modalTitle = document.getElementById('modalTitle');
        const modalIcon = document.getElementById('modalIcon');
        const modalMessage = document.getElementById('modalMessage');
        const actionBtn = document.getElementById('modalActionBtn');

        // تنظیمات مدال برای تصویر
        modalTitle.textContent = title || 'تصویر';
        modalTitle.className = 'text-primary mb-4 fw-semibold';
        
        modalIcon.style.display = 'none';        

        modalMessage.innerHTML = `
            <img src="${imageSrc}" 
                 class="img-fluid rounded my-3 shadow" 
                 style="max-height: 70vh; width: auto;"
                 alt="${title}">
        `;

        actionBtn.textContent = 'بستن';
        actionBtn.className = 'btn btn-secondary pd-x-25 px-4';

        // نمایش مدال
        const bsModal = new bootstrap.Modal(modal, {
            backdrop: true,
            keyboard: true
        });
        bsModal.show();
    };
});