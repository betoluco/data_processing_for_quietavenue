# Description
This project extracts the data out of audio files. The data is used in to create graphics

To start, set the variable in entry.py and run it.

# Setup

1. Create a cloud9 machine with ubuntu and more tha 6 GiB in ram
2. Increase the size of the volume to 70GiB
   1. Selece the Cloud9 instance
   2. Go to Storage tab and click volume ID
   3. Click on Actions -> Modify Volume
   4. Set size to 70 and click Modify

3. In AWS AIM console create a new role 
   1. Select your use case: EC2
   2. Attach permissions policies: AdministratorAccess

4. In AWS EC2 console attach the role to the Cloud9 instance
   1. Selece the Cloud9 instance
   2. Choose Actions -> Security -> Modify IAM Role
   3. In the drop down list select the role previously created
### More info on [aws docs](https://docs.aws.amazon.com/cloud9/latest/user-guide/credentials.html#credentials-temporary-attach-console) and [youtube viedo](https://www.youtube.com/watch?v=C4AyfV3Z3xs)

5. Clone the proyect to aws cloud9
```
git clone https://github.com/betoluco/data_processing_for_quietavenue.git
```

6. In the cloud9 bash
```
sudo apt-get update
sudo pip3 install boto3 numpy scipy
sudo pip3 install --upgrade awscli
sudo apt install ffmpeg
```

7. Click on AWS Cloud9 in menu bar -> Preferences -> AWS Settings -> turn off AWS manage temporary credentials

8. In the cloud9 bash
```
aws configure list
```
something like the following text must appear
```

      Name                    Value             Type    Location
      ----                    -----             ----    --------
   profile                <not set>             None    None
access_key     ****************2I37         iam-role    
secret_key     ****************ME6A         iam-role    
    region                <not set>             None    None
```
### More info on [aws docs](https://aws.amazon.com/premiumsupport/knowledge-center/access-key-does-not-exist)