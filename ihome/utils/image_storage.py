from qiniu import Auth, put_data, etag

# 需要填写你的 Access Key 和 Secret Key
access_key = 'CW-q2Y2c7q9DqJZ9CSvIu2-yZOBwwti6nHQghzn2'
secret_key = 'znPBGzXQLnrbX6miMbZgf_GOrbmAWBdHpHuOjSYI'


def storage(file_data):
	"""
	上传文件到七牛云
	:param file_data:要上传的文件数据
	:return:
	"""

	# 构建鉴权对象
	q = Auth(access_key, secret_key)

	# 要上传的空间
	bucket_name = 'ihome1234'

	# 上传后保存的文件名
	# key = 'my-python-logo.png'

	# 生成上传 Token，可以指定过期时间等
	token = q.upload_token(bucket_name, None, 3600)

	# 要上传文件的本地路径
	# localfile = './sync/bbb.jpg'

	ret, info = put_data(token, None, file_data)
	print(info)
	print("*" * 20)
	print(ret)


if __name__ == '__main__':
	with open('./13.png', 'rb') as f:
		file_data = f.read()
	storage(file_data)
