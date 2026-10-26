"""Backup database and uploads to backups/. Stop the server first for a complete file snapshot."""
from pathlib import Path
import sqlite3,tempfile,zipfile,datetime
from server import DATA_DIR
if __name__=='__main__':
    if not (DATA_DIR/'school.sqlite3').exists():raise SystemExit('Chưa có dữ liệu để sao lưu.')
    dest=Path(__file__).parent/'backups';dest.mkdir(exist_ok=True)
    archive=dest/('Sao_luu_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.zip')
    with tempfile.TemporaryDirectory() as temp:
        snapshot=Path(temp)/'school.sqlite3'
        with sqlite3.connect(DATA_DIR/'school.sqlite3') as source, sqlite3.connect(snapshot) as target:source.backup(target)
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            z.write(snapshot,'data/school.sqlite3')
            for p in (DATA_DIR/'uploads').glob('*'):
                if p.is_file():z.write(p,'data/uploads/'+p.name)
    print('Đã sao lưu:',archive)
