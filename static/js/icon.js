document.addEventListener("DOMContentLoaded", () => {

    document.querySelectorAll(".animated-toggle").forEach(button => {

        const icon = button.querySelector("i");
        if (!icon) return;

        const openIcon = button.dataset.iconOpen;
        const closeIcon = button.dataset.iconClose;

        let active = false;

        function animate(toIcon){

            icon.classList.add("icon-hide");

            setTimeout(()=>{

                icon.className="";

                toIcon.split(" ").forEach(cls=>{
                    icon.classList.add(cls);
                });

                icon.classList.add("icon-show");

            },180);

            setTimeout(()=>{
                icon.classList.remove("icon-hide","icon-show");
            },550);
        }

        function open(){

            if(active) return;

            active=true;
            animate(openIcon);

        }

        function close(){

            if(!active) return;

            active=false;
            animate(closeIcon);

        }

        // -------------------------
        // اگر Dropdown باشد
        // -------------------------

        if(button.dataset.bsToggle==="dropdown"){

            const dropdown=button.closest(".dropdown");

            dropdown.addEventListener("show.bs.dropdown",open);
            dropdown.addEventListener("hide.bs.dropdown",close);

        }

        // -------------------------
        // اگر دکمه معمولی باشد
        // -------------------------

        else{

            button.addEventListener("click",()=>{

                active ? close() : open();

            });

        }

    });

});