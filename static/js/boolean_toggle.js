// 🧠 BooleanToggleWidget JS - انیمیشن نرم + رنگ‌های قابل تنظیم

function toggleBooleanButtons(id, state) {
    const input = document.getElementById(id);
    const wrapper = document.getElementById(`wrapper-${id}`);
    const buttons = wrapper.querySelectorAll(".boolean-btn");

    // خواندن رنگ‌ها از data attribute
    let colors = {};
    try {
        colors = JSON.parse(wrapper.dataset.colors || '{}');
    } catch (e) {
        console.warn("Colors data parse error");
    }

    buttons.forEach(btn => {
        btn.classList.remove("active", "inactive");
        
        const isTrueBtn = btn.dataset.value === "1";
        const targetColor = state === isTrueBtn 
            ? (isTrueBtn ? colors.true : colors.false)
            : (isTrueBtn ? colors.true_inactive : colors.false_inactive);

        // اعمال رنگ با transition
        btn.style.transition = 'all 0.4s cubic-bezier(0.4, 0.0, 0.2, 1)';
        btn.style.backgroundColor = targetColor;
    });

    const activeBtn = wrapper.querySelector(`[data-value="${state ? 1 : 0}"]`);
    const inactiveBtn = wrapper.querySelector(`[data-value="${state ? 0 : 1}"]`);

    if (activeBtn) {
        activeBtn.classList.add("active");
        activeBtn.style.transform = 'scale(1.02)';
    }
    if (inactiveBtn) {
        inactiveBtn.classList.add("inactive");
        inactiveBtn.style.transform = 'scale(1)';
    }

    input.value = state ? 1 : 0;

    // تریگر event برای فرم
    input.dispatchEvent(new Event('change', { bubbles: true }));
}

// مقداردهی اولیه
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".boolean-button-group").forEach(wrapper => {
        const input = wrapper.querySelector("input[type=hidden]");
        const initialState = input.value === "1" || input.value === "true";
        
        // اعمال رنگ اولیه
        const colors = JSON.parse(wrapper.dataset.colors || '{}');
        const buttons = wrapper.querySelectorAll(".boolean-btn");
        
        buttons.forEach(btn => {
            const isTrueBtn = btn.dataset.value === "1";
            const isActive = (initialState && isTrueBtn) || (!initialState && !isTrueBtn);
            
            const color = isActive 
                ? (isTrueBtn ? colors.true : colors.false)
                : (isTrueBtn ? colors.true_inactive : colors.false_inactive);
            
            btn.style.backgroundColor = color;
        });

        toggleBooleanButtons(input.id, initialState);
    });
});