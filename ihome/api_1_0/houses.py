from . import api
from ihome.utils.commons import login_required
from flask import g, request, jsonify, current_app, session
from ihome.utils.response_code import RET
from ihome.models import Area, House, Facility, HouseImage, User, Order
from ihome import db, constants, redis_store
from ihome.utils.image_storage import storage
import json
from datetime import datetime


@api.route("/areas", methods=["GET"])
@login_required
def get_area_info():
	"""
	获取城区信息 —— 使用redis缓存机制,保存基本城区信息，（因为城区信息基本不变，使用缓存减少时间）
	1.先尝试从redis中获取数据
	2.如果redis中有数据，就直接返回给前端
	3.如果redis中没有数据，去MySQL中查询数据，拿到数据后保存到redis中，再返回个前端

	重点二：缓存数据的同步问题——保证mysql与redis的数据一致相同
	1.在操作mysql的时候，删除redis缓存数据 【不提倡】
	2，给redis缓存数据设置有效期，保证过了有效期，缓存数据被删除，从mysql中重新读取数据
	:return:
	"""
	# 先尝试葱redis中获取数据
	try:
		resp_json = redis_store.get("area_info")
	except Exception as e:
		current_app.logger.error(e)
	else:
		if resp_json is not None:
			current_app.logger.info("hit redis area_info")
			return resp_json, 200, {"Content-Type": "application/json"}

	# 查询数据库，读取城区信息
	try:
		area_li = Area.query.all()
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="数据库获取异常")

	area_dict_li = []
	# 遍历取出，将对象转换为字典
	for area in area_li:
		area_dict_li.append(area.to_dict)

	# 将json数据转换为字典
	resp_dict = dict(errno=RET.OK, errmsg="OK", data=area_dict_li)
	resp_json = json.dumps(resp_dict)

	# 将数据缓存进redis
	try:
		# 给redis缓存数据设置有效期，保证过了有效期，缓存数据被删除，从mysql中重新读取数据
		redis_store.setex("area_info", constants.AREA_INFO_REDIS_CACHE_EXPIRES, resp_json)
	except Exception as e:
		current_app.logger.error(e)

	# 返回结果
	return resp_json, 200, {"Content-Type": "application/json"}


@api.route("/house/info", methods=["POST"])
@login_required
def save_house_info():
	"""
	保存房屋的基本信息
	前端发送过来的json数据
		{
			"title":"",
			"price":"",
			"area_id":"1",
			"address":"",
			"room_count":"",
			"acreage":"",
			"unit":"",
			"capacity":"",
			"beds":"",
			"deposit":"",
			"min_days":"",
			"max_days":"",
			"facility":["7","8"]
		}
	:return:
	"""
	# 获取数据
	house_data = request.get_json()
	user_id = g.user_id  # g对象获取user的id

	title = house_data.get("title")  # 房屋的名称标题
	price = house_data.get("price")  # 房屋单价
	area_id = house_data.get("area_id")  # 房屋所属的地区编号
	address = house_data.get("address")  # 房屋地址
	room_count = house_data.get("room_count")  # 房屋包含的房间数目
	acreage = house_data.get("acreage")  # 房屋面积
	unit = house_data.get("unit")  # 房屋布局（几室几厅)
	capacity = house_data.get("capacity")  # 房屋容纳人数
	beds = house_data.get("beds")  # 房屋卧床数目
	deposit = house_data.get("deposit")  # 押金
	min_days = house_data.get("min_days")  # 最小入住天数
	max_days = house_data.get("max_days")  # 最大入住天数

	# 检验参数完整
	if not all([title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
		return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

	# 检验金额是否正确
	try:
		price = int(float(price) * 100)  # 房屋单价
		deposit = int(float(deposit) * 100)  # 押金
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

	# 判断城区id是否存在
	try:
		area = Area.query.get(area_id)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="数据库异常")

	if area is None:
		return jsonify(errno=RET.NODATA, errmsg="城区信息错误")

	# 保存房屋信息
	house = House(
		user_id=user_id,
		area_id=area_id,
		title=title,
		price=price,
		address=address,
		room_count=room_count,
		acreage=acreage,
		unit=unit,
		capacity=capacity,
		beds=beds,
		deposit=deposit,
		min_days=min_days,
		max_days=max_days
	)

	# 处理房屋设施信息
	facility_ids = house_data.get("facility")

	# 如果用户勾选了，再保存进数据库
	if facility_ids:
		# 过滤用户勾选设施信息，["7", "8"]
		try:
			# select * from ih_facility_info where id in []
			facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
		except Exception as e:
			current_app.logger.error(e)
			return jsonify(errno=RET.DBERR, errmsg="数据库异常")

		# 表示有合法设施数据
		if facilities:
			# 保存设施数据
			house.facilities = facilities

	# 数据库统一保存,保持事务的一致性
	try:
		db.session.add(house)
		db.session.commit()
	except Exception as e:
		db.session.rollback()
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

	# 保存成功，返回结果
	return jsonify(errno=RET.OK, errmsg="OK")


@api.route("/houses/image", methods=["POST"])
@login_required
def save_house_image():
	"""
	保存房屋的图片
	参数：图片，房屋id
	:return:
	"""
	# 获取参数
	image_file = request.files.get("house_image")
	house_id = request.form.get("house_id")

	# 检验参数完整性
	if not all([image_file, house_id]):
		return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

	# 判断房屋信息正确性
	try:
		house = House.query.get(house_id)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="数据库异常")

	if not house:
		return jsonify(errno=RET.NODATA, errmsg="房屋信息不存在")

	# 上传图片到七牛云
	image_data = image_file.read()
	try:
		file_name = storage(image_data)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.THIRDERR, errmsg="上传图片失败")

	# 保存图片信息到数据库
	house_image = HouseImage(house_id=house_id, url=file_name)
	db.session.add(house_image)

	# 在models的House有一个主图片需要处理
	if not house.index_image_url:
		# 如果主图为空
		house.index_image_url = file_name
		db.session.add(house)

	# 数据库提交
	try:
		db.session.commit()
	except Exception as e:
		db.session.rollback()
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="保存图片异常")

	# 拼接图片路径
	image_url = constants.QINIU_URL_DOMAIN + file_name

	# 返回结果
	return jsonify(errno=RET.OK, errmsg="OK", data={"image_url": image_url})


@api.route("/user/house", methods=["GET"])
@login_required
def get_user_houses():
	"""
	获取房东发布的房源信息
	:return:
	"""
	# 获取用户id
	user_id = g.user_id

	# 根据用户id查询用户发布的房源信息（返回对象）
	try:
		user = User.query.get(user_id)
		houses = user.houses
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="数据库获取异常")

	# 将每个房屋数据转换为字典，并放入列表中
	houses_li = []
	if houses:
		for house in houses:
			houses_li.append(house.to_basic_dict())

	# 返回结果
	return jsonify(errno=RET.OK, errmsg="OK", data={"houses": houses_li})


# 127.0.0.1:5000//api/v.1/houses/index
# GET
@api.route("/houses/index", methods=["GET"])
def get_houses_index():
	"""
	获取主页幻灯片展示的房屋基本信息（订单数最多的前五个）
	:return:
	"""
	# 先尝试从redis缓存中读取数据
	try:
		ret = redis_store.get("home_data_page")
	except Exception as e:
		current_app.logger.error(e)
		ret = None  # 一定要置为None
	# 有直接返回
	if ret:
		current_app.logger.error('hit home index info in redis')
		# 因为redis储存的是json数据，所以进行字符串的拼接
		return '{"errno": 0, "errmsg": OK, "data": %s}' % ret, 200, {"Content-Type": "application/json"}

	# 没有，查询，mysql数据库获取数据
	try:
		# 查询房屋订单数量最多的前五个
		houses = House.query.order_by(House.order_count.desc().limit(constants.HOME_PAGE_MAX_HOUSES))
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="数据库异常")

	if houses:
		return jsonify(errno=RET.NODATAm, errmsg="没有查询到数据")

	# 将数据转换为列表，添加到列表中
	houses_li = []
	for house in houses:
		# 如果房主为设置主图片，则跳过
		if not house.index_image_url:
			continue
		houses_li.append(house.to_basic_dict())

	# 将列表数据转换为json，存到redis缓存中
	houses_json = json.dumps(houses_li)
	try:
		redis_store.setex("home_data_page", constants.HOME_PAGE_DATA_REDIS_EXPIRES, houses_json)
	except Exception as e:
		# 记录一下日志即可
		current_app.logger.error(e)

	# 返回结果
	return '{"errno": 0, "errmsg": "OK", "data": %s}' % houses_json, 200, {"Content-Type": "application/json"}


# 127.0.0.1:5000/houses/<house_id>
# GET请求方式
@api.route("/houses/<int:house_id>", methods=["GET"])
def get_house_detail(house_id):
	"""获取房屋的详细信息"""
	# 前端在房屋详情页展示，如果浏览页面的不是该房屋的房东，则显示预定按钮，否则不展示
	# 所以需要后端返回user_id，尝试获取用户的user_id，若登录返回，若未登录返回user_id=-1
	user_id = session.get("user_id", "-1")

	# 检验house_id参数
	if not house_id:
		return jsonify(errno=RET.PARAMERR, errmsg="参数出错")

	# 从redis数据库中获取数据
	try:
		ret = redis_store.get("house_info_%s" % house_id)
	except Exception as e:
		current_app.logger.error(e)
		ret = None  # 出错时，将ret置为None
	# redis存在数据
	if ret:
		current_app.logger.info("hit house info in redis")
		return '{"errno": 0, "errmsg": "OK", "data": {"user_id": %s, "house": %s}}' % (user_id, ret), \
			   200, {"Content-Type": "application/json"}

	# 如果redis中不存在数据，则从数据库中读取数据插入redis
	try:
		house = House.query.get(house_id)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="数据库查询异常")

	# 检验房屋是否存在
	if not house:
		return jsonify(errno=RET.NODATA, errmsg="数据不存在")

	# 将房屋对象转换为字典
	try:
		house_data = house.to_full_dict()
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DATAERR, errmsg="数据出错")

	# 转换为json格式，存入redis中
	house_json = json.dumps(house_data)
	try:
		redis_store.setex("house_info_%s" % house_id, constants.HOUSE_DETAIL_REDIS_EXPIRE_SECOND, house_json)
	except Exception as e:
		current_app.logger.error(e)

	resp = '{"errno": 0, "errmsg": "OK", "data": {"user_id": %s, "house": %s}' % (user_id, house_json), \
		   200, {"Content-Type": "application/json"}
	return resp


# GET /api/v1.0/houses?sd=2017-12-01&ed=2017-12-31&aid=10&sk=new&p=1
@api.route("/houses")
def get_house_list():
	"""获取房屋的列表信息（搜索页面）"""
	start_date = request.args.get("sd", "")  # 用户想要起始时间
	end_date = request.args.get("ed", "")  # 用户想要的结束时间
	area_id = request.args.get("aid", "")  # 区域编号
	sort_key = request.args.get("sk", "new")  # 排序关键字, 默认排序为new
	page = request.args.get("p")  # 分页页数

	# 参数判断——处理时间
	try:
		if start_date:
			# 将时间字符串转换为时间类型  strftime（将时间类型转换为字符串）
			start_date = datetime.strptime(start_date, "%Y-%m-%d")

		if end_date:
			end_date = datetime.strptime(end_date, "%Y-%m-%d")

		if start_date and end_date:
			assert start_date <= end_date
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.PARAMERR, errmsg="日期参数错误")

	# 判断区域id
	if area_id:
		try:
			area = Area.query.get(area_id)
		except Exception as e:
			current_app.logger.error(e)
			return jsonify(errno=RET.DBERR, errmsg="区域参数有误")

	# 处理页数
	try:
		page = int(page)
	except Exception as e:
		current_app.logger.error(e)
		page = 1

	# 获取缓存数据
	redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
	try:
		resp_json = redis_store.hget(redis_key, page)
	except Exception as e:
		current_app.logger.error(e)
	else:
		if resp_json:  # 缓存数据存在
			return resp_json, 200, {"Content-Type": "application/json"}

	# 过滤条件参数列表容器
	filter_params = []

	# 填充过滤参数——时间条件
	conflict_orders = None

	try:
		if start_date and end_date:  # 都传了
			conflict_orders = Order.query.filter(Order.begin_data <= end_date, Order.end_data >= start_date).all()
		elif start_date:  # 传入起始时间
			conflict_orders = Order.query.filter(Order.end_data >= start_date).all()
		elif end_date:  # 传入结束时间
			conflict_orders = Order.query.filter(Order.begin_data <= end_date).all()
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="数据库异常")

	if conflict_orders:
		# 从订单中获取冲突的房屋id
		conflict_house_id = [order.house_id for order in conflict_orders]

		# 如果冲突的房屋id不为空，向查询参数添加条件
		filter_params.append(House.id.notin_(conflict_house_id))

	# 区域条件
	if area_id:
		filter_params.append(House.area_id == area_id)

	# 查询数据库——补充排序条件
	if sort_key == "booking":  # 入住最多
		house_query = House.query.filter(*filter_params).order_by(House.order_count.desc())
	elif sort_key == "price-inc":  # 价格 低->高
		house_query = House.query.filter(*filter_params).order_by(House.price.asc())
	elif sort_key == "price-des":  # 高->低
		house_query = House.query.filter(*filter_params).order_by(House.price.desc())
	else:  # 默认排序时间最新
		house_query = House.query.filter(*filter_params).order_by(House.create_time.desc())

	# 分页处理
	try:
		#                              当前页数       每页数据量                                 自动错误输出
		page_obj = house_query.paginate(page=1, per_page=constants.HOUSE_LIST_PAGE_CAPACITY, error_out=False)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="数据库异常")

	# 获取页面数据
	house_li = page_obj.items
	houses = []
	for house in house_li:
		houses.append(house.to_basic_dict())

	# 获取总页数
	total_page = page_obj.pages

	# 将结果转化为json字符串
	resp_dict = dict(errno=RET.OK, errmsg="OK", data={"total_page": total_page, "houses": houses, "current_page": page})
	resp_json = json.dumps(resp_dict)

	# 防止当用户访问页数超过总页数，出现多余的缓存
	if page <= total_page:
		# 设置缓存——缓存用户查询的页面数据
		# "house_起始_结束_区域id_排序_页数"
		redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
		try:
			# todo:redis管道需要多加熟悉！
			# 创建一个pipeline（管道）对象，可以一次性执行多个语句
			pipeline = redis_store.pipeline()

			# 开启多个语句的记录
			pipeline.multi()

			# 设置缓存类型——哈希  "1": "{}",
			pipeline.hset(redis_key, page, resp_json)
			pipeline.expire(redis_key, constants.HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRES)  # 设置缓存时间

			# 执行语句
			pipeline.execute()
		except Exception as e:
			current_app.logger.error(e)

	return resp_json, 200, {"Content-Type": "application/json"}

# redis_store
#
# "house_起始_结束_区域id_排序_页数"
# (errno=RET.OK, errmsg="OK", data={"total_page": total_page, "houses": houses, "current_page": page})
#
#
#
# "house_起始_结束_区域id_排序": hash
# {
#     "1": "{}",
#     "2": "{}",
# }
