import yaml

# Open the YAML file
with open('global_config.yaml', 'r') as file:
    # Load the YAML data into a Python object
    data = yaml.safe_load(file)

# Access the data
print(data['DRONE_TOTAL'])