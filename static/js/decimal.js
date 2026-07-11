// document.addEventListener("DOMContentLoaded", function () {
    
//     const input = document.getElementById("id_degrees-0-gpa");
//     if (!input)
//         return;

//     input.addEventListener("input", function () {

//         // فقط اعداد را نگه دار
//         let value = this.value.replace(/\D/g, "");

//         if (value.length <= 2) {
//             this.value = value;
//             return;
//         }

//         // بعد از دو رقم اول نقطه قرار بده
//         this.value = value.slice(0, 2) + "." + value.slice(2, 4);
//     });

// });