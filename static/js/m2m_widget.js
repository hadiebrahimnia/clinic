document.addEventListener("DOMContentLoaded", () => {

    document.querySelectorAll(".m2m-widget").forEach(initWidget);

});


function initWidget(widget){

    const select = widget.querySelector("select");

    const display = widget.querySelector(".m2m-display");

    const list = widget.querySelector(".m2m-options");

    const search = widget.querySelector(".m2m-search");

    //--------------------------------------------------
    // Build Options
    //--------------------------------------------------

    list.innerHTML = "";

    Array.from(select.options).forEach(option=>{

        const li=document.createElement("li");

        li.dataset.value=option.value;

        li.textContent=option.textContent;

        if(option.selected){

            li.classList.add("selected");

        }

        li.onclick=()=>{

            option.selected=!option.selected;

            render(widget);

        };

        list.appendChild(li);

    });

    //--------------------------------------------------

    display.onclick=(e)=>{

        if(e.target.tagName==="I") return;

        widget.classList.toggle("open");

        search.focus();

    };

    //--------------------------------------------------

    search.oninput=()=>{

        const txt=search.value.toLowerCase();

        list.querySelectorAll("li").forEach(li=>{

            li.style.display=

                li.textContent.toLowerCase().includes(txt)

                ? ""

                : "none";

        });

    };

    //--------------------------------------------------

    document.addEventListener("click",(e)=>{

        if(!widget.contains(e.target)){

            widget.classList.remove("open");

        }

    });

    render(widget);

}



function render(widget){

    const select=widget.querySelector("select");

    const chips=widget.querySelector(".m2m-selected-items");

    const placeholder=widget.querySelector(".m2m-placeholder");

    const list=widget.querySelector(".m2m-options");

    chips.innerHTML="";

    Array.from(list.children).forEach(li=>{

        const option=select.querySelector(`option[value="${li.dataset.value}"]`);

        li.classList.toggle("selected",option.selected);

    });

    Array.from(select.selectedOptions).forEach(option=>{

        const chip=document.createElement("div");

        chip.className="m2m-chip";

        chip.innerHTML=`
            ${option.textContent}
            <i class="fa fa-times-circle"></i>
        `;

        chip.querySelector("i").onclick=(e)=>{

            e.stopPropagation();

            option.selected=false;

            render(widget);

        };

        chips.appendChild(chip);

    });

    placeholder.style.display=

        select.selectedOptions.length

        ? "none"

        : "block";

}