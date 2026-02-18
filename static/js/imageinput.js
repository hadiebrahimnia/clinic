function previewImage(input) {
    const allowedFormats = (input.dataset.allowedFormats || 'jpg,jpeg,png').split(',');
    const maxSizeMB = parseFloat(input.dataset.maxSize || '2');
    const minWidth = parseInt(input.dataset.minWidth || '0');
    const minHeight = parseInt(input.dataset.minHeight || '0');
    const maxWidth = parseInt(input.dataset.maxWidth || '9999');
    const maxHeight = parseInt(input.dataset.maxHeight || '9999');

    const preview = document.getElementById(`preview-${input.id}`);
    const selectBtn = document.getElementById(`select-btn-${input.id}`);
    const removeBtn = document.getElementById(`remove-btn-${input.id}`);
    const widget = input.closest('.form-control');

    // حذف خطاهای قدیمی
    const oldError = widget.querySelector('.upload-error');
    if (oldError) oldError.remove();

    if (input.files && input.files[0]) {
        const file = input.files[0];
        const fileExt = file.name.split('.').pop().toLowerCase();
        const fileSizeMB = file.size / 1024 / 1024;

        if (!allowedFormats.includes(fileExt)) {
            return showUploadError(widget, `فرمت مجاز نیست! (${allowedFormats.join(', ')})`);
        }
        if (fileSizeMB > maxSizeMB) {
            return showUploadError(widget, `حجم نباید بیش از ${maxSizeMB} مگابایت باشد.`);
        }

        // بررسی ابعاد
        const img = new Image();
        img.onload = function() {
            if (img.width < minWidth || img.height < minHeight) {
                return showUploadError(widget, `حداقل ابعاد باید ${minWidth}×${minHeight}px باشد.`);
            }
            if (img.width > maxWidth || img.height > maxHeight) {
                return showUploadError(widget, `حداکثر ابعاد مجاز ${maxWidth}×${maxHeight}px است.`);
            }

            preview.src = img.src;
            preview.classList.remove('d-none');
            selectBtn.classList.add('d-none');
            removeBtn.classList.remove('d-none');
        };
        const reader = new FileReader();
        reader.onload = e => { img.src = e.target.result; };
        reader.readAsDataURL(file);
    }
}

function clearImageSelection(inputId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(`preview-${inputId}`);
    const selectBtn = document.getElementById(`select-btn-${inputId}`);
    const removeBtn = document.getElementById(`remove-btn-${inputId}`);
    const widget = input.closest('.form-control');

    input.value = '';
    preview.src = '#';
    preview.classList.add('d-none');
    selectBtn.classList.remove('d-none');
    removeBtn.classList.add('d-none');

    const oldError = widget.querySelector('.upload-error');
    if (oldError) oldError.remove();
}

function showUploadError(widget, message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'upload-error text-danger small mt-2';
    errorDiv.innerHTML = `<i class="fas fa-exclamation-circle me-1"></i> ${message}`;
    widget.appendChild(errorDiv);
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('input[type="file"][accept^="image"]').forEach(input => {
        input.addEventListener('change', () => previewImage(input));
    });
});
