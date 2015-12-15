(function () {


    document.getElementById("log-toggle-meta").addEventListener("click", function() {
        selectors = [
            ".record.join",
            ".record.part",
            ".record.quit",
        ]
        for (i = 0; i < selectors.length; ++i) {
            elements = document.querySelectorAll(selectors[i]);
            if(!elements) {
                continue;
            }
            for (j = 0; j < elements.length; ++j) {
                element = elements[j];
                if(element.classList.contains("hidden")) {
                    element.classList.remove("hidden")
                } else {
                    element.classList.add("hidden")
                }
            }
        }
    });


    document.getElementById("log-toggle-colors").addEventListener("click", function() {
        console.log("toggle");
        elements = document.querySelectorAll(".record .nick");
        for (j = 0; j < elements.length; ++j) {
            element = elements[j];
            if(element.classList.contains("colorinherit")) {
                element.classList.remove("colorinherit")
            } else {
                element.classList.add("colorinherit")
            }
        }
    });


})();