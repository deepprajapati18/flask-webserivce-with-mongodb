# -*- coding: utf-8 -*-
"""
Created on Tue Oct 30 13:20:32 2018

@author: Dell
"""

from __future__ import unicode_literals
import os
import re
from flask import Flask, jsonify, request, render_template, redirect, url_for
from flask_bcrypt import Bcrypt
from flask_pymongo import PyMongo
from flask_cors import CORS, cross_origin
from bson.json_util import dumps
from PIL import Image
# from bson.objectid import ObjectId
import base64
import uuid
from flask_paginate import Pagination, get_page_args

# forms that imported
from forms import ChangePassword

#import statement for email purpose
import smtplib
from string import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



app = Flask(__name__, static_url_path='/static')
app.config.from_pyfile('app.cfg')
app.config['MONGO_DBNAME'] = 'crud_mongo'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/crud_mongo'
app.config['CORS_HEADERS'] = 'Content-Type'

mongo = PyMongo(app)
CORS(app)

#secret key use in register and login page
app.config['SECRET_KEY'] = 'a949a7e106e03e256b1d8d3c59f5b6b0'
bcrypt = Bcrypt(app) #pass app to that bcrypt class to intialize that


PROJECT_HOME = os.path.dirname(os.path.realpath(__file__))
UPLOAD_FOLDER = '{}/static/images/'.format(PROJECT_HOME)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#image url path
default_image_path = "static/images/"
img_path = "http://127.0.0.1:5000/static/images/"



@app.route("/user/register", methods=["POST"])
def register():
	try:
		user_id = 1
		user = mongo.db.users
		
		user_data = user.find().sort("_id", -1).limit(1)
		for a in user_data:
			user_id = a["_id"] + user_id
		
		username = request.json['username']
		email = request.json['email']
		password = request.json['password']

		# username = request.form.get('username')
		# email = request.form.get('email')
		# password = request.form.get('password')

		if not (username and email and password):
			return dumps({'status': 'error', "message":"Please enter proper field"})
		
		elif (user.find_one({"$or": [{"username":username}, {"email":email}]})):
			return dumps({'status': 'error', "message":"Username or email already exist"})
		
		elif not (re.match("\A(?P<name>[\w\-_.]+)@(?P<domain>[\w\-_]+).(?P<toplevel>[\w]+)\Z",email,re.IGNORECASE)):
			return dumps({'status': 'error', "message" : "Email is not valid"})       
		
		else:
			hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
			status = user.insert({'_id':user_id, 'username': username, 'email': email, 'password': hashed_password})
			print (user.find_one({'_id':user_id}))
			return dumps({'status': 'success', 'message' : 'Register Successfully'})
	
	except Exception:
		return dumps({'status': 'error', 'message' : str(Exception)})


@app.route('/user', methods=['GET'])
def get_all_users():
	try:
		user = mongo.db.users
		output = []
		for s in user.find({}, {"_id": 1, "username": 1, "email": 1, "password": 1}):
			output.append(s)
		return dumps({'status': 'success', 'message' : output})
	
	except Exception:
		return dumps({'status': 'error', 'message' : str(Exception)})


@app.route('/user/<int:user_id>', methods=['GET'])
def get_one_user(user_id):
	try:
		user = mongo.db.users
		output = user.find_one({'_id': user_id}, {"_id": 1, "username": 1, "email": 1, "password": 1})
		if output:
			return dumps({'status': 'success', 'message' : output})
		else:
			return dumps({'status': 'success', 'message' : 'No User Found'})
	
	except Exception:
		return dumps({'status': 'error', 'message' : str(Exception)})


# endpoint to update user
@app.route("/user/<int:user_id>", methods=["PUT"])
def user_update(user_id):
	try:
		user = mongo.db.users

		username = request.json['username']
		email = request.json['email']
		password = request.json['password']
		
		if not (username and email):
			return dumps({'status': 'error', "message":"Please enter proper field"})
		
		elif not (re.match("\A(?P<name>[\w\-_.]+)@(?P<domain>[\w\-_]+).(?P<toplevel>[\w]+)\Z",email,re.IGNORECASE)):
			return dumps({'status': 'error', "message" : "Email is not valid"})
		
		else:
			findquery = {"_id" : user_id}
			newquery = {"$set": {'username': username, 'email': email, 'password': password}}
			status = user.update_one(findquery, newquery)
			return dumps({'status': 'success', 'message' : 'update Successfully'})

	except Exception:
		return dumps({'status': 'error', 'message' : str(Exception)})


@app.route("/user/<int:user_id>", methods=["DELETE"])
def user_delete(user_id):
	try:
		user = mongo.db.users
		
		s = user.find_one({'_id': user_id}, {"_id": 1, "username": 1, "email": 1, "password": 1})
		if s:
			output = s
			
			d = user.delete_one({'_id': ObjectId(user_id)})
			return dumps({'status': 'success', 'message' : 'deleted', 'deleted_Item' : output})
		else:
			return dumps({'status': 'error', "message" : "No such Username"})
		
	except Exception:
		return dumps({'status': 'error', 'message' : str(Exception)})


@app.route("/user/login", methods=["POST"])
def login():
	try:
		user = mongo.db.users

		email = request.json['email']
		password = request.json['password']

		if not (email and password):
			return dumps({'status': 'error', "message":"Please enter proper field"})
		elif not (re.match("\A(?P<name>[\w\-_.]+)@(?P<domain>[\w\-_]+).(?P<toplevel>[\w]+)\Z",email,re.IGNORECASE)):
			return dumps({'status': 'error', "message" : "Email is not valid"})
		else:
			user_email = user.find_one({'email': email}, {"_id":0, "email":1})
			if user_email:
				user_password = user.find_one({'email': email}, {"_id":0, "password":1})
				if bcrypt.check_password_hash(user_password.get("password"), password):
					return dumps({'status': 'success','message':'login Successfull'})
				else:
					return dumps({'status': 'error', 'message': 'Invalid Password'})
			else:
				return dumps({'status': 'error', 'message':'You are not Registerd'})
	
	except Exception:
		return dumps({'status': 'error', 'message' : str(Exception)})


#email portion
MY_ADDRESS = "<YOUR EMAIL ID>"
PASSWORD = '<YOUR PASSWORD>'


def read_template(filename):
	"""
	Returns a Template object comprising the contents of the 
	file specified by filename.
	"""
	
	with open(filename, 'r', encoding='utf-8') as template_file:
		template_file_content = template_file.read()
		print (template_file_content)
	return Template(template_file_content)


@app.route("/user/forgot", methods=["POST"])
def forgot():
	try:
		user = mongo.db.users

		email = request.json['email']

		if not (email):
			return dumps({'status': 'error', "message":"Please enter proper field"})
		elif not (re.match("\A(?P<name>[\w\-_.]+)@(?P<domain>[\w\-_]+).(?P<toplevel>[\w]+)\Z",email,re.IGNORECASE)):
			return dumps({'status': 'error', "message" : "Email is not valid"})
		else:
			user_email = user.find_one({'email': email}, {"_id":0,"username":1, "email":1})
			if user_email:
				
				#sending email portion
				name, email = user_email.get("username"), user_email.get("email")  # read contacts
				message_template = read_template('message.txt')
				
				# set up the SMTP server
				s = smtplib.SMTP(host='smtp.gmail.com', port=587)
				s.starttls()
				s.login(MY_ADDRESS, PASSWORD)
				
				# For each content, send the email:
				msg = MIMEMultipart()
				
				# add in the actual person name to the message template
				message = message_template.substitute(PERSON_NAME=name.title(), RESET_LINK = "http://127.0.0.1:5000/user/reset_password/"+email)
				
				# setup the parameters of the message
				msg['From']=MY_ADDRESS
				msg['To']=email
				msg['Subject']="Reset Password Link"
				
				# add in the message body
				msg.attach(MIMEText(message, 'plain'))
				
				# send the message via the server set up earlier.
				s.send_message(msg)
				del msg
				
				# Terminate the SMTP session and close the connection
				s.quit()
				return dumps({'status': 'success', "message" : "Password reset link is send to your mail"})
			
			else:
				return dumps({'status': 'error', 'message':'Invalid Email-ID'})
	except Exception:
		return dumps({'status': 'error', 'message' : str(Exception)})


@app.route("/user/reset_password/<email>", methods=['POST','GET'])
def reset_password(email):
	try:
		user = mongo.db.users

		form = ChangePassword()
		if form.validate_on_submit():
			new_password = request.form['change_password']
			hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
			findquery = {"email" : email}
			newquery = {"$set": {'password': hashed_password}}
			status = user.update_one(findquery, newquery)
			return "<h1>Successfully Changed</h1>"
		else:
			return render_template('reset_password.html', form = form, email = email)

	except Exception:
		return dumps({'status': 'error', 'message' : str(Exception)})


# portion of Image operation with base-64

# here _id is taken number for output purpose
@app.route('/user/img_upload', methods=['POST'])
def img_upload():
	try:
		user_id = 1
		
		user = mongo.db.users

		user_data = user.find().sort("_id", -1).limit(1)
		for a in user_data:
			user_id = a["_id"] + user_id

		if request.json['image_file']:
			
			image_file = request.json['image_file']
			
			#random file name with folder name
			f_name = str(uuid.uuid4()) + ".png"
			store_file = default_image_path + f_name
			# print(f_name)
			
			#for storing the image, fname is name of the image
			fh = open(store_file, "wb")
			fh.write(base64.b64decode(image_file + '='))
			fh.close()
			
			store_image = {'_id':user_id, "image_file" : f_name}
			x = user.insert(store_image)
			return dumps({'filename':f_name})
		
		else:
			return dumps({'status': 'error', 'message':'Please select an Image'})

	except Exception:
		return dumps({'status': 'error', 'message' : str(Exception)})


"""
Note: if  there are no keyword like image_file in any document
then it gives an error
so first remove the document that you practice on register
"""

@app.route('/user/img_get', methods=['GET'])
def img_get():
	try:
		user = mongo.db.users
		
		output = []
		for s in user.find({},{"_id": 0, "image_file" : 1}):
			img_url = img_path + s["image_file"]
			output.append(img_url)
		return dumps({'status': 'success', 'result' : output})

	except Exception:
		return dumps({'status': 'error', 'message' : str(Exception)})


@app.route("/user/img_update/<int:user_id>", methods=["PUT"])
def img_update(user_id):
	try:
		if request.json['image_file']:
			user = mongo.db.users

			s = user.find_one({'_id': user_id}, {"_id": 1, "image_file": 1})
			os.remove(default_image_path + s["image_file"])
			
			image_file = request.json['image_file']
			#random file name with folder name
			f_name = str(uuid.uuid4()) + ".png"
			store_file = default_image_path + f_name
			
			#for storing the image, fname is name of the image
			fh = open(store_file, "wb")
			fh.write(base64.b64decode(image_file))
			fh.close()
			
			#update image
			findquery = {"_id" : user_id}
			newquery = {"$set": {'image_file': f_name}}
			status = user.update_one(findquery, newquery)
			
			return dumps({'status': 'success', 'message' : 'Item Updated'})
		
		else:
			return dumps({'status': 'error', 'message':'Please select an Image'})

	except Exception:
		return dumps({'status': 'error', 'message' : str(Exception)})


@app.route("/user/img_delete/<int:user_id>", methods=["DELETE"])
def img_delete(user_id):
	try:
		user = mongo.db.users
		
		s = user.find_one({'_id': user_id}, {"_id": 1, "image_file": 1})
		
		if s:
			output = s
			os.remove(default_image_path + s["image_file"])
		
			d = user.delete_one({'_id': user_id})
			return dumps({'status': 'success', 'message' : 'Item Deleted', 'deleted_Item' : output})

		else:
			return dumps({'status': 'error', 'message': 'Image not Found'})
	
	except Exception:
		return dumps({'status': 'error', 'message' : str(Exception)})
	
# base64 image portion ends now okay


# image operation without base64
@app.route('/user/mul_img_upload', methods=['POST'])
def mul_img_upload():
	try:
		user_id = 1

		user = mongo.db.users
		
		user_data = user.find().sort("_id", -1).limit(1)
		for a in user_data:
			user_id = a["_id"] + user_id
		
		if request.files['image_file']:
			image_file = request.files['image_file']
			extension = os.path.splitext(image_file.filename)[1]
			print (image_file.filename)
		
			if extension == ".jpg" or extension == ".png" or extension == ".jpeg":
				
				f_name = str(uuid.uuid4()) + ".png"
			
				"""
				#method 1 : for storing image
				#for optimizing the image size
				picture_path = os.path.join(app.root_path, 'static/profile_pics', f_name)
				output_size = (125, 125)
				i = Image.open(image_file)
				i.thumbnail(output_size)
				i.save(picture_path)
				"""
				
				output_size = (100, 100)
				i = Image.open(image_file)
				i.thumbnail(output_size)
				#method 2 : for storing the image
				#save image in folder, second argument is file name
				i.save(os.path.join(app.config['UPLOAD_FOLDER'], f_name))
			
				store_image = {'_id':user_id, "image_file" : f_name}
				x = user.insert(store_image)
				return dumps({'filename':f_name})
		
			else:
				return dumps({'status': 'success', 'message' : 'Item added'})
		else:
			return dumps({'status': 'error', 'message': 'Please select an Image file'})
	
	except Exception:
		return dumps({'status': 'error', 'message':'Exception'})


@app.route('/user/mul_img_get', methods=['GET'])
def mul_img_get():
	try:
		user = mongo.db.users
		
		output = []
		for s in user.find({},{"_id": 0, "image_file" : 1}):
			img_url = img_path + s["image_file"]
			output.append(img_url)
		return dumps({'status': 'success', 'result' : output})

	except Exception:
		return dumps({'status': 'error', 'message':'Exception'})

# multipart portion ends


#pagination start

'''Note You can change the pagination from app.cfg file which is added upper'''
def get_pagination(**kwargs):
	kwargs.setdefault('record_name', 'records')
	return Pagination(**kwargs)


# ?page=1 add forward to this url to get the result
@app.route('/user/pagination/', methods=['GET'])
def pagination():
	try:
		user = mongo.db.users
		
		total = user.count()
		
		page, per_page, offset = get_page_args(page_parameter='page',
											   per_page_parameter='per_page')
		users = []
		for i in user.find({},{'_id': 0,'username': 1}).skip(offset).limit(per_page):
			value = i['username']
			users.append(value)

		if users:
			pagination = get_pagination(page=page,
										per_page=per_page,
										total=total,
										record_name='username',
										format_total=True,
										format_number=True,
										)
			length_of_pages = len(pagination.pages)
			print (length_of_pages)
			print (pagination.links)

			return dumps({'status': 'success', 'message' : 'Page Changed', 'Users': users})
		else:
			return dumps({'status': 'error', 'message' : 'Sorry Page Not Found'})
		
	except Exception:
		return dumps({'status': 'error', 'message':'Exception'})


if __name__ == '__main__':
	app.run(debug= True)
