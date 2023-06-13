# Description
Process audio and video data for it's visualization in quietavenu

# Setup

1. Create a cloud9 environment with ubuntu and more tha 6 GiB in ram
2. In AWS EC2 console increase the size of the volume to 70GiB
   1. Selece the Cloud9 instance
   2. Go to Storage tab and click volume ID
   3. Click on Actions -> Modify Volume
   4. Set size to 70 and click Modify
   5. Back in instace, in instance state dropdown menu select Reboot

3. In AWS AIM console create a new role 
   1. Select your use case: EC2
   2. Attach permissions policies: AdministratorAccess

4. In AWS EC2 console attach the role to the Cloud9 instance
   1. Selece the Cloud9 instance
   2. Go to Actions -> Security -> Modify IAM Role
   3. In the drop down list select the role previously created
More info on [aws docs](https://docs.aws.amazon.com/cloud9/latest/user-guide/credentials.html#credentials-temporary-attach-console) and [youtube video](https://www.youtube.com/watch?v=C4AyfV3Z3xs)

5. Click on AWS Cloud9 in menu bar -> Preferences -> AWS Settings -> turn off "AWS manage temporary credentials"

6. In the cloud9 bash
```bash
aws configure list
```
something like the following text must appear
```bash

      Name                    Value             Type    Location
      ----                    -----             ----    --------
   profile                <not set>             None    None
access_key     ****************2I37         iam-role    
secret_key     ****************ME6A         iam-role    
    region                <not set>             None    None
```
### More info on [aws docs](https://aws.amazon.com/premiumsupport/knowledge-center/access-key-does-not-exist)


7. Clone the proyect to aws cloud9
```bash
git clone https://github.com/betoluco/data_processing_for_quietavenue.git
```

8. In the cloud9 bash
```bash
sudo apt-get update
sudo apt install ffmpeg
cd data_processing_for_quietavenue
sudo pip3 install -r requirements.txt
```
# To ejecute:

Fill the data in entry.py file and ejecute it
