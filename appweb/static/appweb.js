// Constantes
var MAX_ERROR_COUNT = 15;
var ERROR_MESSAGE = "We coulnd't process your request due to an internal error. We will try to fix it as soon as possible.";
var EMAIL_REQUEST = "In the meantime, you can send your request to the following email address: blablablabla@mp2p.net.";
var VALIDATION_MESSAGES = ["Some values are missing. Please fill all the fields marked with a star (*).\n\n", "Invalid format for the email. Please check that it is a valid email address.\n\n", "You have to accept our terms of use and privacy policy by clicking on the checkbox.\n\n"];

// objetos de la pagina
var content, new_filetype, filetype_select, filetype_active; // siempre
var results, loading_results, current_search_form, results_count=0, report, close_report, report_form, report_file_id, report_request, vote_request; // busqueda

// estado de la pagina
var loaded_ids = {}, errors_count = 0, stop_event=false;

// actividad de la pagina
var requesting = null, stopped = false;

document.observe("dom:loaded", function() {
    content = $("content");
    new_filetype = $("new_filetype");

    filetype_select = $("filetype_select");
    filetype_active = $("filetype_active");
    filetype_active.innerHTML = $$("#filetype_select li ."+new_filetype.value)[0].outerHTML;
    filetype_select.toggle(false);
    filetype_select.removeClassName("loading");
    filetype_active.observe("click", filetype_active_click);

    $$("#filetype_select li").each(function(item){
        item.observe("click", filetype_select_click);
    });

    $(document).observe('click', function(event) {
        var source = Event.element(event);
        if (filetype_select.visible() && !source.descendantOf(filetype_select) && !source.descendantOf(filetype_active)) {
            filetype_select.toggle(false);
        }
        if (report && report.button && (source==close_report || (source!=report.button && !source.descendantOf(report.button) && !source.descendantOf(report))))
        {
            clearReport();
        }
        if (stop_event) {
            Event.stop(event);
            stop_event = false;
        }
    });

    // Solo en pagina de busqueda, que hay resultados
    if (content) {
        results = $("results");
        loading_results = $("loading-results");
        current_search_form = $('current_search');
        report = $("report");
        close_report = $("close_report");
        report_form = $("report_form");
        report_file_id = $("file_id");

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
            results.innerHTML = "";
            content.removeClassName("no-results");
            loading_results.show();
        });

        // Pide más resultados
        content.observe('scroll', scrollHandler);
        scrollHandler();
    }
});

function filetype_active_click(event) {
    filetype_select.toggle(true);
}
function filetype_select_click() {
    var html = this.innerHTML;
    filetype_active.innerHTML = html;
    filetype_select.toggle(false);
    new_filetype.value = $(this).firstDescendant().className;
}

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
            onSuccess: getMoreItems_onSuccess,
            onFailure: getMoreItems_onFailure
        });
    }
}

function getMoreItems_onSuccess(transport, data)  {
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
}
function getMoreItems_onFailure() {
    errors_count+=1;
}

function updateItems(report){
    // Configura items
    $$(".result-item.just-added").each(updateItem);
}

function updateItem(result_item) {
    var item = $(result_item);
    var item_id = item.readAttribute("data-id");

    // comprueba que no exista ya en los resultados
    if (item_id in loaded_ids) {
        item.remove();
        return;
    }
    loaded_ids[item_id] = true;

    item.observe("click", item_click);
    item.removeClassName("just-added");

    // añade clase par o impar
    if (results_count%2==0)
        item.addClassName("result-odd");
    else
        item.addClassName("result-even");
    results_count+=1;
}

function item_click(event) {
    stop_event = false;
    var result = $(this);
    var button = Event.element(event);
    if (!button.match(".button"))
        button = button.up(".button");

    if (result) {
        file_id = result.readAttribute("data-id");

        if (!button || button.up(".result-action-info")) {
            toggle(result.down(".result-action-info .button"), result, "result-expanded");
            stop_event = true;
        } else if (button.up(".result-hate")) { // TIENE que ir antes que love
            if (toggle(button, null, null, "on")) {
                voteFile(file_id, result.readAttribute("data-server"), 0);
                toggle(result.down(".result-love > .button"), null, null, "off");
            }
        } else if (button.up(".result-love")) {
            if (toggle(button, null, null, "on")) {
                voteFile(file_id, result.readAttribute("data-server"), 1);
                toggle(result.down(".result-hate > .button"), null, null, "off");
            }
        } else if (button.up(".result-action-report")) {
            toggle(button, report, "js-show", "");
            if (report.hasClassName("js-show")) {
                var buttonPos = Element.cumulativeOffset(button);
                report_file_id.value = file_id;
                report.button = button;
            }
            stop_event = true;
        }
    }
}

function toggle(button, parent, className, force){
    if (button.hasClassName("button-off") && force!="off") {
        button.addClassName("button-on").removeClassName("button-off");
        if (parent) parent.addClassName(className);
    } else if (button.hasClassName("button-on") && force!="on") {
        button.addClassName("button-off").removeClassName("button-on");
        if (parent) parent.removeClassName(className);
    } else {
        return false; // no ha hecho nada
    }
    return true;
}

function sendReport(){
    if (report_request) return;
    report_request = new Ajax.Request('complaint', {
        method: 'post',
        parameters: report_form.serialize(true),
        onSuccess: function(transport) {
            result = eval(transport.responseText);
            if (result===true) {
                clearReport();
                alert("Your complaint has been sent.");
            } else if (result===false) {
                clearReport();
                alert("Error!");
            } else {
                var wrongs = [false, false, false];
                result.each(function(item){
                    var field = $(item);
                    field.addClassName("wrong");
                    if (item=="email" && field.getValue().length>0)
                        wrongs[1]=true;
                    else if (item=="accept_tos")
                        wrongs[2]=true;
                    else
                        wrongs[0]=true;
                    });
                var message="";
                for (var i=0;i<3;i++)
                    if (wrongs[i]) message+=VALIDATION_MESSAGES[i];
                alert(message);
            }
            report_request = null;
        },
        onFailure: function(transport) {
            clearReport();
            alert(ERROR_MESSAGE + " " + EMAIL_REQUEST);
            report_request = null;
        }
    });
}

function clearReport(){
    report_form.reset();
    $$("#report .wrong").each(function(item){item.removeClassName("wrong")});
    toggle(report.button, report, "js-show", "off");
    report.button = false;
}

function voteFile(file_id, server, vote){
    if (vote_request) return;
    vote_request = new Ajax.Request('vote', {
        method: 'post',
        parameters: {"file_id":file_id, "server":server, "vote":vote, "_csrf_token":$F("_csrf_token")},
        onSuccess: function(transport) {
            result = eval(transport.responseText);
            if (!result) {
                alert(ERROR_MESSAGE);
            }
            vote_request = null;
        },
        onFailure: function(transport) {
            alert(ERROR_MESSAGE);
            vote_request = null;
        }
    });
}
