"""Install into the current user's Codex skill directory on THIS machine only."""
import argparse,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--destination',type=Path,default=Path.home()/'.agents'/'skills'/'geomotion')
p.add_argument('--replace',action='store_true',help='Replace an existing install after backing it up')
a=p.parse_args();source=Path(__file__).resolve().parents[1]/'.agents'/'skills'/'geomotion';dest=a.destination.expanduser().resolve()
if dest==source or source in dest.parents or dest in source.parents:
 p.error('Install destination must be separate from the repository source')
if dest.exists():
 if not a.replace:p.error('Destination exists; inspect it first, then use --replace if desired')
 backup=dest.parent.parent/'skill-backups'/dest.name
 backup.parent.mkdir(parents=True,exist_ok=True)
 if backup.exists():p.error('Backup already exists; move it before replacing again')
 dest.rename(backup)
shutil.copytree(source,dest,ignore=shutil.ignore_patterns('cache','outputs','assets','__pycache__','*.pyc'))
print('Installed:',dest)
print('Start a new Codex session on this machine. Other environments need their own installation.')
