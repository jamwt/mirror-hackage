# requires python-requests.org
import sys
import requests
import os
import hashlib
import traceback

if len(sys.argv) < 2:
    sys.stderr.write("error: require path to mirror base as first argument")
    raise SystemExit(1)
base = sys.argv[1]

os.chdir(base)

def mkdir_p(d):
    if not os.path.isdir(d):
        os.mkdir(d)

mkdir_p("archive")
mkdir_p("archive/package")
mkdir_p("index")

if len(sys.argv) > 2:
    url_base = sys.argv[2]
    if not url_base.endswith("/"):
        url_base += "/"
else:
    url_base = "http://hackage.haskell.org/packages/archive/"

# Thanks stackoverflow..
class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def start_line(l):
    sys.stderr.write(l.ljust(60) + "...")
    sys.stderr.flush()

def end_okay():
    sys.stderr.write(BColors.OKGREEN + "[OK]".rjust(10) + BColors.ENDC + "\n")

def end_finished():
    sys.stderr.write(BColors.OKBLUE + "[DONE]".rjust(10) + BColors.ENDC + "\n")

def end_starting():
    sys.stderr.write(BColors.WARNING + "[START]".rjust(10) + BColors.ENDC + "\n")

def end_fail(why):
    sys.stderr.write(BColors.FAIL + "[FAIL]".rjust(10) + BColors.ENDC + "\n   -> " + why + "\n")
    raise SystemExit(1)

def information(i):
    sys.stderr.write(BColors.WARNING + "   --> " + i + "\n" + BColors.ENDC)

start_line("[1] Downloading log")
resp = requests.get(url_base + "log")
if resp.status_code != 200:
    end_fail("log download got HTTP status code: %d" % resp.status_code)
log_data = resp.content.splitlines()
end_okay()

mark = open("_mark", "r").read().strip() if os.path.isfile("_mark") else "(missing)"
start_line("[2] Scanning for %r" % mark)

pos = -1

def make_log_checksums():
    global pos # woot side efffects!
    csum = ""
    for x, l in enumerate(log_data):
        csum = (hashlib.sha1(csum + l).hexdigest())
        if csum == mark:
            assert pos == -1, "wtfbbq?"
            pos = x
        yield l, csum

steps = list(make_log_checksums())

pos += 1

todo = len(log_data) - pos

end_okay()

information("%d new uploads to mirror" % todo)

# Mirror each
start_line("[3] Mirroring new packages")
end_starting()

def mirror_package(full, package, version):
    # 1. Make directory

    mkdir_p("index/%s" % package)
    mkdir_p("index/%s/%s" % (package, version))

    cabal_r = requests.get(url_base + "%s/%s/%s.cabal" % (package, version, package))
    if cabal_r.status_code == 404:
        information("Package %s seems to have been removed!  Skipping..." % full)
        return
    assert cabal_r.status_code == 200, "non-200 from cabal download"
    with open("index/%s/%s/%s.cabal" % (package, version, package), "w") as f:
        f.write(cabal_r.content)

    data_r = requests.get(url_base + "%s/%s/%s.tar.gz" % (package, version, full))
    assert data_r.status_code == 200, "non-200 from tarball download"
    with open("archive/package/%s.tar.gz" % (full,), "w") as f:
        f.write(data_r.content)

for x, (pline, csum) in enumerate(steps[pos:]):
    # Download all we need..

    package, version = pline.split()[-2:]
    fullpack = "%s-%s" % (package, version)

    # Actually mirror
    start_line("        %s (%d/%d)" % (fullpack, x+1, todo))
    try:
        mirror_package(fullpack, package, version)
    except:
        information("Exception during mirror:\n%s" % traceback.format_exc())
        end_fail("Aborting due to exception")
    else:
        end_okay()

    # Update bookmark at each stage
    # (paranoid: atomic rename)
    with open("_temp_mark", "w") as f:
        f.write(csum)

    os.rename("_temp_mark", "_mark") 

start_line("    Mirroring new packages")
end_finished()

start_line("[4] Building index")
end_starting()

os.chdir("index")
os.system("tar cfz 00-index.tar.gz *")
os.rename("00-index.tar.gz", "../archive/00-index.tar.gz")

start_line("    Building index")
end_finished()
