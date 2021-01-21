This project extracts the data out of audio files. The data is used in to create graphics

To start, set the variable in entry.py and run it.

To set up the project you need to do the following:

1. Create a cloud9 machine with ubuntu and more tha 6 GiB in ram
2. Increase the size of the volume to 70GiB
    a. Selece the Cloud9 instance
    b. Go to Storage tab and click volume ID
    c. Click on Actions -> Modify Volume
    d. Set size to 70 and click Modify

3. In AWS AIM console create a new role 
    a. Select your use case: EC2
    b. Attach permissions policies: AdministratorAccess

4. In AWS EC2 console attach the role to the Cloud9 instance
    a. Selece the Cloud9 instance
    b. Choose Actions -> Security -> Modify IAM Role
    c. In the drop down list select the role previously created
    # More info on:
        https://docs.aws.amazon.com/cloud9/latest/user-guide/credentials.html#credentials-temporary-attach-console
        https://www.youtube.com/watch?v=C4AyfV3Z3xs

5. On bash "sudo pip3 install boto3 numpy scipy"
6. On bash "sudo pip3 install --upgrade awscli"
7. On bash "sudo apt-get update"
8. On bash "sudo apt install ffmpeg"
9. 
9. Click on AWS Cloud9 in menu bar -> Preferences -> AWS Settings
    turn off AWS manage temporary credentials

10. On bash "aws configure list". and check
      Name                    Value             Type    Location
      ----                    -----             ----    --------
   profile                <not set>             None    None
access_key     ****************2I37         iam-role    
secret_key     ****************ME6A         iam-role    
    region                <not set>             None    None

    #More info on: 
        https://aws.amazon.com/premiumsupport/knowledge-center/access-key-does-not-exist/