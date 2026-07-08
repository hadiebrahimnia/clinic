/**
 * ImageInput Widget - JavaScript Handler
 * نسخه بهبود یافته، تمیزتر و مقاوم‌تر
 */

class ImageInputHandler {
    constructor() {
        this.init();
    }

    init() {
        document.addEventListener('DOMContentLoaded', () => {
            document.querySelectorAll('input[type="file"][accept^="image"]').forEach(input => {
                this.attachToInput(input);
            });
        });
    }

    attachToInput(input) {
        // جلوگیری از اتصال چندباره
        if (input.dataset.imageInputInitialized) return;
        input.dataset.imageInputInitialized = 'true';

        input.addEventListener('change', () => this.previewImage(input));
    }

    previewImage(input) {
        const widget = input.closest('.form-control');
        if (!widget) return;

        this.clearOldErrors(widget);

        const file = input.files[0];
        if (!file) return;

        const config = this.getConfig(input);

        // اعتبارسنجی اولیه
        if (!this.validateFile(file, config, widget)) {
            input.value = ''; // پاک کردن فایل نامعتبر
            return;
        }

        // بررسی ابعاد تصویر
        this.validateImageDimensions(file, config, widget, (isValid) => {
            if (!isValid) {
                input.value = '';
                return;
            }

            this.showPreview(input, file, widget);
        });
    }

    getConfig(input) {
        return {
            allowedFormats: (input.dataset.allowedFormats || 'jpg,jpeg,png').split(','),
            maxSizeMB: parseFloat(input.dataset.maxSize || '2'),
            minWidth: parseInt(input.dataset.minWidth || '200'),
            minHeight: parseInt(input.dataset.minHeight || '200'),
            maxWidth: parseInt(input.dataset.maxWidth || '4000'),
            maxHeight: parseInt(input.dataset.maxHeight || '4000')
        };
    }

    validateFile(file, config, widget) {
        const fileExt = file.name.split('.').pop().toLowerCase();
        const fileSizeMB = file.size / (1024 * 1024);

        if (!config.allowedFormats.includes(fileExt)) {
            this.showError(widget, `فرمت مجاز نیست! (${config.allowedFormats.join(', ')})`);
            return false;
        }

        if (fileSizeMB > config.maxSizeMB) {
            this.showError(widget, `حجم فایل نباید بیش از ${config.maxSizeMB} مگابایت باشد.`);
            return false;
        }

        return true;
    }

    validateImageDimensions(file, config, widget, callback) {
        const img = new Image();
        
        img.onload = () => {
            if (img.width < config.minWidth || img.height < config.minHeight) {
                this.showError(widget, `حداقل ابعاد تصویر باید ${config.minWidth}×${config.minHeight} پیکسل باشد.`);
                callback(false);
                return;
            }

            if (img.width > config.maxWidth || img.height > config.maxHeight) {
                this.showError(widget, `حداکثر ابعاد مجاز ${config.maxWidth}×${config.maxHeight} پیکسل است.`);
                callback(false);
                return;
            }

            callback(true);
        };

        img.onerror = () => {
            this.showError(widget, 'فایل تصویر آسیب‌دیده است.');
            callback(false);
        };

        const reader = new FileReader();
        reader.onload = e => img.src = e.target.result;
        reader.readAsDataURL(file);
    }

    showPreview(input, file, widget) {
        const previewImg = document.getElementById(`preview-${input.id}`);
        const imagePreviewContainer = document.getElementById(`image-preview-${input.id}`) || 
                                     widget.querySelector('#image-preview');
        const selectBtn = document.getElementById(`select-btn-${input.id}`);
        const removeBtn = document.getElementById(`remove-btn-${input.id}`);

        if (!previewImg) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            previewImg.classList.remove('d-none');
            
            // نمایش контейнер پیش‌نمایش
            if (imagePreviewContainer) {
                imagePreviewContainer.classList.remove('d-none');
            }

            if (selectBtn) selectBtn.classList.add('d-none');
            if (removeBtn) removeBtn.classList.remove('d-none');
        };
        reader.readAsDataURL(file);
    }

        clearImageSelection(inputId) {
        const input = document.getElementById(inputId);
        if (!input) return;

        const widget = input.closest('.form-control');
        const previewImg = document.getElementById(`preview-${inputId}`);
        const imagePreviewContainer = document.getElementById(`image-preview-${inputId}`) || 
                                     widget.querySelector('#image-preview');
        const selectBtn = document.getElementById(`select-btn-${inputId}`);
        const removeBtn = document.getElementById(`remove-btn-${inputId}`);

        input.value = '';

        if (previewImg) {
            previewImg.src = '#';
            previewImg.classList.add('d-none');
        }
        if (imagePreviewContainer) {
            imagePreviewContainer.classList.add('d-none');
        }
        if (selectBtn) selectBtn.classList.remove('d-none');
        if (removeBtn) removeBtn.classList.add('d-none');

        this.clearOldErrors(widget);
    }

    showError(widget, message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'upload-error text-danger small mt-2';
        errorDiv.innerHTML = `<i class="fas fa-exclamation-circle me-1"></i> ${message}`;
        widget.appendChild(errorDiv);
    }

    clearOldErrors(widget) {
        widget.querySelectorAll('.upload-error').forEach(err => err.remove());
    }
}

// ==================== راه‌اندازی ====================
const imageInputHandler = new ImageInputHandler();

// برای دسترسی جهانی (در صورت نیاز)
window.clearImageSelection = (inputId) => {
    imageInputHandler.clearImageSelection(inputId);
};