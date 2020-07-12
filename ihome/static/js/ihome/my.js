// js读取cookie的方法
function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    // r ? r[1] : undefined 如果r为真，返回r[1]值，否则返回undefined未定义
    return r ? r[1] : undefined;
}

// 点击退出按钮是执行的函数
function logout() {
    $.ajax({
        url: "/api/v1.0/session",
        headers: {
            "X-CSRFToken": getCookie("csrf_token")
        },
        dataType: "json",
        success: function (resp) {
            if ("0" == resp.errno){
                location.href = "/index.html";
            }
        }
    })
}

$(document).ready(function(){
    $.get("/api/v1.0/user", function (resp) {
        // 判断用户是否登录，4101表示未登录
        if (resp.errno == "4101") {
            location.href = "/index.html";
        } else if (resp.errno == "0") {
            // 查找数据，显示到前台
            $('#user-name').html(resp.data.name);
            $('#user-mobile').html(resp.data.mobile);
            if (resp.data.avatar) {
                $('#user-avatar').attr('src', resp.data.avatar);
            }
        }
    })
    
});