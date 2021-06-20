import re

def str_extract(string, regex, ignore_case = False):
    if ignore_case:
        match = re.search(regex, string, re.IGNORECASE)
    else:
        match = re.search(regex, string)
    if match is None:
        return
    return match.group(0)

def extract_id_from_message(id):
  str1 = str_extract(id, r'\<\@\!?([^\>]+)\>')
  str2 = str_extract(str1, r'\d+')
  return int(str2)

def new_name(member, elo):
  print("\nPre shortned: ", member.nick)
  no_brackets = purge_name_brackets(member.nick)
  temp_name = check_name_length(no_brackets)
  print("Shortened NAME: ", temp_name)
  new_name = temp_name + "[" + str(elo) + "]"
  print(new_name)
  return new_name

def check_name_length(name):
  if len(name) > 24:
    name = name[:24]
  return name

def find_name_brackets(name):
  try:
    x = re.findall("\[.+\]", name)[0]
    return x
  except:
    return None

def purge_name_brackets(name):
  name = name.split("[", 1)[0]
  name = name.split("{", 1)[0]
  return name

# id = '<@!848460088565039144> This is a message.'
# print(extract_id_from_message(id))