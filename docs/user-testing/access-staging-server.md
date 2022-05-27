# Accessing the Staging Server

This guide shows you how to add a new public key to the staging environment, and how to log on to the server using SSH.

See [these instructions](https://docs.oracle.com/cd/E36784_01/html/E37125/sshuser-33.html) for generating a new public/private key pair

## Logging on to the Staging Server

You will need to have a public key located on the server to be able to log on to it - see 'Adding a Key to the Staging Server' below for how to add a public key to the server.

Once your public key is on the server, you can access the server by running the following command:

```ssh -i <FILEPATH_TO_YOUR_PRIVATE_KEY> adminuser@20.117.101.220```

Where <FILEPATH_TO_YOUR_PRIVATE_KEY> is the location on your machine of the private key corresponding to the public key on the server.

## Adding a Key to the Staging Server

Anyone with current access to the server will be able to add a new key to the existing authorized_keys file. 

The following steps need to be carried out:

1. Log on to the server as above

2. Run `ls -a` to see all folder contents, including hidden ones

3. Run `cd .ssh` to navigate into the .ssh folder, and run `ls -a` to see all the files in this folder. The file we want to amend is called `authorized_keys`

5. Run `nano authorized_keys` to open the file

6. Paste the new public key string into a new line in the file. The key must all be on one line

7. Press `Ctrl+o` to save the file contents and `Ctrl+x` to exit

The owner of the public will now be able to log onto the server using SSH :rocket:
