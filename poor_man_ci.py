from __future__ import print_function
import traceback
import sys
import os
import subprocess
from pathlib import Path


ROOT_DIR = "poor-man-ci"


def remove_everything():
    remove = [
      "{0}/build.sh".format(ROOT_DIR),
      "{0}/debug.log".format(ROOT_DIR),
      "{0}".format(ROOT_DIR)
    ]

    for file in remove:
      path = Path(".git/{0}".format(file))
      try:
        if path.exists():
          if path.is_dir():
            path.rmdir()
          else:
            path.unlink()

        print("Success: removed {0}".format(path))
      except:
        print("Error: cannot remove {0}".format(path))


if not Path(".git").exists():
  print("Error: cannot find .git folder. Are you inside project folder?")
  sys.exit()


# Checking whether ci configured for this project
if Path(".git/poor-man-ci").exists():
  print("Error: project already configured for poor man ci")
  sys.exit()

command = None

while True:
  command = input("Please enter command for building")

  if not command:
    print("Warning: command cannot be empty")
  else:
    break


build_keyword = input("Should commit require `build` keyword for building or every commit == build? [y/N]")

if build_keyword in ["y", "Y", "Yes", "yes", "YES"]:
  print("Ok! Commit message would require to have build keyword")
  build_keyword = True
else:
  print("Ok! Build will be everytime you push to current project branch")
  build_keyword = False


command_content = """
{0}
""".format(command)


build_part = """
echo "$(date +"%d.%m.%Y %T"): BUILDING" |& tee -a  ./.git/poor-man-ci/debug.log
./.git/poor-man-ci/build.sh |& tee -a ./.git/poor-man-ci/debug.log
echo "$(date +"%d.%m.%Y %T"): BUILD DONE" |& tee -a  ./.git/poor-man-ci/debug.log
"""

if build_keyword:
  build_part = """
log=$(git log -1)
if [[ log == *"build"* ]]; then
  echo "$(date +"%d.%m.%Y %T"): TRIGGERING BUILD" |& tee -a ./.git/poor-man-ci/debug.log
  {0}
  echo "$(date +"%d.%m.%Y %T"): BUILD DONE" |& tee -a ./.git/poor-man-ci/debug.log
fi
""".format(build_part)


hook_part = """
echo "$(date +"%d.%m.%Y %T"): INCOMING CHANGES" |& tee -a  ./.git/poor-man-ci/debug.log
{0}
""".format(build_part)

CURRENT_DIR = os.path.abspath(
  os.path.dirname(__file__)
)

crontab_part = """
# POOR MAN CI {0}
* * * * * cd {0} && git pull
""".format(
  CURRENT_DIR
)


BUILD_FILE = ".git/{0}/build.sh".format(ROOT_DIR)
LOG_FILE = ".git/{0}/debug.log".format(ROOT_DIR)

HOOK_FILE = ".git/hooks/post-merge"

try:
  Path(".git/" + ROOT_DIR).mkdir()
  Path(LOG_FILE).touch()

  with open(BUILD_FILE, "w") as file:
    file.write(command_content)
  
  print("Created build file")

  with open(HOOK_FILE, "w") as file:
    file.write(hook_part)

  print("Created hook file")

  print("Changing permissions for files")

  subprocess.call(['chmod', 'g+rwx', BUILD_FILE])
  subprocess.call(['chmod', 'g+rwx', HOOK_FILE])

  print("Permissions changed!")

  print("Creating crontab")

  tabs = ""

  try:
    tabs = subprocess.check_output("crontab -l", shell=True).decode()
  except subprocess.CalledProcessError:
    print(
      "Info: crontab -l returned non zero exit code but this is ok. It means there is no crontab data for current user"
    )
    pass

  if "# POOR MAN CI {0}".format(CURRENT_DIR) in tabs:
    print("Warning: crontab for this project already there")
  else:
    subprocess.run(
      """( crontab -l | cat; echo "{0}" ) | crontab -""".format(
        crontab_part
      ),
      shell=True
    )

    print("Added crontab!")
  
  
  print("Successfully initialized poor man ci!")
except:
  print("Error: cannot initialize poor man ci. See error below:")
  traceback.print_exc()
  remove_everything()

