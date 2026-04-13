from datetime import datetime, timezone
import os
import time

# initializing date
test_date = datetime(2020, 4, 8)

# printing original date
print("The original date is : " + str(test_date))

# getting month name using %B
res = test_date.strftime("%B")

# printing result
print("Month Name from Date : " + str(res))


print(os.path.dirname(r"C:\Users\lb06ng01\Documents\hachshara\WEB\SERVER SIDE\server.py"))

print("123456789"[0:])




file_mtime = os.path.getmtime(r"C:\Users\lb06ng01\Documents\hachshara\WEB\SERVER SIDE\site-files\index.html")
last_modified = datetime.fromtimestamp(file_mtime, timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
print(last_modified)

print(datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT"))
print(time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime()))

