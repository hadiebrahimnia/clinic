// ====================== input-rules.js ======================
document.addEventListener('DOMContentLoaded', function () {

    let errorTimeout = null;

    // ====================== محدوده‌های کدهای عددی ======================
    const PERSIAN_LETTERS_CODES = new Set([
        ...Array.from({ length: 0x06FF - 0x0600 + 1 }, (_, i) => 0x0600 + i), // عربی/فارسی پایه
        0x200C, // نیم‌فاصله (ZERO WIDTH NON-JOINER)
        0x200D, // ZERO WIDTH JOINER
    ]);

    const PERSIAN_NUMBERS_CODES = new Set([
        0x06F0, 0x06F1, 0x06F2, 0x06F3, 0x06F4,
        0x06F5, 0x06F6, 0x06F7, 0x06F8, 0x06F9
    ]);

    const ENGLISH_LETTERS_CODES = new Set([
        ...Array.from({ length: 26 }, (_, i) => 65 + i),   // A-Z
        ...Array.from({ length: 26 }, (_, i) => 97 + i),   // a-z
    ]);

    function isPersianLetter(char) {
        if (!char) return false;
        const code = char.codePointAt(0);
        return PERSIAN_LETTERS_CODES.has(code) || 
               (code >= 0x0600 && code <= 0x06FF) || 
               code === 0x200C || code === 0x200D;
    }

    function isPersianNumber(char) {
        if (!char) return false;
        const code = char.codePointAt(0);
        return PERSIAN_NUMBERS_CODES.has(code);
    }

    function isEnglishLetter(char) {
        if (!char) return false;
        const code = char.codePointAt(0);
        return (code >= 65 && code <= 90) || (code >= 97 && code <= 122);
    }

    function isDigit(char) {
        if (!char) return false;
        const code = char.codePointAt(0);
        return (code >= 48 && code <= 57) || isPersianNumber(char);
    }

    // ====================== اعمال قوانین ======================
    function enforceInputRules(input) {
        const type = input.dataset.inputType || 'text';

        const isAll = type === 'all';
        const isPersianLetters = type === 'persian-letters';
        const isPersianNumbers = type === 'persian-numbers';
        const isPersianAll    = type === 'persian';
        const isEnglishLetters = type === 'english-letters';
        const isEnglishNumbers = type === 'english-numbers';
        const isOnlyNumbers   = type === 'number';
        const isEnglishAll    = type === 'english';

        const maxLength = parseInt(input.getAttribute('maxlength')) || null;

        // ====================== Input Event ======================
        input.addEventListener('input', function () {
            let value = this.value;
            const original = value;

            let cleaned = '';

            for (let char of value) {
                let allowed = false;
                if (isAll) {
                    allowed =isPersianLetter(char) ||isEnglishLetter(char) ||isDigit(char) ||char === ' ' ||char === '\u200C';
                }
                else if  (isPersianLetters) {
                    allowed = isPersianLetter(char) || char === ' ' || char === '\u200C';
                }
                else if (isPersianNumbers) {
                    allowed = isPersianNumber(char);
                }
                else if (isPersianAll) {
                    allowed = isPersianLetter(char) || isPersianNumber(char) || char === ' ' || char === '\u200C';
                }
                else if (isEnglishLetters) {
                    allowed = isEnglishLetter(char) || char === ' ';
                }
                else if (isOnlyNumbers || isEnglishNumbers) {
                    allowed = isDigit(char);
                }
                else if (isEnglishAll) {
                    allowed = isEnglishLetter(char) || isDigit(char) || char === ' ';
                }

                if (allowed) {
                    cleaned += char;
                }
            }

            if (maxLength && cleaned.length > maxLength) {
                cleaned = cleaned.substring(0, maxLength);
            }

            if (cleaned !== original) {
                this.value = cleaned;
                showDebouncedError(getAlertMessage(type));
            }
        });

        // ====================== Keydown (پیشگیری لحظه‌ای) ======================
        input.addEventListener('keydown', function (e) {
            const key = e.key;

            if (['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab', 'Enter'].includes(key)) {
                return;
            }

            let allowed = false;

            if (isAll) { 
                allowed = isPersianLetter(key) || isEnglishLetter(key) || /^\d$/.test(key) || isPersianNumber(key) || key === ' '; 
            }
            else if (isPersianLetters) {
                allowed = isPersianLetter(key) || key === ' ';
            }
            else if (isPersianNumbers) {
                allowed = isPersianNumber(key);
            }
            else if (isPersianAll) {
                allowed = isPersianLetter(key) || isPersianNumber(key) || key === ' ';
            }
            else if (isEnglishLetters) {
                allowed = isEnglishLetter(key) || key === ' ';
            }
            else if (isOnlyNumbers || isEnglishNumbers) {
                allowed = /^\d$/.test(key) || isPersianNumber(key);
            }
            else if (isEnglishAll) {
                allowed = isEnglishLetter(key) || /^\d$/.test(key) || key === ' ';
            }

            if (!allowed) {
                e.preventDefault();
                showDebouncedError(getAlertMessage(type));
            }
        });

        // ====================== Paste ======================
        input.addEventListener('paste', function (e) {
            setTimeout(() => {
                // دوباره از input event استفاده می‌شود
                // اما برای اطمینان یکبار دیگر تمیز می‌کنیم
                const event = new Event('input');
                this.dispatchEvent(event);
            }, 10);
        });
    }

    // ====================== پیام‌ها ======================
    function getAlertMessage(type) {
        const messages = {
            'all': 'فقط حروف فارسی، انگلیسی و اعداد مجاز هستند!',
            'number': 'فقط اعداد مجاز هستند!',
            'persian-letters': 'فقط حروف فارسی مجاز هستند!',
            'persian-numbers': 'فقط اعداد فارسی مجاز هستند!',
            'persian': 'فقط حروف و اعداد فارسی مجاز هستند!',
            'english-letters': 'فقط حروف انگلیسی مجاز هستند!',
            'english-numbers': 'فقط اعداد انگلیسی مجاز هستند!',
            'english': 'فقط حروف و اعداد انگلیسی مجاز هستند!',
        };
        return messages[type] || 'ورودی نامعتبر است!';
    }

    function showDebouncedError(message) {
        if (errorTimeout) clearTimeout(errorTimeout);
        errorTimeout = setTimeout(() => showGrowlError(message), 400);
    }

    function showGrowlError(message) {
        if (typeof Growl !== 'undefined' && Growl.growl) {
            Growl.growl({
                title: 'خطای ورودی',
                message: message,
                style: 'error',
                size: 'medium',
                duration: 3000,
                location: 'top-right',
            });
        } else {
            console.warn(message);
        }
    }

    // ====================== اعمال خودکار ======================
    document.querySelectorAll('input[data-input-type]').forEach(input => {
        enforceInputRules(input);
    });
});