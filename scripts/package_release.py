"""Produce reviewable portable/source artifacts using an explicit public allowlist."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import ssl
import subprocess
import sys
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app_runtime import APP_SLUG,VERSION

PUBLIC_ROOT_FILES = ['.gitignore','.gitattributes','README.md','README.zh-CN.md','LICENSE','THIRD_PARTY_NOTICES.md',
    'CHANGELOG.md','RELEASE_NOTES.md','SECURITY.md','CONTRIBUTING.md','requirements.txt','requirements-build.txt',
    'settings.example.json','team_map.json','injury_types.json','nba_teams.json','使用说明.txt',
    'app_runtime.py','app_main.py','app_ui.py','i18n.py','ui_theme.py','dialogs.py','steam_discovery.py','operations.py','baseline_tools.py',
    'launch_nba.py','sync_nba.py','fetch_source.py','nba_reconcile.py','preview_sync.py','roster_file.py',
    'save_container.py','schedule_notice.py','usage_notice.py','game_setup.py']
PUBLIC_DIRS=['assets','licenses','locales','profiles','scripts','packaging','docs','.github']


def public_files():
    files=[ROOT/name for name in PUBLIC_ROOT_FILES]
    for folder in PUBLIC_DIRS:
        files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
    for file in files:
        if not file.is_file():
            raise FileNotFoundError(file)
    return sorted(files)


def archive_tree(folder,path,prefix):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for file in sorted(folder.rglob('*')):
            if file.is_file():
                archive.write(file,str(Path(prefix)/file.relative_to(folder)))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--build-root',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--prepare-only',action='store_true')
    args=parser.parse_args()
    build,output=Path(args.build_root),Path(args.output)
    output.mkdir(parents=True,exist_ok=True)
    dist=build/'dist'/APP_SLUG
    licenses=dist/'licenses'
    licenses.mkdir(exist_ok=True)
    python_license=Path(sys.base_prefix)/'LICENSE.txt'
    if python_license.is_file():
        shutil.copy2(python_license,licenses/'Python-LICENSE.txt')
    for name,dist_name in [('psutil','psutil'),('PyInstaller','pyinstaller')]:
        package=importlib.metadata.distribution(dist_name)
        for file in package.files or []:
            if any(part.lower() in ('licenses','license','copying','license.txt') for part in file.parts):
                source=package.locate_file(file)
                if source.is_file():
                    shutil.copy2(source,licenses/(name+'-'+source.name))
    tcl=Path(sys.base_prefix)/'tcl'
    for folder in ('tcl8.6','tk8.6'):
        source=tcl/folder/'license.terms'
        if source.is_file():
            shutil.copy2(source,licenses/(folder+'-license.terms'))
    # Python HTTPS still uses OpenSSL; use the notice matching this build runtime.
    openssl_version=ssl.OPENSSL_VERSION.split()[1]
    if not ssl.OPENSSL_VERSION.startswith('OpenSSL ') or not openssl_version.replace('.','').isalnum():
        raise RuntimeError('Review the license for this TLS runtime: '+ssl.OPENSSL_VERSION)
    license_name='OpenSSL-'+openssl_version+'-LICENSE.txt'
    bundled_license=ROOT/'licenses'/license_name
    license_url='https://raw.githubusercontent.com/openssl/openssl/openssl-'+openssl_version+'/LICENSE.txt'
    if bundled_license.is_file():
        license_data=bundled_license.read_bytes()
    else:
        with urllib.request.urlopen(license_url,timeout=30) as response:
            license_data=response.read(65537)
        if len(license_data)>65536 or b'Apache License' not in license_data:
            raise RuntimeError('Review the license for this OpenSSL build before packaging.')
    (licenses/license_name).write_bytes(license_data)
    shutil.copy2(ROOT/'licenses/OpenSSL-NOTICE.md',licenses/'OpenSSL-NOTICE.md')
    (licenses/'OpenSSL-component.json').write_text(json.dumps(dict(version=ssl.OPENSSL_VERSION,
        source=license_url,license=license_name,sha256=hashlib.sha256(license_data).hexdigest()),indent=2)+'\n',encoding='utf-8')
    for file in ('README.md','README.zh-CN.md','LICENSE','THIRD_PARTY_NOTICES.md','RELEASE_NOTES.md'):
        shutil.copy2(ROOT/file,dist/file)
    if args.prepare_only:
        return
    source=output/'source'/APP_SLUG
    source.mkdir(parents=True,exist_ok=True)
    selected = public_files()
    for file in selected:
        target=source/file.relative_to(ROOT)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(file,target)
    with zipfile.ZipFile(output/f'{APP_SLUG}-{VERSION}-source.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for file in selected:
            archive.write(file,str(Path(APP_SLUG)/file.relative_to(ROOT)))
    archive_tree(dist,output/f'{APP_SLUG}-{VERSION}-windows-x64-portable.zip',APP_SLUG)
    installer=build/f'release/{APP_SLUG}-{VERSION}-windows-x64-setup.exe'
    shutil.copy2(installer,output/installer.name)
    unpacked=output/'portable'/APP_SLUG
    shutil.copytree(dist,unpacked,dirs_exist_ok=True)
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    artifacts=[]
    for file in sorted(output.iterdir()):
        if file.is_file() and file.suffix in ('.zip','.exe'):
            artifacts.append(dict(file=file.name,bytes=file.stat().st_size,sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
    (output/'SHA256SUMS.txt').write_text(''.join(f'{f["sha256"]}  {f["file"]}\n' for f in artifacts),encoding='utf-8')
    (output/'release-manifest.json').write_text(json.dumps(dict(version=VERSION,source_revision=revision,
        artifacts=artifacts,published=False,installed=False,game_started=False,
        rights_review='Scoped implementation provenance documented. Provider and external-game-modification terms remain disclosed considerations; acknowledgement is not third-party permission.',
        validation='Windows artifacts built; no automated tests added or run. Runtime integrity checks retained. Local installation and update-only execution are recorded separately in release delivery notes. No game launch; UI interaction and Steam in-game adoption remain unverified.'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    shutil.copy2(ROOT/'RELEASE_NOTES.md',output/'REVIEW.md')
    print(json.dumps(dict(version=VERSION,artifacts=artifacts),ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
