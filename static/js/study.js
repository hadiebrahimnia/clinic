document.addEventListener('DOMContentLoaded', function () {

    const field = document.getElementById('id_field');
    const specialization = document.getElementById('id_specialization');

    field?.addEventListener('change', function () {

        const fieldId = this.value;
        const url = this.dataset.url;

        specialization.innerHTML =
            '<option value="">گرایش را انتخاب نمایید</option>';

        specialization.disabled = true;

        if (!fieldId)
            return;

        fetch(`${url}?field_id=${fieldId}`)
            .then(response => response.json())
            .then(data => {

                specialization.disabled = false;

                data.forEach(item => {
                    specialization.innerHTML += `
                        <option value="${item.id}">
                            ${item.name_fa}
                        </option>
                    `;
                });

                if (data.length > 0) {
                    specialization.value = '';
                }
            });

    });

});