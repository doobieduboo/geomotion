"""Fetch only declared demo assets; verify bytes and retain provenance."""
import hashlib,json,urllib.request
from pathlib import Path


def prepare(skill_root):
    manifest=json.loads((skill_root/'references'/'asset-manifest.json').read_text())
    dest=skill_root/'assets'/'demo';dest.mkdir(parents=True,exist_ok=True)
    for asset in manifest['assets']:
        p=dest/asset['filename']
        if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==asset['sha256']:
            continue
        req=urllib.request.Request(asset['url'],headers={'User-Agent':'GeoMotionSkill/1.0'})
        with urllib.request.urlopen(req,timeout=60) as r: data=r.read()
        if hashlib.sha256(data).hexdigest()!=asset['sha256']:
            raise ValueError('Asset checksum changed: '+asset['filename']+'; inspect source before updating manifest')
        temp=p.with_suffix(p.suffix+'.part');temp.write_bytes(data);temp.replace(p)
    return dest


if __name__=='__main__':
    print(prepare(Path(__file__).resolve().parents[1]))
