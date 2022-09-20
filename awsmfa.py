#!/usr/bin/env python3

from configparser import ConfigParser, NoSectionError
import os
import optparse
import sys
import boto3

def check_credentials():
    config_parser = ConfigParser()
    credentials_parser = ConfigParser()
    config_parser.read(filenames = os.path.expanduser('~/.aws/config'))
    try:
        config_parser.get('profile perm', 'region')
    except NoSectionError as e:
        config_parser.add_section('profile perm')
        # parser.set('profile test1', {'region':'ap-southeast-1'})
        config_parser['profile perm'] = {
            'region':'ap-southeast-1',
            'output':'json'
        }
        with open(os.path.expanduser('~/.aws/config'), 'w') as x:
            config_parser.write(x)

    credentials_parser.read(filenames = os.path.expanduser('~/.aws/credentials'))
    try:
        credentials_parser.get('perm', 'aws_access_key_id')
        credentials_parser.get('perm', 'aws_secret_access_key')
        print("Permenant profile detected")
    except NoSectionError as e:
        if 'default' in credentials_parser.keys():
            print("Permanent credentials will be created from default credentials")
            credentials_parser.add_section('perm')
            credentials_parser['perm'] = {
                'aws_access_key_id':credentials_parser.get('default', 'aws_access_key_id'),
                'aws_secret_access_key':credentials_parser.get('default', 'aws_secret_access_key')
            }
        else:
            print("Permanent profile credentials were not found, please insert the required info:")
            key_id = input("Enter your permanent aws_access_key_id: ")
            secret_key = input("Enter your permanent aws_secret_access_key: ")
            credentials_parser.add_section('perm')
            credentials_parser['perm'] = {
                'aws_access_key_id':key_id,
                'aws_secret_access_key':secret_key
            }
        with open(os.path.expanduser('~/.aws/credentials'), 'w') as y:
            credentials_parser.write(y)

def set_temp_cred(key_id, secret, session_id):
    credentials_parser = ConfigParser()
    credentials_parser.read(filenames = os.path.expanduser('~/.aws/credentials'))
    credentials_parser['default'] = {
        'aws_access_key_id':key_id,
        'aws_secret_access_key':secret,
        'aws_session_token':session_id
    }
    with open(os.path.expanduser('~/.aws/credentials'), 'w') as z:
        credentials_parser.write(z)
        
    # with open(os.path.expanduser("~/.bashrc"), "a") as outfile:
    # # 'a' stands for "append"  
    # outfile.write("export MYVAR=MYVALUE")
        
    # # write to OS environment variable
    # os.environ['AWS_ACCESS_KEY_ID'] = key_id
    # os.environ['AWS_SECRET_ACCESS_KEY'] = secret
    # os.environ['AWS_SESSION_TOKEN'] = session_id

if __name__ == '__main__':
    opt_parser = optparse.OptionParser()
    opt_parser.add_option('-t', '--token',
            action="store", dest="token",
            help="MFA token")
    opt_parser.add_option('-u', '--user',
            action="store", dest="user",
            help="AWS user name")
    options, args = opt_parser.parse_args()
    if not options.token:
        print("MFA token is required, please run the script with -t <token>")
        sys.exit(1)
    if not options.user:
        print("usser is required, please run the script with -u <user name>")
        sys.exit(1)
    check_credentials()
    session = boto3.Session(profile_name='perm')
    sts_client = session.client('sts')
    response = sts_client.get_session_token(
        DurationSeconds=129600,
        SerialNumber=f'arn:aws:iam:::mfa/{options.user}',
        TokenCode=options.token
    )
    c = response['Credentials']
    print("Setting temp credential")
    set_temp_cred(c['AccessKeyId'], c['SecretAccessKey'], c['SessionToken'])
    print(f"Your session expires on {c['Expiration']}")
