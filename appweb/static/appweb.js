document.observe("dom:loaded", function() {
    bubble = $$(".action-report-bubble")[0];

    // Solo en pagina de busqueda, que hay burbuja
    if (bubble) {
        bubble.button = false;

        // Mostrar informacion
        $$(".result-item").each(function (result){
            $(result).observe("click", function(event) {

                // Clicks fuera de la burbuja
                if (bubble.button && (!Event.element(event).descendantOf(bubble)))
                {
                    toggle(bubble.button, bubble, "js-bubble-show");
                    bubble.button = false;
                } else {
                    var stop = true;
                    var result = $(this);
                    var button = Event.element(event);
                    if (!button.match(".button"))
                        button = button.up(".button");
                    if (result) {
                        if (!button || button.up(".result-action-info"))
                            toggle(result.down(".result-action-info .button"), result, "result-expanded");
                        else if (button.up(".result-action-report")) {
                            toggle(button, bubble, "js-bubble-show");
                            var buttonPos = Element.cumulativeOffset(button);
                            bubble.style.top = buttonPos[1]+"px";
                            bubble.style.left = buttonPos[0]+"px";
                            bubble.button = button;
                        }
                        else
                            stop = false;
                    }
                }

                if (stop)
                    Event.stop(event);
            });
        });
    }
});


function toggle(button, parent, className){
    if (button.hasClassName("button-off")) {
        button.addClassName("button-on").removeClassName("button-off");
        parent.addClassName(className);
    } else {
        button.addClassName("button-off").removeClassName("button-on");
        parent.removeClassName(className);
    }
}
