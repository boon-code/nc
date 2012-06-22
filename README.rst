===
nc
===
This is a simple network connection program to copy files.
The second script, *gnc.py* is only used on an android device. You can easily 
copy files of one directory from your android phone, or push them to your 
computer.

Details
-------
This is a quite simple program. You first have to start it on your computer 
and then start gnc.py on your android phone. Now you can access the current
directory (or some other if specified). Normally, you should use it over an ssh tunnel (default setting). Therefore you need some tool like ConnectBot. 

Futur
-----
Featurs I want to add:

- It would be cool, if this tool itself could create an ssh tunnel...
- Maybe add an option in *gnc.py* that the pc can control file down/upload.
  I'm thinking about *fuse* because it has got python bindings and I already
  used it once (but with C).
- Allow access to subdirectories of the current working directory 
  (no links).



