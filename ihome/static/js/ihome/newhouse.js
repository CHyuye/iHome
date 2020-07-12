function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function(){
    // 向后端获取城区信息
    $.get("/api/v1.0/areas", function (resp) {
        if (resp.errno == "0") {
            var areas = resp.data;
            // for (i=0; i<areas; i++) {
            //     var area = area[i];
            //     $("#area-id").append('<option value="'+ area.aid +'">'+ area.aname +'</option>');
            // }

            // 使用js模板渲染城区信息参数
            var html = template("areas-tmpl", {areas: areas});
            // 把获取后的参数往指定为填充
            $("#area-id").html(html)
        }
        else {
            alert(resp.errmsg);
        }
    });

    // 向后端保存房屋基本信息
    $("#form-house-info").submit(function (e) {
        e.preventDefault();  // 阻止默认表单行为
        // 处理表单数据，提取出name和value值，使它们相对应
        var data = {};
        $("#form-house-info").serializeArray().map(function (x) { data[x.name] = x.value});

        // 收集设施id信息
        var facility = [];
        $(":checked[name=facility]").each(function (index, x) { facility[index] = $(x).val() });

        // 将设施信息填充到data数据中
        data.facility = facility;

        //向后端发送请求
        $.ajax({
            url: "/api/v1.0/houses/info",
            type: "post",
            contentType: "applications/json",
            dataType: "json",
            data: JSON.stringify(data),
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (resp) {
                if (resp.errno == "4101"){
                    // 用户未登录
                    location.href = "/login.html";
                } else if (resp.errno == "0") {
                    // 隐藏基本信息表单
                    $("#form-house-info").hide();
                    // 显示图片信息
                    $("#form-house-image").show();
                    // 设置图片表单中的house_id
                    $("#house-id").val(resp.data.house_id);
                } else {
                    alert(resp.errmsg);
                }

            }
        })
    });

    // 上传房屋图片到后端
    $("#form-house-image").submit(function (e) {
        e.preventDefault();
       $(this).ajaxSubmit({
           url: "/api/v1.0/houses/image",
           type: "post",
           dataType: "json",
           headers: {
               "X-CSRFToken": getCookie("csrf_token")
           },
           success: function (resp) {
               if (resp.errno == "4101") {
                   location.href = "/login.html";
               } else if (resp.errno == "0") {
                   // 添加图片的div下插入图片链接
                   $(".house-image-cons").append('<img src="' + resp.data.image_url + '">');
               } else {
                   alert(resp.errmsg);
               }
           }
       })

    })

})