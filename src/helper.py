import re
import logging


logging.basicConfig(filename="main.log",
                    format='%(asctime)s %(message)s',)
logger = logging.getLogger()
logger.warning("Helper initializing.")

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
  nick = member.nick if member.nick else member.name
  logger.warning(f"{nick} about to be added elo.")
  no_brackets = purge_name_brackets(nick)
  temp_name = check_name_length(no_brackets)
  new_name = temp_name + "[" + str(elo) + "]"
  logger.warning(f"{member.nick} name after elo added: {new_name}")
  return new_name


def check_name_length(name):
  if len(name) > 24:
    logger.warning(f"Name {str(name)} was too long, being shortened.")
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