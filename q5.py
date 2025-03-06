import boto3
from datetime import datetime, timedelta

# Initialize AWS clients
ec2 = boto3.client('ec2')
cw = boto3.client('cloudwatch')
rds = boto3.client('rds')
s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')

# Time range for analysis
end_time = datetime.utcnow()
start_time = end_time - timedelta(days=30)


def get_low_utilization_ec2():
    """Find EC2 instances with CPU utilization below 10% over 30 days."""
    underutilized = []
    instances = ec2.describe_instances()['Reservations']

    for res in instances:
        for inst in res['Instances']:
            inst_id = inst['InstanceId']
            
            metrics = cw.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': inst_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=['Average']
            )

            avg_cpu = sum([dp['Average'] for dp in metrics.get('Datapoints', [])]) / max(1, len(metrics.get('Datapoints', [])))

            if avg_cpu < 10:
                underutilized.append(inst_id)

    return underutilized


def get_idle_rds_instances():
    """Find RDS instances with no active connections for over 7 days."""
    idle_instances = []
    dbs = rds.describe_db_instances()['DBInstances']

    for db in dbs:
        db_id = db['DBInstanceIdentifier']

        metrics = cw.get_metric_statistics(
            Namespace='AWS/RDS',
            MetricName='DatabaseConnections',
            Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_id}],
            StartTime=end_time - timedelta(days=7),
            EndTime=end_time,
            Period=86400,
            Statistics=['Sum']
        )

        if all(dp['Sum'] == 0 for dp in metrics.get('Datapoints', [])):
            idle_instances.append(db_id)

    return idle_instances


def get_unused_lambda_functions():
    """Find Lambda functions not invoked in the last 30 days."""
    unused_lambdas = []
    functions = lambda_client.list_functions()['Functions']

    for function in functions:
        fn_name = function['FunctionName']

        metrics = cw.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Invocations',
            Dimensions=[{'Name': 'FunctionName', 'Value': fn_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=['Sum']
        )

        if not metrics.get('Datapoints', []):  # No invocations in 30 days
            unused_lambdas.append(fn_name)

    return unused_lambdas


def get_unused_s3_buckets():
    """Find S3 buckets that are empty or not accessed recently."""
    unused_buckets = []
    buckets = s3.list_buckets()['Buckets']

    for bucket in buckets:
        bucket_name = bucket['Name']
        
        # Check if bucket is empty
        objects = s3.list_objects_v2(Bucket=bucket_name)
        if 'Contents' not in objects:  
            unused_buckets.append(bucket_name)
            continue  # No need to check access if it's empty
        
        # Check for recent access
        metrics = cw.get_metric_statistics(
            Namespace='AWS/S3',
            MetricName='NumberOfObjects',
            Dimensions=[{'Name': 'BucketName', 'Value': bucket_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=['Sum']
        )

        if not metrics.get('Datapoints', []):
            unused_buckets.append(bucket_name)

    return unused_buckets


# Run all checks
low_ec2 = get_low_utilization_ec2()
idle_rds = get_idle_rds_instances()
unused_lambda = get_unused_lambda_functions()
unused_s3 = get_unused_s3_buckets()

# Print Summary Report
print("\n AWS Cost Optimization Report \n")

print("Underutilized EC2 Instances (Low CPU <10%):", low_ec2 or "None")
print("Idle RDS Instances (No connections in 7 days):", idle_rds or "None")
print("Unused Lambda Functions (No invocations in 30 days):", unused_lambda or "None")
print("Unused S3 Buckets (Empty or No recent access):", unused_s3 or "None")