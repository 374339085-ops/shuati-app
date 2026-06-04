import os
with open('D:\\刷题软件\\server.py', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.find('WEB_HTML = r')
end = content.find('def get_local_ip()')
print(f"Block from {start} to {end}, length {end-start}")
# Check if the triple quote is closed before get_local_ip
last_part = content[end-200:end]
print("Last 200 chars before get_local_ip:")
print(repr(last_part[-200:]))
# Replace the entire block
new_part = "WEB_HTML = open(os.path.join(os.path.dirname(__file__), 'server_templates', '刷题.html'), encoding='utf-8').read()"
new_content = content[:start] + new_part + "\n\n" + content[end:]
with open('D:\\刷题软件\\server.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
print("Done!")
