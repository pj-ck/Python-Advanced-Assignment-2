import boto3
import csv

def get_regions():
    ec2 = boto3.client('ec2')
    response = ec2.describe_regions() #Describes the Regions that are enabled for your account, or all Regions.
    return [region['RegionName'] for region in response['Regions']]

def get_instance_types(region):
    ec2 = boto3.client('ec2', region_name=region)
    paginator = ec2.get_paginator('describe_instance_type_offerings') #paginator for describe_instance_type_offerings, 
    #Lists the instance types that are offered for the specified location. If no location is specified, the default is to list the instance types that are offered in the current Region.

    instance_types = set()
    
    for page in paginator.paginate(LocationType='region'):
        for offering in page['InstanceTypeOfferings']:
            instance_types.add(offering['InstanceType'])
    
    return sorted(instance_types)

def save_to_csv(data, filename='ec2_instance_types.csv'):
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['region', 'instance_type'])
        writer.writerows(data)

def main():
    all_data = []
    regions = get_regions()
    print(regions)
    # for region in regions:
    #     instance_types = get_instance_types(region)
    #     for instance in instance_types:
    #         all_data.append((region, instance))
    
    # save_to_csv(all_data)
    # print(f"EC2 instance types saved to ec2_instance_types.csv")

if __name__ == "__main__":
    main()