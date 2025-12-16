document.addEventListener('DOMContentLoaded', function () {
    let mainPasswordValue = '';
    let mainInputId = null;

    // تابع toggle نمایش/مخفی کردن رمز
    window.togglePasswordVisibility = function(inputId) {
        const input = document.getElementById(inputId);
        const icon = document.getElementById('eye-icon-' + inputId);

        if (input.type === 'password') {
            input.type = 'text';
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        } else {
            input.type = 'password';
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        }
    };

    // پیدا کردن همه ویجیت‌ها
    document.querySelectorAll('.password-strength-widget input[type="password"]').forEach(input => {
        const widget = input.closest('.password-strength-widget');
        const inputId = input.id;
        const hasRules = widget.querySelector('.password-rules');

        if (hasRules) {
            // این فیلد اصلی است (دارای قوانین)
            mainInputId = inputId;

            input.addEventListener('input', function () {
                mainPasswordValue = this.value;
                updatePasswordStrength(this.value, inputId);

                // به‌روزرسانی تطابق در فیلد تکرار (اگر وجود داشته باشد)
                const confirmInputs = document.querySelectorAll('.password-strength-widget input[type="password"]');
                confirmInputs.forEach(ci => {
                    if (ci.id !== inputId) {
                        checkPasswordMatch(mainPasswordValue, ci.value, ci.id);
                    }
                });
            });

        } else {
            // این فیلد تکرار است
            input.addEventListener('input', function () {
                checkPasswordMatch(mainPasswordValue, this.value, inputId);
            });
        }
    });

    function updatePasswordStrength(password, inputId) {
        const bar = document.getElementById(`strength-bar-${inputId}`);
        const text = document.getElementById(`strength-text-${inputId}`);
        const rules = document.querySelectorAll(`#rules-${inputId} li`);
        let strength = 0;

        if (password.length >= 8) { strength++; markRule(rules[0], true); } else { markRule(rules[0], false); }
        if (/[a-z]/.test(password)) { strength++; markRule(rules[1], true); } else { markRule(rules[1], false); }
        if (/[A-Z]/.test(password)) { strength++; markRule(rules[2], true); } else { markRule(rules[2], false); }
        if (/[0-9]/.test(password)) { strength++; markRule(rules[3], true); } else { markRule(rules[3], false); }
        if (/[@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?~]/.test(password)) { strength++; markRule(rules[4], true); } else { markRule(rules[4], false); }

        if (strength === 0) {
            bar.style.width = '0%';
            bar.className = 'progress-bar bg-danger';
            text.textContent = 'رمز عبور خیلی ضعیف است';
        } else if (strength <= 2) {
            bar.style.width = '30%';
            bar.className = 'progress-bar bg-danger';
            text.textContent = 'ضعیف';
        } else if (strength <= 3) {
            bar.style.width = '60%';
            bar.className = 'progress-bar bg-warning';
            text.textContent = 'متوسط';
        } else if (strength === 4) {
            bar.style.width = '85%';
            bar.className = 'progress-bar bg-info';
            text.textContent = 'قوی';
        } else {
            bar.style.width = '100%';
            bar.className = 'progress-bar bg-success';
            text.textContent = 'خیلی قوی!';
            text.style.color = '#28a745';
        }
    }

    function markRule(li, valid) {
        valid ? li.classList.add('valid') : li.classList.remove('valid');
    }

    function checkPasswordMatch(pass1, pass2, confirmId) {
        const matchDiv = document.getElementById(`confirm-match-${confirmId}`);
        if (!matchDiv) return;

        if (pass2 === '') {
            matchDiv.style.display = 'none';
        } else if (pass1 === pass2 && pass1 !== '') {
            matchDiv.style.display = 'block';
            matchDiv.innerHTML = '<span class="text-success"></span>';
        } else {
            matchDiv.style.display = 'block';
            matchDiv.innerHTML = '<span class="text-danger"><i class="fas fa-times-circle fa-lg"></i> تکرار رمز عبور با رمز عبور مطابقت ندارند</span>';
        }
    }
});