function test_merge_request() {
    console.log('test merge request');
    var checkedCases = $('input[name="cb_case"]:checked').map(function () {
        return this.value;
    }).get();

    if (checkedCases.length == 0) {
        toastr.warning("Choose at least one test case");
    }
    else {
        $("#case_container").empty();
        checkedCases.forEach(function(element){
            var caseName = "<label class=\"col-sm-4 control-label\">" + element + "</label>"
            var li = "<div class=\"form-group\">" + caseName + "<div class=\"col-sm-2\"><input type=\"number\" value=\"1\" min=\"1\" class=\"form-control\"></div></div>"
            $('#case_container').append(li);
        });
        if ($("#tbody_merge_request td").length == 2) {
            insert_merge_request();
        }
        $("#modalMergereq").modal();
    }
}

function insert_merge_request(info) {
    $.get("./bisects/",function(data, status){
        $.each(data.merge_requests, function(index, val){
            console.log(val);
            $("<tr><td>" + val + "</td></tr>").insertAfter("#tr_merge_request")
        });
    });
}