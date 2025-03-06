import boto3



def get_billed_regions():
    ce = boto3.client('ce')
    response = ce.get_cost_and_usage(
        TimePeriod={'Start': '2025-01-01', 'End': '2025-02-02'},
        Granularity='MONTHLY',
        Metrics=['BlendedCost'],
        GroupBy=[{'Type': 'DIMENSION', 'Key': 'REGION'}]
    )
    return [item['Keys'][0] for item in response['ResultsByTime'][0]['Groups']]

print(get_billed_regions())