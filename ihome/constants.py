# 存储整个项目所有的变量

# 图片验证码的redis有效期, 单位：秒
IMAGE_CODE_REDIS_EXPIRES = 180

# 短信验证码的redis有效期, 单位：秒
SMS_CODE_REDIS_EXPIRES = 180

# 登录尝试的错误次数
LOGIN_ERROR_MAX_TIMES = 5

# 登录错误禁止时间
LOGIN_ERROR_FORBID_TIMES = 600

# 七牛域名
QINIU_URL_DOMAIN = "http://q9yp8h5ca.bkt.clouddn.com/"

# 城区信息的缓存时间，单位：秒
AREA_INFO_REDIS_CACHE_EXPIRES = 7200

# 首页房屋展示的最多数量
HOME_PAGE_MAX_HOUSES = 5

# 首页房屋数据redis缓存时间，单位：秒
HOME_PAGE_DATA_REDIS_EXPIRES = 7200

# 房屋详情页数据redis缓存时间。单位：秒
HOUSE_DETAIL_REDIS_EXPIRE_SECOND = 7200

# 房屋详情页展示的评论最大数
HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS = 30

# 房屋列表页查询每页展示的数量
HOUSE_LIST_PAGE_CAPACITY = 3

# 房屋列表页面页数缓存时间，单位：秒
HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRES = 7200

# 支付宝支付网关地址
ALIPAY_URL_PREFIX = "https://openapi.alipaydev.com/gateway.do?"
