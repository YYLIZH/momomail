from schema import Mail
import json

with open("test.json", "r") as f:
    data = json.load(f)

mail = Mail(**data)
with open("test.html", "w") as f:
    f.write(mail.parts[0].body.data)
print(mail.dict(exclude={"payload"}))
