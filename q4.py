import boto3
import csv

def check_iam_roles():
    """Find IAM roles with overly permissive policies (AdministratorAccess)"""
    iam = boto3.client('iam')
    roles = iam.list_roles()['Roles']
    issues = []

    for role in roles:
        role_name = role['RoleName']
        attached_policies = iam.list_attached_role_policies(RoleName=role_name)['AttachedPolicies']

        for policy in attached_policies:
            if "AdministratorAccess" in policy['PolicyName']:
                issues.append([role_name, policy['PolicyName']])

    with open("iam_roles.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["IAMRoleName", "PolicyName"])
        writer.writerows(issues)

def check_iam_mfa():
    """Check if IAM users have MFA enabled"""
    iam = boto3.client('iam')
    users = iam.list_users()['Users']
    issues = []

    for user in users:
        mfa_devices = iam.list_mfa_devices(UserName=user['UserName'])['MFADevices']
        issues.append([user['UserName'], bool(mfa_devices)])

    with open("iam_mfa.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["IAMUserName", "MFAEnabled"])
        writer.writerows(issues)

def check_security_groups():
    """Identify security groups with public access on sensitive ports"""
    ec2 = boto3.client('ec2')
    sg_list = ec2.describe_security_groups()['SecurityGroups']
    issues = []

    for sg in sg_list:
        for rule in sg['IpPermissions']:
            for ip in rule.get('IpRanges', []):
                if ip['CidrIp'] == "0.0.0.0/0" and rule['FromPort'] in [22, 80, 443]:
                    issues.append([sg['GroupName'], rule['FromPort'], ip['CidrIp']])

    with open("security_groups.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["SGName", "Port", "AllowedIP"])
        writer.writerows(issues)

def check_unused_key_pairs():
    """List all EC2 key pairs and check if they are unused"""
    ec2 = boto3.client('ec2')
    key_pairs = ec2.describe_key_pairs()['KeyPairs']
    used_keys = set()

    # Check running instances
    instances = ec2.describe_instances()['Reservations']
    for res in instances:
        for inst in res['Instances']:
            if 'KeyName' in inst:
                used_keys.add(inst['KeyName'])

    unused_keys = [[kp['KeyName']] for kp in key_pairs if kp['KeyName'] not in used_keys]

    with open("unused_keys.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["KeyPairName"])
        writer.writerows(unused_keys)

# Run all checks
check_iam_roles()
check_iam_mfa()
check_security_groups()
check_unused_key_pairs()

print("🔹 AWS Security Reports Generated: iam_roles.csv, iam_mfa.csv, security_groups.csv, unused_keys.csv")