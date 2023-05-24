function updateParamList(object, table_param, chk_param, fields_update, url){
    const loader = $('.loader-wrapper');

    $(object).change(function(){
        var frm = $(table_param).serialize();
        var chk = $(chk_param).serialize();
        var data = frm +'&' + chk

        loader.css('display', 'flex');

        $.ajax({
            url: url,
            data: data,
            dataType: 'html',
            success: function(data) {
            loader.hide();
            $(fields_update).html(data);
//            $(fields_update).html(data['form'])
            }
          });
        });
    }

function senderFunction(url) {
    var frm = $('#parameters-form');

    const loader = $('.loader-wrapper').css('display', 'flex');

    $.ajax({
        url: url,
        data: frm.serialize(),
        dataType: 'json',
        success: function (data) {
            loader.hide();
            alert(data["messages"]);
            $("#forces-table tbody").html(data['html']);
            $("#load-to-file").load(data['load_to_file']);
        },
        error: function (data) {
            loader.hide();
//            console.log(data);
            alert(data.status + "\n" + data.responseJSON.error);
            $("#added-fields").html(data.responseJSON.form);
        }
      });
    }

function postFunction(url, obj) {
   event.preventDefault();

   const loader = $('.loader-wrapper').css('display', 'flex');

   alert("данные отправлены на сервер");
   var formData = new FormData(obj);
   $.ajax({
       type: 'POST',
       url: url,
       data: formData,
       success: function (data) {
            loader.hide();
            alert(data["messages"]);
            $("#added-fields").html(data);
            $("#added-fields").html(data['form']);
            $("#forces-table tbody").html(data['html']);
            $("#load-to-file").load(data['load_to_file']);
           },
       error: function (data) {
            loader.hide();
            alert(data.status + "\n" + data.responseJSON.error);
            $("#added-fields").html(data.responseJSON.form);
            },
       cache: false,
       contentType: false,
       processData: false
   });
}

