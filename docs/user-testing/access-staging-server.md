## Log onto the Turing staging server

You will need to have a public key located on the server to be able to do this. Anyone with current access to the server will be able to add a new key to the existing authorized_keys file. 

The authorised keys file is located within: `home/adminuser/.ssh`

When logging into the server, the user arrives in the adminuser folder, so .ssh is within that directory, but hidden by default. Type `ls -a` to view hidden folders. 

`cd .ssh`

`ls -a`

The authorized_keys file will be listed. Use 
`nano authorized_keys` to open the file. Paste the new public key string into a new line in the file. The key must all be on one line. CTL-o to save the file contents and CTL-x to exit.

The owner of the public will now be able to log onto the server using SSH. 

ssh -i C:/users/nro25/keys/data-classification-app-docker-vm_key.pem adminuser@20.117.101.22
