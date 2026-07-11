document.addEventListener("DOMContentLoaded", () => {

    document.querySelectorAll(".color-widget").forEach(widget => {

        const picker = widget.querySelector("input[type=color]");
        const textInput = widget.querySelector("input[type=text]");
        const previewBtn = widget.querySelector(".color-preview");
        const previewText = previewBtn.querySelector(".preview-text");

        function updateColor(color) {
            picker.value = color;
            textInput.value = color;
            previewBtn.style.backgroundColor = color;
            
            // هوشمندانه کردن رنگ متن داخل دکمه (سفید یا سیاه)
            const r = parseInt(color.substr(1,2), 16);
            const g = parseInt(color.substr(3,2), 16);
            const b = parseInt(color.substr(5,2), 16);
            const brightness = (r * 299 + g * 587 + b * 114) / 1000;
            
            previewText.style.color = brightness > 128 ? '#000000' : '#ffffff';
        }

        // رویداد picker
        picker.addEventListener("input", () => {
            updateColor(picker.value);
        });

        // رویداد ورودی متنی
        textInput.addEventListener("input", () => {
            if(/^#[0-9a-fA-F]{6}$/.test(textInput.value)){
                updateColor(textInput.value);
            }
        });

        // مقدار اولیه
        updateColor(picker.value);
    });
});