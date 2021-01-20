This project extracts the data out of audio files. The data is used in to create graphics

To start, set the variable in entry.py and run it.

To set up the project you need to do the following:

1. Create a cloud9 machine with ubuntu and more tha 6 GiB in ram
2. Increase the size of the volume to 40GiB
    a. Selece the Cloud9 instance
    b. Go to Storage tab and click volume ID
    c. Actions -> Modify Volume
    d. Set size to 40 and click Modify
3. In AWS AIM console create a new role 
    a. Select your use case: EC2
    b. Attach permissions policies: AdministratorAccess
4. In AWS EC2 console attach the role to the Cloud9 instance
    a. Selece the Cloud9 instance
    b. Choose Actions -> Security -> Modify IAM Role
    c. In the drop down list select the role previously created
    d. Back in the environment, use the AWS CLI to run the aws 
        configure command or the aws-shell to run the configure command. 
        Do not specify any values for AWS Access Key ID or AWS Secret Access Key
        (press Enter after each of these prompts). For Default region name,
        specify the AWS Region closest to you or the region where your AWS resources
        are located. For example, us-east-2 for the US East (Ohio) Region. For a 
        list of regions, see AWS Regions and Endpoints in the Amazon Web Services
        General Reference. Optionally, specify a value for Default output format 
        (for example, json).
5. sudo pip3 install boto3 numpy scipy
6. sudo apt-get update
7. sudo apt install ffmpeg