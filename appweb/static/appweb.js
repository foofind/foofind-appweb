document.observe("dom:loaded", function() {
    console.log("b");
    $$(".result-action-info > a").each(function (o){
        $(o).observe("click", function(event) {
            var element = Event.element(event).up("a");
            var parent = element.up(".result-item");
            if (element.hasClassName("button-off")) {
                element.addClassName("button-on").removeClassName("button-off");
                parent.addClassName("result-expanded");
            } else {
                element.addClassName("button-off").removeClassName("button-on");
                parent.removeClassName("result-expanded");
            }
        });
    });
});
