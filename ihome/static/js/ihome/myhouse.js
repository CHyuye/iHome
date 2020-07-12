$(document).ready(function(){
    // 对于发布房源，首先确定其是否登录，实名认证
    $.get("/api/v1.0/users/auth", function (resp) {
        if (resp.errno == "4101") {
            // 用户未登录
            location.href = "/login.html"
        } else if (resp.errno == "0") {
            // 用户登录，返回进行实名认证，显示“去认证”按钮
            if (!resp.data.real_name && resp.data.id_card) {
                $(".auth-warn").show();
                return
            }
        }

    });

    // 已实名认证的请求房源信息
    $.get("/api/v1.0/user/houses", function (resp) {
        if (resp.errno == "0") {
            $("#houses-list").html(template("houses-list-tmpl", {houses: resp.data.houses}))
        } else {
            $("#houses-list").html(template("houses-list-tmpl", {houses: []}))
        }

    })
});