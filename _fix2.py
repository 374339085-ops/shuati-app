with open('D:\\刷题软件\\server.py', 'rb') as f:
    content = f.read()
webpos = content.find(b'WEB_HTML = r')
endpos = content.find(b'def get_local_ip()')
print(f"WEB_HTML at {webpos}, get_local_ip at {endpos}")
if b'WEB_HTML = open' in content:
    print("Already fixed")
else:
    # Replace the old r''' block
    new_line = b"WEB_HTML = open(os.path.join(os.path.dirname(__file__), 'server_templates', '\xe5\x88\xb7\xe9\xa2\x98.html'), encoding='utf-8').read()\n"
    new_content = content[:webpos] + new_line + content[endpos:]
    with open('D:\\刷题软件\\server.py', 'wb') as f:
        f.write(new_content)
    print(f"Replaced! New size {len(new_content)}")
