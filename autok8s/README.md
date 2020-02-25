# SSH key without a password
To set up a passwordless SSH connection for the root user you need to have root access on the server. Easiest method is to temporarily allow root to log in over ssh via password. One way or another you need root access on the server to do this. If you do not have root access on the server, contact the server administrator for help.

#### On the client (where you ssh FROM)
First make a ssh key with no password. I highly suggest you give it a name rather then using the default
`ssh-keygen -f foo`

When you are prompted for a password, just hit the enter key and you will generate a key with no password.

Next you need to transfer the key to the server. Easiest method is to use ssh-copy-id . To do this you must temporarily allow root to ssh into the server.

##### On the server (where you ssh TO)
edit /etc/ssh/sshd_config
`sudo nano /etc/ssh/sshd_config`
Make sure you allow root to log in with the following syntax
`PasswordAuthentication yes`
`PermitRootLogin yes`
`Restart the server`

Restart the ssh server
`sudo service ssh restart`
Set a root password, use a strong one
`sudo passwd`

##### On the client :
From the client, Transfer the key to the server
`ssh-copy-id -i ~/.ssh/foo root@server`
change "foo" the the name of your key and enter your server root password when asked.

##### Test the key

`ssh -i ~/.ssh/foo root@server`
Assuming it works, unset a root password and disable password login.

##### On the server :
Reset the root passwords expiry
`sudo passwd -l root`
Edit /etc/ssh/sshd_config
`sudo nano `/etc/ssh/sshd_config``

Change the following :
`PasswordAuthentication no`
`PermitRootLogin without-password`
Restart the ssh server
`sudo service ssh restart`

##### On the client (Test):
You should now be able to ssh in with your key without a password and you should not be able to ssh in as any user without a key.

