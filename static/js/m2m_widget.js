// 🧠 ManyToManySearchWidget JS (Vanilla)

function toggleM2MDropdown(id) {
    const widget = document.getElementById(`wrapper-${id}`);
    widget.classList.toggle("open");

    const select = document.getElementById(id);
    const dropdown = document.getElementById(`dropdown-${id}`);
    const list = dropdown.querySelector(".m2m-options");
    const search = dropdown.querySelector(".m2m-search");

    // بارگذاری گزینه‌ها فقط یک‌بار
    if (!list.hasChildNodes()) {
        Array.from(select.options).forEach(opt => {
            const li = document.createElement("li");
            li.textContent = opt.textContent;
            li.dataset.value = opt.value;
            if (opt.selected) li.classList.add("selected");
            li.addEventListener("click", () => toggleM2MOption(id, li));
            list.appendChild(li);
        });
    }

    // فوکوس روی سرچ
    setTimeout(() => search.focus(), 100);
}

function toggleM2MOption(id, li) {
    const select = document.getElementById(id);
    const wrapper = document.getElementById(`wrapper-${id}`);
    const chipsContainer = wrapper.querySelector(".m2m-selected-items");
    const placeholder = wrapper.querySelector(".m2m-placeholder");

    li.classList.toggle("selected");
    const value = li.dataset.value;

    // مدیریت select واقعی
    const option = Array.from(select.options).find(o => o.value === value);
    option.selected = !option.selected;

    // مدیریت نمایش chipها
    chipsContainer.innerHTML = "";
    const selectedOptions = Array.from(select.selectedOptions);

    selectedOptions.forEach(opt => {
        const chip = document.createElement("div");
        chip.className = "m2m-chip";
        chip.innerHTML = `${opt.textContent} <i class="fa fa-times-circle" onclick="removeM2MChip('${id}', '${opt.value}')"></i>`;
        chipsContainer.appendChild(chip);
    });

    placeholder.style.display = selectedOptions.length ? "none" : "block";
}

function removeM2MChip(id, value) {
    const select = document.getElementById(id);
    const option = Array.from(select.options).find(o => o.value === value);
    if (option) option.selected = false;

    const dropdown = document.getElementById(`dropdown-${id}`);
    const li = dropdown.querySelector(`li[data-value="${value}"]`);
    if (li) li.classList.remove("selected");

    const wrapper = document.getElementById(`wrapper-${id}`);
    const chipsContainer = wrapper.querySelector(".m2m-selected-items");
    const placeholder = wrapper.querySelector(".m2m-placeholder");

    chipsContainer.querySelectorAll(".m2m-chip").forEach(chip => {
        if (chip.textContent.includes(option.textContent)) chip.remove();
    });

    if (select.selectedOptions.length === 0) placeholder.style.display = "block";
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".m2m-widget").forEach(widget => {
        const id = widget.querySelector("select").id;
        const dropdown = document.getElementById(`dropdown-${id}`);
        const search = dropdown.querySelector(".m2m-search");

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
