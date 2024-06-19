var addFormData = (v, d) => {
    if (d.type == 'radio') {
        if ($(d).is(":checked")) {
            v[d.name] = $(d).val();
        }
        return
    }
    if (v[d.name] != undefined) {

        if (typeof v[d.name] == 'string' || typeof v[d.name] == 'number') {
            v[d.name] = [v[d.name], d.type == 'checkbox' ? ($(d).is(":checked") ? 1 : 0) : $(d).val()];

        } else {
            v[d.name].push(d.type == 'checkbox' ? ($(d).is(":checked") ? 1 : 0) : $(d).val());
        }
    } else {
        // console.log(d.name,$(d).val(), $(d).is(":checked"),$(d).val())
        v[d.name] = d.type == 'checkbox' ? ($(d).is(":checked") ? 1 : 0) : $(d).val();
    };
};
function reloadPage(delay = 0) {
    setTimeout(() => {
        window.location.reload();
    }, delay)
}
function getFormData(id) {

    var inputs = $('#' + id + ' :input');

    var values = {},
        key = $('#' + id).attr('data-cf-formkey');
    inputs.each(function () {
        var skip = $(this).parents('.skip-form').first();
        var sub = $(this).parents('.sub-form').first();
        if (skip.length != 0) {
            if (skip.attr('id') != id && skip.find('#' + id).length == 0) { //chcks if the skipform is not a parent of current form
                return;
            }
        }
        if (sub.length != 0) {
            if (sub.attr('id') != id && sub.find('#' + id).length == 0) {
                values[sub.attr('id')] = getFormData(sub.attr('id'));
                return;
            }
        }
        if ($(this).hasClass('key')) {
            return
        }
        if ($(this).attr('data-cf-setunder') != null) {
            if ($(this).val() != '') {
                if (values[$(this).attr('data-cf-setunder')] == undefined) {
                    values[$(this).attr('data-cf-setunder')] = {};
                }
                if (this.type == 'checkbox') {
                    addFormData(values[$(this).attr('data-cf-setunder')], this);
                } else if ($(this).tagName() == 'SELECT') {
                    if ($(this).val() != -1) {
                        addFormData(values[$(this).attr('data-cf-setunder')], this);
                    }
                } else {
                    addFormData(values[$(this).attr('data-cf-setunder')], this);
                }
            }
        } else if ($(this).val() != '') {
            if ($(this).hasClass('value')) {
                var key = $(this).parents('.key_value').first().find('.key').first().val();
                values[key] = $(this).val();
                return;
            }

            if (this.type == 'checkbox') {
                addFormData(values, this);
            } else if ($(this).tagName() == 'SELECT') {
                if ($(this).val() != -1) {
                    addFormData(values, this);
                }
            } else {
                addFormData(values, this);
            }
        }
    });
    if (key != undefined) {
        var v = {};
        v[key] = values;
        return v;
    }
    return values;
}
$(function () {
    jQuery.fn.tagName = function () {
        return this.prop("tagName");
    };
})
function error(str, title) {
    Swal.fire({
        title:
            (title == undefined ? "Error" : title)
        , html: str,
        icon: 'error'
    })
    // $("#alert").modal("show").find('.modal-content').addClass(
    //     "bg-danger").removeClass("bg-primary").find(
    //         '.modal-body').html(
    //             "<b>" + str + "</b>");
    // $('#alert').find('.title').html('<b>' + (title == undefined ? "Error" : title) + '</b>').addClass('text-white');
}
function success(str, title) {
    Success(str, title);
}
function Success(str, title) {
    Swal.fire({
        title:
            (title == undefined ? "Success!!" : title)
        , html: str,
        icon: 'success'
    })
    // $("#alert").modal("show").find('.modal-content').addClass(
    //     "bg-danger").removeClass("bg-primary").find(
    //         '.modal-body').html(
    //             "<b>" + str + "</b>");
    // $('#alert').find('.title').html('<b>' + (title == undefined ? "Error" : title) + '</b>').addClass('text-white');
}
function send(url, data, method) {
    return $.ajax({
        url: url,
        method: method,
        data: data
    });
}