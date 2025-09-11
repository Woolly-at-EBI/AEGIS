# YAML for ancient processing and comparisons
yaml_file="./ancient.yaml"
echo "updating and processing "$yaml_file

curl 'https://raw.githubusercontent.com/MIxS-MInAS/extension-ancient/refs/heads/main/src/mixs/schema/ancient.yml' > $yaml_file

gen-python $yaml_file > ../../source/ancient.py

#####################################

yaml_file="./mixs.yaml"
echo "updating and processing "$yaml_file

curl https://raw.githubusercontent.com/GenomicsStandardsConsortium/mixs/refs/heads/main/src/mixs/schema/mixs.yaml > $yaml_file

gen-python $yaml_file> ../../source/mixs.py