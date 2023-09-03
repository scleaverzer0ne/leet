"""
    Title: LEET
    Module Name: backend
    Author: Daljeet Singh Chhabra, Lalit Kumar Meena
    Language: Python
    Date Created: 22-03-2020
    Date Modified: 08-04-2020

    Description:
        ###############################################################
        ##  Controls the major backend functionality of LEET.
        ###############################################################
"""
from proj_constants import MONGO_HOST_URL, MONGO_USER_PWD, MONGO_USER_NAME, salt
from mailer import (send_email_verification_mail, send_add_team_member_mail)
from random import randint
from json import dumps as json_dump
from base64 import b64encode
from bson import ObjectId
import hashlib
import pymongo
from datetime import datetime
from parse_time_table import parse_tt


# @Author: Daljeet Singh Chhabra
def string_hash(text):
    return hashlib.sha256(salt.encode() + text.encode()).hexdigest() + ':' + salt


# @Author: Daljeet Singh Chhabra
def string_de_hash(text):
    password, salt = text.split(':')
    return password


# @Author: Daljeet Singh Chhabra
def register_auth_user(usr_fname, usr_lname, usr_eml, usr_pwd, usr_phone, usr_org, usr_type='staff', owner='self',
                       usr_dep='None'):
    """
        Function to register new user for the system
    :param usr_fname: First name of the user.
    :param usr_lname: Last name of the user.
    :param usr_eml: Email address of the user.
    :param usr_pwd: Password of the user.
    :param usr_phone: Phone number of the user.
    :param usr_org: Organization name of the user.
    :param usr_type: Head member of organization. Defaults to staff.
    :param usr_dep: Department of user -> Default None
    :param owner: Account owner -> self/Admin UID
    :return: True if registration successful, else False.
    """
    client = pymongo.MongoClient(MONGO_HOST_URL, username=MONGO_USER_NAME, password=MONGO_USER_PWD)
    db = client['leet']

    auth_users_col = db['auth_user']
    if auth_users_col.count_documents({'usr_eml': usr_eml}):
        # print(f'User with email {usr_eml} is already created.')
        return False
    if usr_pwd:
        hashed_pwd = string_hash(usr_pwd)
    else:
        hashed_pwd = ''

    new_user_data = {'usr_fname': usr_fname, 'usr_lname': usr_lname, 'usr_eml': usr_eml, 'usr_pwd': hashed_pwd,
                     'usr_phone': usr_phone, 'usr_comp': usr_org, 'is_activated': 'False', 'usr_type': usr_type,
                     'failed_attempts': 0, 'owner': owner, 'usr_dep': usr_dep}
    ins = auth_users_col.insert_one(new_user_data)

    if usr_pwd:  # User registered using password, so OTP will be sent to verify email.
        # Generating OTP for user
        otp = randint(100000, 999999)

        # Setting the OTP in the DB
        verification_data = {
            'usr_eml': usr_eml,
            'otp': otp
        }
        verify_usr_eml_col = db['verify_usr_eml']
        ins = verify_usr_eml_col.insert_one(verification_data)

        client.close()
        # Send Email verification mail
        send_email_verification_mail(usr_eml, usr_fname, otp)
        # print(verification_link)

    else:
        data = {"eml": usr_eml, "org": usr_org}
        json_data = json_dump(data)
        link = 'leet://' + b64encode(bytes(json_data, 'utf-8')).decode('utf-8')
        send_add_team_member_mail(usr_eml, usr_org, link)

    return ins.acknowledged


# @Author: Daljeet Singh Chhabra
def check_auth_login(usr_eml, usr_pwd):
    """
        Function to authenticate user's login credentials in the database.
    :param usr_eml: Email address of the user.
    :param usr_pwd: Password of the user.
    :return: True if login successful, else False.
    """
    client = pymongo.MongoClient(MONGO_HOST_URL, username=MONGO_USER_NAME, password=MONGO_USER_PWD)
    db = client['leet']

    auth_users_col = db['auth_user']
    hashed_pwd = string_hash(usr_pwd)
    search_data = {'usr_eml': usr_eml, 'usr_pwd': hashed_pwd}

    res = auth_users_col.count_documents(search_data)
    if res is None:  # No such user exist
        return None
    res_act = auth_users_col.find_one({'usr_eml': usr_eml}, {'is_activated': 1, '_id': 1})

    is_activated = res_act.get('is_activated')

    client.close()
    # 'Logged in Successfully'
    if res == 1 and is_activated == 'True':
        return str(res_act.get('_id'))
    # Invalid Credentials
    else:
        # Increasing the failed attempts
        search_data.pop('usr_pwd')
        increase_failed_attempts = {'failed_attempts': 1}
        lock_acc = {'is_activated': 'False'}
        auth_users_col.update_one(search_data, {"$inc": increase_failed_attempts})
        failed_attempts = auth_users_col.find_one(search_data, {'_id': 0, 'failed_attempts': 1})['failed_attempts']

        if failed_attempts >= 3:
            auth_users_col.update_one(search_data, {"$set": lock_acc})
            return 0
        return None


# @Author: Daljeet Singh Chhabra
def get_auth_user_details(uid, q=None):
    client = pymongo.MongoClient(MONGO_HOST_URL, username=MONGO_USER_NAME, password=MONGO_USER_PWD)
    db = client['leet']

    auth_users_col = db['auth_user']
    search_data = {'_id': ObjectId(uid)}
    if q == 'name':
        res = auth_users_col.find_one(search_data,
                                      {'_id': 0, 'usr_fname': 1, 'usr_lname': 1, 'usr_type': 1, 'usr_dep': 1})
        if res['usr_type'] == 'admin':
            res.pop('usr_type')
            res['usr_admin'] = True
        else:
            res.pop('usr_type')
            res['usr_admin'] = False
        client.close()
        return res

    res = auth_users_col.find_one(search_data, {'_id': 0, 'usr_pwd': 0, 'failed_attempts': 0})

    if res['usr_type'] == 'admin':
        res.pop('usr_type')
        res['usr_admin'] = True
        res['owner'] = str(res['owner'])
    else:
        res.pop('usr_type')
        res['usr_admin'] = False
        res['owner'] = str(res['owner'])
    client.close()

    return res


# @Author: Daljeet Singh Chhabra
def verify_usr_eml(usr_eml, otp):
    """
        Function to verify user's email address and activates the account so that user can login to the system.
    :param usr_eml: Email address of the user
    :param otp: one time email verification key for user account
    :return:
    """
    search_data = {
        'usr_eml': usr_eml,
        'otp': otp
    }
    client = pymongo.MongoClient(MONGO_HOST_URL, username=MONGO_USER_NAME, password=MONGO_USER_PWD)
    db = client['leet']

    verify_usr_eml_col = db['verify_usr_eml']
    auth_user_col = db['auth_user']
    res = verify_usr_eml_col.count_documents(search_data)
    print(search_data)
    print(res)
    if res == 1:
        search_data.pop('otp')
        new_data = {
            'is_activated': 'True'
        }
        auth_user_col.update_one(search_data, {"$set": new_data})

        usr_comp_id = auth_user_col.find_one(search_data, {'_id': 1}).get('_id')
        verify_usr_eml_col.delete_one(search_data)

        return True
    else:
        return '404'


# @Author: Daljeet Singh Chhabra
def set_usr_password(usr_eml, pwd_reset_key, usr_pwd):
    """
        Function to reset user password.
    :param usr_pwd: New password of the user
    :param usr_eml: Email address of the user.
    :param pwd_reset_key: Single use password reset key.
    :return:
    """
    search_data = {
        'usr_eml': usr_eml,
        'pwd_reset_key': pwd_reset_key,
    }

    client = pymongo.MongoClient(MONGO_HOST_URL, username=MONGO_USER_NAME, password=MONGO_USER_PWD)
    db = client['leet']

    reset_usr_pwd_col = db['reset_usr_pwd']
    auth_user_col = db['auth_user']
    res = reset_usr_pwd_col.count_documents(search_data)
    if res == 1:
        search_data.pop('pwd_reset_key')

        hashed_pwd = string_hash(usr_pwd)
        new_data = {
            'is_activated': 'True',
            'usr_pwd': hashed_pwd,
            'failed_attempts': 0
        }
        auth_user_col.update_one(search_data, {"$set": new_data})
        reset_usr_pwd_col.delete_one(search_data)
        return True

    else:
        return '404'


# @Author: Daljeet Singh Chhabra
def faculty_analysis(f_id):
    """
        Function to return analysis data of individual faculty
    :param f_id: Faculty ID
    :return:
    """
    search_data = {'fac_id': f_id, }
    client = pymongo.MongoClient(MONGO_HOST_URL, username=MONGO_USER_NAME, password=MONGO_USER_PWD)
    db = client['leet']
    analysis_col = db['lecture_analysis']

    res = list(analysis_col.find(search_data, {'fac_id': 1, 'date': 1, 'analysis.overall_rate': 1, '_id': 0}))
    overall = 0
    for i in res:
        overall += float(i['analysis'].get('overall_rate'))
    overall /= len(res)
    res.append(overall)
    return res


# @Author: Lalit Kumar Meena
def user_role(uid):
    """
        Function to get role of user.
    :param uid: UID of user.
    :return: Role of the user
    """
    search_data = {
        '_id': ObjectId(uid)
    }

    client = pymongo.MongoClient(MONGO_HOST_URL, username=MONGO_USER_NAME, password=MONGO_USER_PWD)
    db = client['leet']

    auth_user_col = db['auth_user']
    res = auth_user_col.count_documents(search_data)
    usr_role = None
    if res == 1:
        usr_role = auth_user_col.find_one(search_data, {'usr_type': 1, '_id': 0})['usr_type']

    return usr_role


# @Author: Lalit Kumar Meena
def add_staff(uid, eml, dep, org):
    """
        Create a new staff entry in auth_user
    :param uid: UID of ADMIN
    :param eml: Email address of user
    :param dep: Department of user
    :param org: Organization of user
    :return: True if success else False
    """

    # noinspection PyTypeChecker
    return register_auth_user(None, None, eml, None, None, org, "Staff", ObjectId(uid), dep)


# @Author: Lalit Kumar Meena
def register_staff(usr_fname, usr_lname, usr_eml, usr_pwd, usr_phone, usr_org):
    """
        Updates existing staff entry in auth_user and verifying its email
    :param usr_fname: First name of user
    :param usr_lname: Last name of user
    :param usr_eml: Email address of user
    :param usr_pwd: Password of user
    :param usr_phone: Phone number of user
    :param usr_org: Organization of user.
    :return: True or False
    """
    hashed_pwd = string_hash(usr_pwd)

    client = pymongo.MongoClient(MONGO_HOST_URL, username=MONGO_USER_NAME, password=MONGO_USER_PWD)
    db = client['leet']

    auth_users_col = db['auth_user']
    res = auth_users_col.count_documents({'usr_eml': usr_eml})
    if res == 1:

        new_staff_data = {
            'usr_fname': usr_fname,
            'usr_lname': usr_lname,
            'usr_pwd': hashed_pwd,
            'usr_phone': usr_phone,
        }
        auth_users_col.update_one({'usr_eml': usr_eml}, {"$set": new_staff_data})

        # Generating OTP for user
        otp = randint(100000, 999999)

        # Setting the OTP in the DB
        verification_data = {
            'usr_eml': usr_eml,
            'otp': otp
        }
        verify_usr_eml_col = db['verify_usr_eml']
        ins = verify_usr_eml_col.insert_one(verification_data)

        client.close()

        # Send Email verification mail
        send_email_verification_mail(usr_eml, usr_fname, otp)

        return ins.acknowledged
    else:
        return False


# @Author: Lalit Kumar Meena
def add_faculty(uid, fid, name, dep):
    """
        Function to add a new faculty in faculties collection
    :param uid: Id of the HOD
    :param fid: Faculty ID
    :param name: Faculty's name
    :param dep: Faculty's department.
    :return: True if successfully added. False if faculty already exist.
    """
    client = pymongo.MongoClient(MONGO_HOST_URL, username=MONGO_USER_NAME, password=MONGO_USER_PWD)
    db = client['leet']

    faculty_col = db['faculties']
    res = faculty_col.count_documents({'fac_id': fid})
    if res == 0:
        new_fac_data = {
            'fac_name': name,
            'fac_id': fid,
            'fac_dep': dep,
            'fac_head': ObjectId(uid)
        }
        ins = faculty_col.insert_one(new_fac_data)
        return ins.acknowledged

    else:
        return False


# @Author: Lalit Kumar Meena
def add_class(uid, class_name, class_dep, class_cams, class_tt_path):
    """

    :param uid: Id of HOD
    :param class_name: Name of Class
    :param class_dep: Department of class
    :param class_cams: IP Addresses of cameras installed in class -> ['str', 'str']
    :param class_tt_path: path of time table excel, to be parsed from parse_time_table module.
    :return: True if success, else false.
    """
    client = pymongo.MongoClient(MONGO_HOST_URL, username=MONGO_USER_NAME, password=MONGO_USER_PWD)
    db = client['leet']

    class_col = db['classes']
    res = class_col.find_one({'class_name': class_name})
    if res == None:
        new_class_data = {
            'class_name': class_name,
            'class_dep': class_dep,
            'class_cams': class_cams,
            'tt': parse_tt(uid, class_tt_path),
            'hod_id': ObjectId(uid)
        }

        ins = class_col.insert_one(new_class_data)
        return ins.acknowledged

    else:
        return False


# @Author: Lalit Kumar Meena
def dashboard_data(uid, query):
    """
    Gets the dashboard data for the particular department or all the departments if query is "admin"
    :param uid: _id of user
    :param query: department name or "admin"
    :return: dict of dashboard data.
    """
    client = pymongo.MongoClient(MONGO_HOST_URL, username=MONGO_USER_NAME, password=MONGO_USER_PWD)
    db = client['leet']

    analysis_col = db['lecture_analysis']
    auth_user_col = db['auth_user']
    faculties_col = db['faculties']
    if query == 'admin':
        res = []
        hod_ids = list(auth_user_col.find({'owner': ObjectId(uid)}, {'_id': 1}))
        for i in hod_ids:
            res.append(str(i.get('_id')))
        final_res = []
        for x in res:
            final_res.append(list(analysis_col.find({'hod_id': ObjectId(x)}, {'hod_id': 0, '_id': 0})))

        return final_res[0]

    else:
        class_ana = []
        for x in analysis_col.find({'hod_id': ObjectId(uid)}, {'hod_id': 0, '_id': 0}):
            class_ana.append(x)

        # Generating all faculties ranking
        search_data = {'fac_head': ObjectId(uid)}

        faculties = list(faculties_col.find(search_data, {'fac_id': 1, 'fac_name': 1, '_id': 0}))
        faculty_ids = [i['fac_id'] for i in faculties]

        def get_fac_name(fac_id):
            for f in faculties:
                if f['fac_id'] == fac_id:
                    return f['fac_name']

        fac_ana = []
        for f_id in faculty_ids:
            search_data = {'fac_id': f_id}
            res = list(analysis_col.find(search_data, {'fac_id': 1, 'date': 1, 'analysis.overall_rate': 1, '_id': 0}))
            overall = 0
            for i in res:
                # noinspection PyTypeChecker
                overall += float(i['analysis'].get('overall_rate'))
            overall /= len(res)
            fac_ovr = {
                'fac_name': get_fac_name(f_id),
                'fac_id': str(f_id),
                'overall_rate': overall
            }

            fac_ana.append(fac_ovr)

        final_res = {
            'class_ana': class_ana,
            'fac_ana': fac_ana
        }
        return final_res


# @Author: Lalit Kumar Meena
def lecture_analysis_data(uid, anal_res):
    """
        "Gets the analysis data of lectures from live lecture feed"
    :param uid: Id of HOD
    :param anal_res: Analysis Result
    """

    client = pymongo.MongoClient(MONGO_HOST_URL, username=MONGO_USER_NAME, password=MONGO_USER_PWD)
    db = client['leet']

    analysis_col = db['lecture_analysis']
    anal_res['date'] = datetime.now()
    anal_res['hod_id'] = ObjectId(uid)
    ins = analysis_col.insert_one(anal_res)

    return ins.acknowledged
