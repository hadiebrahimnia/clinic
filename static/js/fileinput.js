function initFileInput(id) {

    const input = document.getElementById(id);

    if (!input) return;

    input.addEventListener("change", function () {

        const preview = document.getElementById("file-preview-" + id);
        const select = document.getElementById("select-btn-" + id);
        const filename = document.getElementById("filename-" + id);

        if (this.files.length === 0) {

            preview.classList.add("d-none");
            select.classList.remove("d-none");

            return;
        }

        select.classList.add("d-none");
        preview.classList.remove("d-none");

        filename.innerText = this.files[0].name;
    });
}


function clearFileSelection(id) {

    const input = document.getElementById(id);

    input.value = "";

    document
        .getElementById("select-btn-" + id)
        .classList.remove("d-none");

    document
        .getElementById("file-preview-" + id)
        .classList.add("d-none");

    document
        .getElementById("filename-" + id)
        .innerHTML = "";
}



document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('input[type="file"]').forEach(function (input) {
        if (input.id) {
            initFileInput(input.id);
        }
    });
});