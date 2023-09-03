"""
    Title: LEET
    Module Name: server
    Author: Daljeet Singh Chhabra
    Language: Python
    Date Created: 22-03-2020
    Date Modified: 08-04-2020
    Description:
        ###############################################################
        ##  Controls the major backend functionality of LEET.
        ###############################################################
"""

from flask import Flask, request, jsonify, render_template
from flask_jwt_extended import (JWTManager, jwt_required, create_access_token, jwt_refresh_token_required,
                                create_refresh_token, get_jwt_identity)
from backend import (check_auth_login, register_auth_user, verify_usr_eml, user_role, add_staff, register_staff,
                     get_auth_user_details, dashboard_data, add_faculty, add_class, faculty_analysis)
from flask_cors import CORS
from datetime import timedelta, datetime
import os
import re

app = Flask(__name__)
jwt = JWTManager(app)
app.secret_key = os.urandom(24)
CORS(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh():
    current_user = get_jwt_identity()
    ret = {
        'access_token': create_access_token(identity=current_user)
    }
    return jsonify(ret), 200


@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('usr_name')
    password = request.json.get('usr_pwd')

    # Validating JSON
    if username == "" or password == "" or username is None or password is None:
        return jsonify({"msg": "Bad username or password"}), 401
    # Validating email
    if not re.search(r'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$', request.json.get('usr_name')):
        return jsonify({"msg": "Invalid Email address"}), 406

    uid = check_auth_login(username, password)
    if uid is None:
        return jsonify({"msg": "Bad username or password"}), 401
    if uid is 0:
        return jsonify({'msg': "Account locked due to multiple incorrect attempts. Please reset your password."}), 401
    # Using create_access_token() and create_refresh_token() to create access and refresh tokens
    ret = {
        'access_token': create_access_token(identity=uid, expires_delta=timedelta(minutes=15)),
        'refresh_token': create_refresh_token(identity=uid),
        'created_on': datetime.now(),
        'expires_in': str(timedelta(minutes=15))
    }
    return jsonify(ret), 200


@app.route('/registerAdmin', methods=['POST'])
def registerAdmin():
    if request.method == 'POST':
        eml = request.json.get('usr_eml')
        pwd = request.json.get('usr_pwd')
        fname = request.json.get('usr_fname')
        lname = request.json.get('usr_lname')
        org = request.json.get('usr_org')
        phone = request.json.get('usr_phone')

        # Checking empty values in JSON
        if eml == "" or pwd == "" or fname == "" or lname == "" or org == "" or phone == "":
            return jsonify({"msg": "Empty field received"}), 406
        # Checking for constraints
        if len(phone) > 10:
            return jsonify({"msg": "Invalid Phone Number"}), 406
        if not re.search(r'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$', eml):
            return jsonify({"msg": "Invalid Email address"}), 406

        if register_auth_user(usr_eml=eml, usr_fname=fname, usr_lname=lname, usr_pwd=pwd, usr_org=org, usr_phone=phone,
                              usr_type="admin"):
            return jsonify(True), 200
        else:
            return jsonify(False), 409


@app.route('/getUserInfo/<string:query>', methods=['POST'])
@jwt_required
def getUserInfo(query):
    uid = get_jwt_identity()
    details = None
    if query == 'name':
        details = get_auth_user_details(uid, q='name')
    elif query == 'all':
        details = get_auth_user_details(uid)
    return jsonify(details), 200


@app.route('/addStaff', methods=['POST'])
@jwt_required
def addStaff():
    uid = get_jwt_identity()
    if user_role(uid) is not "admin":
        return jsonify({'msg': "not authorized to perform the task"}), 401

    hods_data = request.json.get('hod')['data']
    org = request.json.get('hod')['org']
    for hod in hods_data:
        eml = hod['hod_eml']
        dep = hod['hod_dep']

        # Checking empty values in JSON
        if eml == "" or dep == "":
            return jsonify({'msg': "Received Null values"}), 406
        # Checking for constraints
        if not re.search(r'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$', eml):
            return jsonify({"msg": f"Invalid Email address: {eml}"}), 406

        resp = add_staff(uid, eml, dep, org)
        if resp is False:
            return jsonify({"msg": "One or more user already Exist"}), 406
    return jsonify(True), 200


@app.route('/registerStaff', methods=['POST'])
def registerStaff():
    eml = request.json.get('usr_eml')
    pwd = request.json.get('usr_pwd')
    fname = request.json.get('usr_fname')
    lname = request.json.get('usr_lname')
    phone = request.json.get('usr_phone')

    # Checking empty values in JSON
    if eml == "" or pwd == "" or fname == "" or lname == "" or phone == "":
        return jsonify({"msg": "Empty field received"}), 406
    # Checking for constraints
    if len(phone) > 10:
        return jsonify({"msg": f"Invalid Phone Number: {phone}"}), 406
    if not re.search(r'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$', eml):
        return jsonify({"msg": f"Invalid Email address: {eml}"}), 406

    resp = register_staff(usr_fname=fname, usr_lname=lname, usr_eml=eml, usr_phone=phone, usr_pwd=pwd)
    if resp:
        return jsonify(True), 200
    else:
        return jsonify(False), 409


@app.route('/addFaculty', methods=['POST'])
@jwt_required
def addFaculty():
    uid = get_jwt_identity()

    faculties_data = request.json.get('faculty')['data']
    for faculty in faculties_data:
        name = faculty['fac_name']
        fid = faculty['fac_id']
        dep = faculty['fac_dep']
        # Checking empty values in JSON
        if name == "" or dep == "" or fid == "":
            return jsonify({'msg': "Received Null values"}), 406

        resp = add_faculty(uid, fid, name, dep)
        if resp is False:
            return jsonify({"msg": "One or more Faculty already Exist"}), 406
    return jsonify(True), 200


@app.route('/addClass', methods=['POST'])
@jwt_required
def addClass():
    uid = get_jwt_identity()
    if request.method == 'POST':
        f = request.files['class_tt']
        tt_path = f'static/{f.filename}'
        # Saving the resume on server temporarily for parsing
        f.save(tt_path)

        resp = add_class(uid, request.form.get('class_name'), request.form.get('class_dep'),
                         request.form.get('class_cams'), tt_path)

        return jsonify(resp)


@app.route('/dashboardData/<string:query>', methods=['POST'])
@jwt_required
def dashboardData(query):
    uid = get_jwt_identity()
    # if user_role(uid) is not "admin":
    #     print('Not Admin')
    #     return jsonify({'msg': "not authorized to perform the task"}), 401
    """if admin:
        -> all departments name - with data -> hod name, overall department feedback i.e. summation of existing stats of all classes
        -> top faculties overall organization -> faculty name & id with % rating
    """
    """if hod:
        -> all classes name  - with data -> with rating data -> of 1 week.
        -> top faculty of department -> faculty name & id with % rating
    """
    resp = dashboard_data(uid, query)
    return jsonify(resp), 200


@app.route('/getFacultyAnalysis/<string:fac_id>/<string:duration>', methods=['POST'])
@jwt_required
def getFacultyAnalysis(fac_id, duration):
    uid = get_jwt_identity()
    resp = faculty_analysis(fac_id)
    return jsonify(resp), 200


@app.route('/verify-email/<string:email>/<string:otp>', methods=['POST'])
def verify_email(email, otp):
    print(email)
    print(otp)
    resp = verify_usr_eml(email, otp)
    if resp is '404':
        return 'False'
    else:
        return 'True'


@app.route('/dummy', methods=['POST'])
@jwt_required
def dummy():
    uid = get_jwt_identity()
    return jsonify(uid)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
