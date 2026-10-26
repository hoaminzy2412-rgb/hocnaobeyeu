"""Local owner recovery; never exposed as a public HTTP endpoint."""
from getpass import getpass
from server import db,hash_password
if __name__=='__main__':
    name=input('Tên đăng nhập giáo viên (mặc định cohoa): ').strip() or 'cohoa'
    password=getpass('Mật khẩu mới (ít nhất 10 ký tự): ')
    if len(password)<10:raise SystemExit('Mật khẩu quá ngắn.')
    if password!=getpass('Nhập lại mật khẩu: '):raise SystemExit('Hai mật khẩu chưa trùng nhau.')
    with db() as c:
        user=c.execute("SELECT id FROM users WHERE username=? AND role='teacher'",(name,)).fetchone()
        if not user:raise SystemExit('Không tìm thấy giáo viên.')
        c.execute('UPDATE users SET password=? WHERE id=?',(hash_password(password),user['id']))
        c.execute('DELETE FROM sessions WHERE user_id=?',(user['id'],))
    print('Đã đổi mật khẩu. Đăng nhập lại bằng mật khẩu mới.')
