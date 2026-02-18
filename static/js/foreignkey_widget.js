// 🧠 ForeignKeySearchWidget JS - بدون jQuery

function toggleDropdown(id) {
    const widget = document.getElementById(`wrapper-${id}`);
    widget.classList.toggle("open");

    const select = document.getElementById(id);
    const dropdown = document.getElementById(`dropdown-${id}`);
    const optionsContainer = dropdown.querySelector(".fk-options");
    const searchInput = dropdown.querySelector(".fk-search");

    // پر کردن گزینه‌ها فقط یک بار
    if (!optionsContainer.hasChildNodes()) {
        Array.from(select.options).forEach(opt => {
            const li = document.createElement("li");
            li.textContent = opt.textContent;
            li.dataset.value = opt.value;
            if (opt.selected) li.classList.add("selected");
            li.addEventListener("click", () => selectOption(id, li));
            optionsContainer.appendChild(li);
        });
    }

    // فوکوس روی سرچ
    setTimeout(() => searchInput.focus(), 100);
}

function selectOption(id, li) {
    const select = document.getElementById(id);
    const wrapper = document.getElementById(`wrapper-${id}`);
    const display = wrapper.querySelector(".fk-display .fk-selected");
    const placeholder = wrapper.querySelector(".fk-display .fk-placeholder");
    const dropdown = document.getElementById(`dropdown-${id}`);
    const allOptions = dropdown.querySelectorAll("li");

    allOptions.forEach(opt => opt.classList.remove("selected"));
    li.classList.add("selected");

    // مقداردهی به select واقعی
    select.value = li.dataset.value;

    // نمایش در نمای اصلی
    placeholder.style.display = "none";
    display.textContent = li.textContent;

    wrapper.classList.remove("open");
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".fk-widget").forEach(widget => {
        const id = widget.querySelector("select").id;
        const dropdown = document.getElementById(`dropdown-${id}`);
        const search = dropdown.querySelector(".fk-search");

        // فیلتر زنده
        search.addEventListener("input", e => {
            const value = e.target.value.toLowerCase();
            const options = dropdown.querySelectorAll("li");
            options.forEach(opt => {
                const text = opt.textContent.toLowerCase();
                opt.style.display = text.includes(value) ? "block" : "none";
            });
        });

        // بستن با کلیک بیرون
        document.addEventListener("click", ev => {
            if (!widget.contains(ev.target)) widget.classList.remove("open");
        });
    });
});
