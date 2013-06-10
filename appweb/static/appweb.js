// Constantes
var MAX_ERROR_COUNT = 15;

// objetos de la pagina
var  content, results, loading_results, current_search_form, report, report_form, report_file_id;

// estado de la pagina
var loaded_ids = {}, errors_count = 0;

// actividad de la pagina
var requesting = null, stopped = false;

document.observe("dom:loaded", function() {
    content = $("content");
    results = $("results");
    loading_results = $("loading-results");
    current_search_form = $('current_search');
    report = $("report");
    report_form = $("report_form");
    report_file_id = $("file_id");

    // Solo en pagina de busqueda, que hay resultados
    if (results) {
        report.button = false;
        updateItems(report);

        // Formulario de quejas
        report_form.observe('submit', function(event) {
            sendReport();
            Event.stop(event);
        });

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
                toggle(report.button, report, "js-show");
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
                    } else if (button.up(".result-action-report")) {
                        toggle(button, report, "js-show");
                        var buttonPos = Element.cumulativeOffset(button);
                        report_file_id.value = result.readAttribute("data-id");
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


function sendReport(){
    report_request = new Ajax.Request('complaint', {
        method: 'post',
        parameters: report_form.serialize(true),
        onSuccess: function(transport) {
            $$(".wrong").each(function(item){item.removeClassName("wrong");});
            result = eval(transport.responseText);
            if (result===true) {
                report_form.reset();
                toggle(report.button, report, "js-show");
                report.button = false;
                alert("Your complaint has been sent.");
            } else if (result===false) {
                report_form.reset();
                toggle(report.button, report, "js-show");
                report.button = false;
                alert("Error!");
            } else {
                alert("Invalid values!");
                for (field in result){
                    $(result[field]).addClassName("wrong");
                }
            }
        },
        onFailure: function(transport) {
        }
    });
}
