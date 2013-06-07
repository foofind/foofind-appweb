// Constantes
var MAX_ERROR_COUNT = 15;

// objetos de la pagina
var current_search_form, report, content, no_results, results, loading_results;

// estado de la pagina
var loaded_ids = {}, errors_count = 0;

// actividad de la pagina
var requesting = null, stopped = false;

document.observe("dom:loaded", function() {
    current_search_form = $('current_search');
    results = $("results");
    content = $("content");
    report = $$(".report")[0];
    loading_results = $("loading-results");

    // Solo en pagina de busqueda, que hay resultados
    if (results) {
        report.button = false;
        updateItems(report);

        // Nueva busqueda
        $("new_search").observe('submit', function() {
            stop();
            results.update();
            loading_results.show();
        });

        // Pide más resultados
        content.observe('scroll', scrollHandler);
        scrollHandler();
    }
});

function scrollHandler() {
    var height = content.getHeight();
    if (height>content.scrollHeight-content.scrollTop-height) {
        getMoreItems();
        return true;
    }
    return false;
}

function stop() {
    stopped = true;
    if (requesting) {
        requesting.transport.abort();
    }
}

function getMoreItems(){
    // No sigue si ha habido demasiados errores o si se ha parado la busqueda
    if (errors_count>MAX_ERROR_COUNT || stopped) {
        return;
    }

    if (!requesting) {
        loading_results.show();
        requesting = new Ajax.Request('searcha', {
            method: 'post',
            parameters: current_search_form.serialize(true),
            onSuccess: function(transport, data) {
                // Reinicia errores si llegan resultados
                if (data["files_ids"].length>0)
                    errors_count=0;

                // Si se ha llegado al final, no carga mas
                if (data["end"] && data["sure"]) {
                    if (data["total_found"]==0)
                        content.addClassName("no-results");
                    loading_results.hide();
                    stopped = true;
                } else
                    setTimeout(function(){requesting=null; if (!scrollHandler()) loading_results.hide();}, data["wait"]);

                // Almacena nuevos resultados
                $("last_items").value = data["last_items"];
                results.insert(transport.responseText);
                updateItems(report);
            },
            onFailure: function() {
                errors_count+=1;
            }
        });
    }
}

function updateItems(report){
    // Configura items
    $$(".result-item.just-added").each(function (result_item){
        var item = $(result_item);
        var item_id = item.readAttribute("data-id");

        // comprueba que no exista ya en los resultados
        if (item_id in loaded_ids) {
            item.remove();
            return;
        }
        loaded_ids[item_id] = true;

        item.observe("click", function(event) {
            // Clicks fuera de la burbuja de reportar
            if (report.button && (!Event.element(event).descendantOf(report)))
            {
                toggle(report.button, report, "js-report-show");
                report.button = false;
            } else {
                var stop = true;
                var result = $(this);
                var button = Event.element(event);
                if (!button.match(".button"))
                    button = button.up(".button");
                if (result) {
                    if (!button || button.up(".result-action-info")) {
                        toggle(result.down(".result-action-info .button"), result, "result-expanded");
                    } else if (button.up(".report")) {
                        toggle(button, report, "js-report-show");
                        var buttonPos = Element.cumulativeOffset(button);
                        report.style.top = buttonPos[1]+"px";
                        report.style.left = buttonPos[0]+"px";
                        report.button = button;
                    }
                    else
                        stop = false;
                }
            }

            if (stop)
                Event.stop(event);
        });
        item.removeClassName("just-added");
    });
}

function toggle(button, parent, className){
    if (button.hasClassName("button-off")) {
        button.addClassName("button-on").removeClassName("button-off");
        parent.addClassName(className);
    } else {
        button.addClassName("button-off").removeClassName("button-on");
        parent.removeClassName(className);
    }
}
