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

$(function () {
    var color_classes = ['text-success', 'text-danger', 'text-primary'], i = 0;

    setInterval(function () {
        if (i != 0) {
            $('.spinner-border').removeClass(color_classes[i - 1])
        }
        $('.spinner-border').addClass(color_classes[i])
        if (i == color_classes.length - 1) {
            i = 0
        }
        i++;
    }, 20)
    $("#update-puppy-health").click(function (e) {
        var form = document.getElementById("check-puppy-health-form");

        if (form.checkValidity() === true) {
            var data = getFormData("check-puppy-health-form")
            console.log(data)
            $("#check-health-modal").modal("show")
            send("/api/update-puppy-health", data, "POST").done(function (result) {
                $("#check-health-modal").modal("hide")
                if (result && result.msg) {
                    if (result.status == "V") {
                        Swal.fire({
                            titleText: "Vertinary!",
                            text: result.msg,
                            iconHtml: '<i class="fa fa-bolt text-danger"></i>',
                            iconColor: 'red'
                        })
                    } else if (result.status == "M") {
                        Swal.fire({
                            title: "Monitor!",
                            text: result.msg,
                            icon: 'warning'
                        })
                    } else {
                        Success(result.msg, "Good")
                    }
                } else {
                    // Handle the case where result is an empty object or does not contain 'msg'
                    Success("All Good, Your Puppy is in good health!!");
                }
            }).fail(function (err) {
                $("#check-health-modal").modal("hide")
                error(`${err.responseText}`, err.statusText)
            })
        }
        $(form).addClass("was-validated");

    })
    $(".vertinary-update-yes").click(function () {
        var u = $(this).parents(".vertinary-update").first()
        u.find(".update-qtn,.vertinary-update-yes").addClass("visually-hidden")
        u.find(".review-date,.vertinary-update-done").removeClass("visually-hidden")
    })
    $(".vertinary-update-done").click(function () {
        var u = $(this).parents(".vertinary-update").first(),
            review_date = u.find(".review-date #review_date").val(),
            recommendation_id = u.find(".review-date #recommendation_id").val();
        if (review_date === '') {
            error("Please input the review date!");
        } else {
            send("/api/record_action", { recommendation_id: recommendation_id, review_date: review_date, action_taken: "Took puppy to vet" }, "POST").done(function (data) {
                Success("Thank you, we will notify you in this date, if the puppy didn't get well")
                u.hide()

            }).fail(function (err) {
                error("Error, can't update the server!");
            })
        }
    });
    $(".dismiss-recommendation").click(function () {
        var u = $(this).parents(".recommendation").first(),
            recommendation_id = u.find("#recommendation_id").val();
        send("/api/dismiss_recommendation", { recommendation_id: recommendation_id }, "POST").done(function (data) {

            u.hide()
        }).fail(function (err) {
            error("Error, failed to dismiss the recommendation!");
        })
    })
})