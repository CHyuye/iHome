function showSuccessMsg() {
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){}); 
        },1000) 
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function () {
    $("#form-avatar").submit(function (e) {
        // 阻止表单的默认行为
        e.preventDefault();
        // 使用jquery.form.min.js提供的ajaxSubmit对表单进行异步提交
        $(this).ajaxSubmit({
            url: "api/vi.0/users/avatar",
            type: "post",
            dataType: "json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (resp) {
                if (resp == "0") {
                    // 上传成功
                    var avatarURL = resp.data.avatar_url;
                    $("#user-avatar").attr("src", avatarURL);
                } else {
                    alert(resp.errmsg);
                }
            }
        })
    });

    // 修改用户名
    $("#form-name").submit(function (e) {
        // 阻止表单的默认行为
        e.preventDefault();
        // 获取用户名
        var name = $("#user-name").val();
        // 判断用户名是否为空
        if (!name){
            alert("用户名不能为空！");
            return
        }

        // ajax 提交修改后用户名
        $.ajax({
            url: "/api/v1.0/users/name",
            data: JSON.stringify({"name": name}),
            type: 'PUT',
            contentType: "applications/json",
            dataType: "json",
            headers:{
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (data) {
                if (data == '0'){
                    $('.error-msg').hide();
                    showSuccessMsg();
                } else if(data.errno == '4001'){
                    $('.error-msg').show();
                } else if(data.errno == '4101'){
                    location.href = "/login.html";
                }

            }
        })

    })
});

// 显示个人信息，如果没设置则，不显示
$.get("/api/v1.0/user", function (resp) {
    // 判断用户是否登录,跳转到login页面
    if (resp.errno == '4101') {
        location.href = "/login.html";
    } else if (resp.errno == '0') {
        $("#user-name").val(resp.data.name);
        if (resp.data.avatar){
            $("#user-avatar").attr('src', resp.data.avatar);
        }
    }
})