// ====================== input-rules.js ======================

document.addEventListener('DOMContentLoaded', function () {

    let errorTimeout = null;

    function enforceInputRules(input) {
        const type = input.dataset.inputType || 'text';

        const config = {
            // فقط number
            onlyNumbers: type === 'number',

            // Persian Modes
            persianLettersOnly: type === 'persian-letters',
            persianNumbersOnly: type === 'persian-numbers',
            persianAll: type === 'persian',           // حروف + اعداد فارسی

            // English Modes
            englishLettersOnly: type === 'english-letters',
            englishNumbersOnly: type === 'english-numbers',
            englishAll: type === 'english',           // حروف + اعداد انگلیسی

            maxLength: parseInt(input.getAttribute('maxlength')) || null,
        };

        // ====================== رویداد Input ======================
        input.addEventListener('input', function () {
            let value = this.value;
            let originalValue = value;

            // ==================== Number (لاتین) ====================
            if (config.onlyNumbers) {
                value = value.replace(/[^0-9۰-۹]/g, '');
            }

            // ==================== Persian ====================
            if (config.persianLettersOnly) {
                value = value.replace(/[^ء-ی\s]/g, '');           // فقط حروف فارسی
            }
            if (config.persianNumbersOnly) {
                value = value.replace(/[^۰-۹]/g, '');             // فقط اعداد فارسی
            }
            if (config.persianAll) {
                value = value.replace(/[^ء-ی۰-۹\s]/g, '');        // حروف + اعداد فارسی
            }

            // ==================== English ====================
            if (config.englishLettersOnly) {
                value = value.replace(/[^a-zA-Z\s]/g, '');        // فقط حروف انگلیسی
            }
            if (config.englishNumbersOnly) {
                value = value.replace(/[^0-9]/g, '');             // فقط اعداد انگلیسی
            }
            if (config.englishAll) {
                value = value.replace(/[^a-zA-Z0-9\s]/g, '');     // حروف + اعداد انگلیسی
            }

            if (config.maxLength && value.length > config.maxLength) {
                value = value.substring(0, config.maxLength);
            }

            if (value !== originalValue) {
                this.value = value;
                showDebouncedError(getAlertMessage(type));
            }
        });

        // ====================== Keypress برای فیلد عددی لاتین ======================
        if (config.onlyNumbers) {
            input.addEventListener('keypress', function (e) {
                if (!/^[0-9]$/.test(e.key)) {
                    e.preventDefault();
                    showDebouncedError('فقط اعداد مجاز هستند!');
                }
            });
        }

        // ====================== Paste ======================
        input.addEventListener('paste', function (e) {
            setTimeout(() => {
                if ((config.onlyNumbers || config.englishNumbersOnly) && /[^0-9]/.test(this.value)) {
                    this.value = this.value.replace(/[^0-9]/g, '');
                    showGrowlError('فقط اعداد مجاز هستند!');
                }
            }, 10);
        });
    }

    // ====================== پیام‌های هشدار ======================
    function getAlertMessage(type) {
        switch(type) {
            case 'number':
                return 'فقط اعداد مجاز هستند!';
            case 'persian-letters':
                return 'فقط حروف فارسی مجاز هستند!';
            case 'persian-numbers':
                return 'فقط اعداد فارسی مجاز هستند!';
            case 'persian':
                return 'فقط حروف و اعداد فارسی مجاز هستند!';
            case 'english-letters':
                return 'فقط حروف انگلیسی مجاز هستند!';
            case 'english-numbers':
                return 'فقط اعداد انگلیسی مجاز هستند!';
            case 'english':
                return 'فقط حروف و اعداد انگلیسی مجاز هستند!';
            default:
                return 'ورودی نامعتبر است!';
        }
    }

    // ====================== Debounce نمایش ارور ======================
    function showDebouncedError(message) {
        if (errorTimeout) clearTimeout(errorTimeout);

        errorTimeout = setTimeout(() => {
            showGrowlError(message);
        }, 450);
    }

    function showGrowlError(message) {
        if (typeof Growl !== 'undefined' && typeof Growl.growl === 'function') {
            Growl.growl({
                title: 'خطای ورودی',
                message: message,
                style: 'error',
                size: 'medium',
                duration: 3500,
                location: 'top-right',
                fixed: false,
                delayOnHover: true,
            });
        } else {
            console.warn('Growl:', message);
        }
    }

    // ====================== اعمال خودکار ======================
    document.querySelectorAll('input[data-input-type]').forEach(input => {
        enforceInputRules(input);
    });

});