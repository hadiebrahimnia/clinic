document.addEventListener('DOMContentLoaded', function () {

    const country = document.getElementById('id_country');
    const province = document.getElementById('id_province');
    const city = document.getElementById('id_city');


    country?.addEventListener('change', function () {

        const countryId = this.value;
        const url = this.dataset.url;

        province.innerHTML =
            '<option value="">استان را انتخاب نمایید</option>';

        city.innerHTML =
            '<option value="">شهر محل سکونت را انتخاب نمایید</option>';

        city.disabled = true;

        if (!countryId) {
            province.disabled = true;
            return;
        }

        fetch(`${url}?country_id=${countryId}`)
            .then(response => response.json())
            .then(data => {

                province.disabled = false;

                data.forEach(item => {
                    province.innerHTML += `
                        <option value="${item.id}">
                            ${item.name_fa}
                        </option>
                    `;
                });
            });
    });


    province?.addEventListener('change', function () {

        const provinceId = this.value;
        const url = this.dataset.url;

        city.innerHTML = '<option value="">شهر محل سکونت را انتخاب نمایید</option>';

        if (!provinceId) {
            city.disabled = true;
            return;
        }

        fetch(`${url}?province_id=${provinceId}`)
            .then(response => response.json())
            .then(data => {
                city.disabled = false;

                data.forEach(item => {
                    city.innerHTML += `
                        <option value="${item.id}">
                            ${item.name_fa}
                        </option>
                    `;
                });

                // ←←← این خط خیلی مهم است (بعد از لود شهرها)
                if (data.length > 0) {
                    city.value = '';   // یا مقدار پیش‌فرض اگر لازم بود
                }
            });
    });

});

