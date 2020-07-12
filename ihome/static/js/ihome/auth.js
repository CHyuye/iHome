function showSuccessMsg() {
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){}); 
        },1000) 
    });
}

$(document).ready(function () {
    // 查询用户实名信息
    $.get('/api/v1.0/users/auth', function (resp) {
        if (resp.errno == "4101"){
            // 用户未登录
            location.href = "/login.html";
        } else if(resp.errno == "0") {
            // 用户已登录，如果real_name和id_card不为空，表示用户用填写信息
            if (resp.data.real_name && resp.data.id_card) {
                // 将实名信息填写到页面中，并不再允许修改，同时隐藏按钮
                $("#real-name").val(resp.data.real_name);
                $("#id-card").val(resp.data.id_card);
                $("#real-name").prop('disabled', true);
                $("#id_card").prop('disabled', true);
                $("#form-auth>input[type=submit]").hide();
            }
        } else {
            alert(resp.errmsg);
        }
    }. json);

    // 用户实名信息提交行为
    $("#form-auth").submit(function (e) {
        // 阻止提交默认行为
        e.preventDefault();
        // 获取用户实名信息
        var real_name = $("#real-name").val();
        var id_card = $("#id-card").val();
        // 判断用户信息是否为空
        if (real_name == "" || id_card == "" ){
            $(".error-msg").show();
        }

        // 将数据转换为json格式向后端发送
        var data = {
            "real_name": real_name,
            "id_card": id_card
        };

        var json_data = JSON.stringify(data);

        // ajax提交，保存实名信息
        $.ajax({
            url: "/api/v1.0/users/auth",
            data: json_data,
            dataType: "json",
            type: "post",
            contentType: "application/json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (resp) {
                if (resp.errno == '0') {
                    $('.error-msg').hide();
                    // 显示保存成功的信息
                    showSuccessMsg();
                    $("#real-name").prop("disabled", true);
                    $("#id-card").prop("disabled", true);
                    $("#form-auth>input[type=submit]").hide();
                } else {
                    alert(resp.errmsg);
                }
            }

        })

    })
})




