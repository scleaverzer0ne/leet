from mailjet_rest import Client
import os

api_key = ''
api_secret = ''
mailjet = Client(auth=(api_key, api_secret), version='v3.1')


def send_email_verification_mail(email, name, otp):
    """data = {
        'Messages': [
            {
                "From": {
                    "Email": "daljeetsinghchhabra@sistec.ac.in",
                    "Name": "LEET"
                },
                "To": [
                    {
                        "Email": email,
                        "Name": name
                    }
                ],
                "Subject": f"Email Verification for LEET.",
                "TextPart": "Verification",
                "HTMLPart": f'Dear {name}, we received a new sign-up request from this email address. <br> Please '
                            f'verify your account by entering this OTP in LEET app. '
                            f'<br> OTP: {otp}<br> Thanks.',
                "CustomID": "emlverification"
            }
        ]
    }
    """
    data = {
        'Messages': [
            {
                "From": {
                    "Email": "daljeetsinghchhabra@sistec.ac.in",
                    "Name": "LEET"
                },
                "To": [
                    {
                        "Email": email,
                        "Name": name
                    }
                ],
                "TemplateID": 1322921,
                "TemplateLanguage": True,
                "Subject": "New Signup - LEET",
                "Variables": {
                    "usr_fname": name,
                    "otp": otp
                }
            }
        ]
    }
    result = mailjet.send.create(data=data)
    print(result.status_code)
    print(result.json())


def send_forgot_password_mail(email, name, reset_password_link):
    data = {
        'Messages': [
            {
                "From": {
                    "Email": "daljeetsinghchhabra@sistec.ac.in",
                    "Name": "LEET"
                },
                "To": [
                    {
                        "Email": email,
                        "Name": name
                    }
                ],
                "Subject": f"Reset your LEET password!",
                "TextPart": "Password Reset",
                "HTMLPart": f'Dear {name}, a password reset request was received for this email account. <br> You can '
                            f'reset the password of your account by clicking on the <a href="{reset_password_link}">link</a>',
                "CustomID": "AppGettingStartedTest"
            }
        ]
    }
    result = mailjet.send.create(data=data)
    print(result.status_code)
    print(result.json())


def send_add_team_member_mail(email, org, link):
    data = {
        'Messages': [
            {
                "From": {
                    "Email": "daljeetsinghchhabra@sistec.ac.in",
                    "Name": "LEET"
                },
                "To": [
                    {
                        "Email": f"{email}",
                        "Name": f"{email}"
                    }
                ],
                "TemplateID": 1341966,
                "TemplateLanguage": True,
                "Subject": "New Member added - LEET",
                "Variables": {
                    "usr_fname": f"{email}",
                    "org": f"{org}",
                    "reg_link": f"{link}"
                }
            }
        ]
    }
    result = mailjet.send.create(data=data)
    print(result.status_code)
    print(result.json())
