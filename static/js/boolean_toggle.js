// 🧠 BooleanButtonWidget JS - دکمه‌های چسبیده

function toggleBooleanButtons(id, state) {
    const input = document.getElementById(id);
    const wrapper = document.getElementById(`wrapper-${id}`);
    const buttons = wrapper.querySelectorAll(".boolean-btn");

    buttons.forEach(btn => {
        btn.classList.remove("active", "inactive");
    });

    const activeBtn = wrapper.querySelector(`[data-value="${state ? 1 : 0}"]`);
    const inactiveBtn = wrapper.querySelector(`[data-value="${state ? 0 : 1}"]`);

    if (activeBtn) activeBtn.classList.add("active");
    if (inactiveBtn) inactiveBtn.classList.add("inactive");

    input.value = state ? 1 : 0;
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".boolean-button-group").forEach(wrapper => {
        const input = wrapper.querySelector("input[type=hidden]");
        const state = input.value === "1";
        toggleBooleanButtons(input.id, state);
    });
});
