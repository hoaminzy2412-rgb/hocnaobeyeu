# V6: giao diện mầm non 3D, chữ lớn

Đọc HUONG_DAN_GIAO_DIEN_V6.txt. Chỉ đổi lớp hiển thị và ảnh, giữ mã chức năng V5.

# Bản V5: ảnh minh họa của giáo viên

Xem HUONG_DAN_ANH_MINH_HOA.txt để nâng cấp và sử dụng. Một ảnh PNG/JPG cho mỗi học liệu; giữ chức năng nghe, xem, thu âm V4.

# Học nào bé ơi! V4 — Trường học nhỏ, niềm vui lớn

Bản nâng cấp cho cô Hoa: giao diện hoạt hình 3D, chữ Arial lớn, quản trị trường–khối–lớp, tài khoản giáo viên, mã học sinh/PIN, kho game, giao bài, thơ truyện/âm nhạc, thi đua và kết nối gia đình.

**Mã nguồn chạy bằng Python 3.11 trở lên và trình duyệt; không cần npm hoặc thư viện Python bên ngoài. Chưa được đưa lên Internet.** AI sinh câu hỏi cần dịch vụ API do cô cấu hình; chưa có khóa thì vẫn tạo thủ công, nhập JSON, tải game hoặc dán link được.


## Những điểm mới của V4: game 3D, âm lượng và thu âm

- Thêm ba bộ cảnh 3D: **Vườn ong**, **Đại dương**, **Sân khấu của bé**; hình ong/thỏ/cá/rùa/gấu/vịt và các thẻ đáp án có minh họa 3D trang trí.
- Giao diện chơi có khung câu hỏi lớn, thẻ đáp án, tiến độ, dấu chọn rõ; có thể đổi cảnh ngay khi chơi mà không mất câu trả lời. Giáo viên chọn cảnh mặc định khi tạo/sửa học liệu chưa giao.
- Tất cả trình phát MP3/MP4 ở Game và bài tập, kho thơ truyện, âm nhạc và bài làm có nút **Phát có tiếng**, **Bật/Tắt tiếng**, thanh âm lượng và thanh điều khiển gốc của trình duyệt.
- Thêm **thu âm → tạm dừng/tiếp tục → dừng → nghe lại → thu lại → nộp bài**. Có thể tải bản thu về máy trước khi gửi.
- Bản thu và tệp đính kèm khác được lưu riêng, không ghi đè nhau. Giáo viên nghe trực tiếp bản thu trong Chi tiết bài làm hoặc hộp Xem bài làm, rồi viết nhận xét.
- Phụ huynh có thể thu bài từ bài cô giao hoặc vào kho thơ truyện/âm nhạc để tự luyện rồi gửi cô. Nếu học liệu đã được giao cho con thì dùng lượt giao đó. Nếu chưa được giao, tạo một bài tự luyện riêng; **không tự tính bài tự luyện vào thi đua**.

### Cách thử nhanh

1. Cô tải một MP3 hoặc MP4 có tiếng vào kho thơ truyện/âm nhạc; giao cho trẻ hoặc để gia đình mở từ kho.
2. Vào vai phụ huynh, mở bài; bấm **Phát có tiếng**.
3. Bấm **Bắt đầu thu âm**, chọn **Cho phép** khi trình duyệt hỏi quyền micro.
4. Cho trẻ đọc/hát, bấm **Dừng và nghe lại**; bấm **Phát có tiếng** ở bản thu để nghe.
5. Có thể **Thu lại**, **Tải bản thu về máy** hoặc nhập thêm lời chia sẻ.
6. Bấm **Gửi bài và bản thu cho cô**; chỉ bước này mới tải bản thu lên máy chủ.
7. Giáo viên mở **Chi tiết bài làm → Xem bài làm** để nghe và nhận xét.

### Điều kiện micro, âm thanh và giới hạn

- Micro cần **HTTPS hoặc localhost** và người lớn cho phép. Mở từ địa chỉ IP LAN bằng HTTP thường không đủ điều kiện thu âm; khi đó có thể dùng ứng dụng thu âm của thiết bị và đính kèm tệp.
- Không tự mở micro khi xem trang. Khi đóng hộp thoại, rời trang hoặc dừng thu, chương trình dừng các track micro. Nếu đang chờ quyền rồi đóng, track được tắt ngay khi yêu cầu quyền trả về.
- Khi bắt đầu thu, bài mẫu tạm dừng để tránh lẫn tiếng. Nếu cần hát theo nhạc, bố mẹ có thể tự bấm phát lại, nên dùng tai nghe phù hợp.
- Khi tạm dừng bản thu, stream micro vẫn được giữ để tiếp tục; bấm Dừng để ngừng hẳn micro.
- Bản thu có giới hạn tệp **25 MB**, tự yêu cầu dừng sau khoảng **10 phút**. Thời điểm thực tế còn phụ thuộc trình duyệt/hệ điều hành, đặc biệt khi thiết bị khóa màn hình.
- Web chọn định dạng trình duyệt hỗ trợ: M4A/MP4 âm thanh, WebM hoặc OGG. Không gán tên MP3 giả cho bản thu. Khi nộp có thể đính kèm MP3, M4A, WebM, OGG, WAV và các tệp bài làm đã hỗ trợ.
- Một bản thu chưa gửi chỉ nằm trong bộ nhớ của trang. Có cảnh báo khi đóng nhưng không có lưu nháp bền vững sau khi đóng trình duyệt. Bố mẹ nên nghe lại và gửi, hoặc tải bản thu về máy.
- Trên iPhone/iPad, mức âm lượng có thể do phím cứng của thiết bị điều khiển; nút bật/tắt tiếng và phát vẫn nằm trên web. Nếu video gốc không có track âm thanh hoặc máy đang tắt loa, nút âm lượng không thể tự tạo tiếng cho video.
- Chưa trộn giọng hát với nhạc nền thành một tệp riêng, chưa nhận diện lời nói/giọng hát và chưa tự chấm phát âm. Giáo viên nghe và nhận xét.
- Các hình 3D là ảnh minh họa/ảnh trang trí, không tự suy ra đáp án đúng hoặc thay đổi nội dung câu hỏi.

Tham khảo kỹ thuật: https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia ; https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/isTypeSupported_static ; https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/Using_HTML5_Audio_Video/Device-SpecificConsiderations/Device-SpecificConsiderations.html

## 1. Cô mở web như thế nào?

### Cách dễ nhất trên Windows

1. Giải nén ZIP ra một thư mục riêng. Không chạy trong tệp nén.
2. Mở thư mục `HocNaoBeOi_V4`, nơi có cả **server.py**, **engine.py** và thư mục **static**.
3. Nhấp đúp **CHAY_TREN_WINDOWS.bat**. Giữ cửa sổ dòng lệnh mở.
4. Trình duyệt tự mở http://localhost:8000 . Nếu không, cô mở địa chỉ này bằng Chrome/Edge.
5. Tài khoản admin: **cohoa**. Mật khẩu ngẫu nhiên xuất hiện trong Terminal khi chạy lần đầu, đồng thời nằm trong `data/TAI_KHOAN_BAN_DAU.txt` trên máy cô.

### Nếu dùng VS Code hoặc máy không nhận lệnh python

1. **File → Open Folder** → mở thư mục có `server.py` và `engine.py`.
2. Bấm mở **server.py**.
3. Nhấn **Ctrl + Shift + P**, tìm **Python: Select Interpreter** và chọn bản Python thực sự cài trên máy.
4. Tiếp tục **Ctrl + Shift + P → Python: Run Python File in Terminal**.
5. Khi hiện địa chỉ máy chủ, mở http://localhost:8000 .

Nếu máy đã nhận Python, dùng **Terminal → New Terminal**:

```bash
python server.py
```

Windows có thể dùng `py -3 server.py`; macOS/Linux dùng `python3 server.py`. Nếu chưa có Python, cài từ python.org; trên bộ cài Windows truyền thống chọn Add python.exe to PATH. Đóng và mở lại VS Code sau khi cài.

**Không chạy bằng Live Server, không chỉ mở index.html.** Python phải chạy để đăng nhập, tải tệp và lưu kết quả. Dừng bằng Ctrl+C; mở lại không mất dữ liệu.

## 2. Chuyển dữ liệu từ V2 hoặc V3

1. Dừng chương trình V2 và tạo bản sao thư mục `data` trước.
2. Giải nén V4 riêng; sao chép **toàn bộ thư mục `data` của V2** vào cạnh `server.py` trong V4.
3. Chạy V4. Chương trình bổ sung các bảng/cột mới, giữ tài khoản, mật khẩu, hồ sơ, bài làm và tệp hiện có.
4. Tài khoản giáo viên đầu tiên của V2 (`cohoa` với bộ mã mặc định) trở thành **admin**. Mật khẩu cũ giữ nguyên.
5. Admin vào Giáo viên để cấp tài khoản, rồi Lớp học → Sửa để phân công.
6. Tài khoản phụ huynh cũ giữ thông tin đăng nhập cũ. Quy tắc mã học sinh/PIN áp dụng cho **học sinh mới được tạo trong V4**; không tự đổi mật khẩu gia đình cũ.

Đừng ghi đè bản sao V2 bằng dữ liệu sau nâng cấp rồi mở ngược lại bằng chương trình V2. Bản sao trước nâng cấp giúp quay lại khi cần.

## 3. Ba vai trò

| Vai trò | Quyền |
|---|---|
| **Admin** | Toàn trường; thông tin trường/năm học/khối; cấp và khóa tài khoản giáo viên; phân công lớp; thêm học sinh và tự tạo tài khoản gia đình; học liệu, giao bài, nhận xét, thông báo toàn trường, cấu hình AI |
| **Giáo viên** | Các lớp được phân công; tạo lớp mới do mình phụ trách; dùng chung kho học liệu trường, tạo học liệu của mình; giao bài lớp hoặc cá nhân; xem/nộp nhận xét, nhắn các gia đình thuộc lớp; thông báo cho lớp |
| **Học sinh/Phụ huynh** | Đăng nhập mã/tài khoản được cấp; xem con và bài được giao; chơi/nộp bài; xem nhận xét, thơ truyện, âm nhạc, thông báo, nhắn giáo viên |

Giáo viên không được cấp tài khoản giáo viên khác, thêm học sinh, thay thông tin trường hoặc giao bài toàn trường. Admin thực hiện các việc đó.

**Ban giám khảo:** bấm nút Trải nghiệm ở màn hình đăng nhập, không cần mật khẩu. Có dữ liệu mẫu riêng và nút đổi vai **Admin / Giáo viên / Phụ huynh**, cùng ô chọn gia đình. Các thay đổi không tác động đến dữ liệu thật. API AI thật và thay cấu hình khóa AI không mở trong khu mẫu; có thể thử Nhập JSON để tạo game. Không gian mẫu gắn với phiên trình duyệt, tối đa 12 giờ, không tự phục hồi sau khi đăng xuất/hết hạn.

## 4. Bắt đầu quản lý trường

### Trường / Năm học

Admin nhập tên trường, địa chỉ, điện thoại, hiệu trưởng. Thêm năm học, chọn năm học đang sử dụng. Đây là một trường trong mỗi không gian tài khoản; bản này không có giao diện quản lý chuỗi nhiều trường chung một admin.

### Khối học

Có sẵn **Nhà trẻ**, **Mẫu giáo bé**, **Mẫu giáo nhỡ**, **Mẫu giáo lớn**. Admin có thể sửa tên/độ tuổi hoặc thêm khối khác.

### Giáo viên

Admin bấm **Cấp tài khoản giáo viên**, tự nhập tên, tên đăng nhập và mật khẩu từ 10 ký tự. Tên đăng nhập dùng chữ thường không dấu, số và `. _ -`. Có sửa tên, đặt lại mật khẩu, tạm khóa/mở khóa. Sau đó vào Lớp học để phân công lớp.

### Lớp học

Tạo/sửa lớp, chọn khối và năm học. Admin chọn giáo viên phụ trách. Một giáo viên có thể quản lý nhiều lớp; bản này một lớp gắn một giáo viên phụ trách. Giáo viên tự tạo lớp được tự phân công lớp đó.

### Học sinh / Phụ huynh

Admin chỉ nhập tên trẻ, chọn lớp, ngày sinh và ghi chú. Hệ thống tự tạo:

- Mã học sinh dạng **HS + năm + 8 chữ số**, duy nhất trong hệ thống.
- Tài khoản gia đình có tên đăng nhập bằng mã học sinh.
- Mật khẩu ban đầu bằng **4 số cuối mã học sinh**, gồm cả số 0 ở đầu nếu có.

Ví dụ: mã **HS202612340056**, mật khẩu **0056**. Đây chỉ là ví dụ, không phải tài khoản có sẵn.

Sau khi tạo, web hiển thị thông tin đăng nhập để cô gửi riêng cho đúng gia đình. Mật khẩu được băm khi lưu, không lưu nguyên văn. Phụ huynh có thể đổi thành mật khẩu ít nhất 10 ký tự trong Cài đặt. Admin có thể đặt lại mật khẩu nếu gia đình quên.

V4 mặc định tạo một tài khoản gia đình riêng cho mỗi học sinh mới; không có biểu mẫu gộp nhiều tài khoản gia đình mới. Những liên kết nhiều con trên một tài khoản cũ của V2 vẫn được giữ.

## 5. Game và các kho học liệu

**Game và bài tập** là nơi biên soạn; **Kho game học mà chơi** hiển thị các học liệu đã lưu. Hai màn hình dùng chung dữ liệu, không tạo hai bản trùng nhau.

| Tab / Loại | Cách dùng |
|---|---|
| **Tạo thủ công** | Nhập 1–30 câu, mỗi câu 2–4 lựa chọn (mẫu mới mặc định 3), chọn đáp án đúng. Trẻ chạm chọn và hệ thống tự chấm |
| **Tải game HTML** | Tải một tệp HTML tự chứa. Không hỗ trợ ZIP/SCORM/H5P. Có tệp mẫu kết nối tại `samples/game-dem-qua.html` |
| **MP3** | Tải âm thanh, phát ngay trong web |
| **MP4** | Tải video, xem trực tiếp trong web |
| **Dán link game** | Lưu link HTTPS. Website ngoài có thể chặn nhúng. Không phải mọi link đều có điểm tự động |
| **Tạo game AI** | Gọi API đã cấu hình, sinh bộ câu hỏi nháp, cô kiểm duyệt rồi Lưu vào kho |
| **Nhập JSON** | Dán hoặc tải JSON câu hỏi do cô/AI chuẩn bị; mở bản nháp, kiểm tra rồi lưu. Có mẫu `samples/game-mau.json` |
| **Bài văn bản** | Nhập nội dung hoặc tải TXT mã hóa UTF-8 từ biểu mẫu Tạo / Tải học liệu |

Mỗi tệp tối đa **25 MB**. Video nên dùng MP4 H.264/AAC; trình duyệt cần hỗ trợ codec thực tế. Nội dung âm thanh/video không tự phát; người dùng bấm nút phát. Học liệu đã giao không được sửa trực tiếp để bảo toàn lịch sử: tạo bản mới khi cần đổi câu hỏi.

### Thơ truyện và âm nhạc

- **Nghe thơ truyện cùng bé**: tải MP3/MP4, chọn kho lưu tương ứng.
- **Giai điệu của bé**: tải MP3/MP4, chọn kho âm nhạc.
- Phụ huynh có thể mở nghe/xem hai kho này mà không cần lượt giao bài.
- Nếu muốn có bài nộp/kết quả, cô giao học liệu đó cho lớp hoặc trẻ. Việc chỉ phát nhạc/xem truyện trong kho không tự tính là đã hoàn thành bài giao.

## 6. AI được cấu hình như thế nào?

Admin → **Cài đặt → Cấu hình API AI**. Điền:

1. Endpoint HTTPS đầy đủ do nhà cung cấp cung cấp, có giao diện **Chat Completions**.
2. Tên model chính xác trong tài khoản nhà cung cấp.
3. API key.

Bản này gửi JSON có `model`, `messages`, xác thực `Authorization: Bearer ...`, đọc kết quả từ `choices[0].message.content`. Nhà cung cấp phải hỗ trợ định dạng này. API chỉ tạo câu hỏi JSON; không tạo ảnh/video hoặc game HTML tùy ý từ một câu lệnh. Không đặt sẵn model không xác minh hoặc khóa miễn phí.

Khóa nằm trong `data/ai_config.json` trên máy chủ, không gửi lại trình duyệt; ô khóa để trống khi sửa thì giữ khóa cũ. Có thể dùng biến môi trường `AI_API_URL`, `AI_MODEL`, `AI_API_KEY` (ưu tiên hơn cấu hình tệp). Không dán khóa vào cuộc trò chuyện, mã JavaScript hoặc Git công khai.

Sau khi sinh, cô kiểm tra ngôn ngữ/đáp án rồi lưu. Nếu hết hạn mức, sai model hoặc sai endpoint, web báo lỗi rõ ràng và không tạo kết quả AI giả. Chưa có API thì dùng tạo thủ công hoặc Nhập JSON từ công cụ AI cô đang dùng. Chí phí API phụ thuộc nhà cung cấp; bản này không kèm ngân sách/khóa API.

## 7. Giao bài và cho trẻ tương tác

- **Admin** chọn giao **toàn trường / lớp / cá nhân**.
- **Giáo viên** chọn **lớp được phân công / cá nhân trong lớp**.
- Chọn học liệu, hạn tùy chọn và lời dặn.
- Bài toàn trường được tạo thành lượt giao ở từng lớp; không có lớp thì chưa giao được.
- Phụ huynh vào **Bài cô giao → Mở bài cho con**, chọn bé và bắt đầu.
- Game gốc: chạm chọn đáp án, Câu tiếp, Hoàn thành.
- Văn bản/MP3/MP4: đọc/nghe/xem rồi nhập câu trả lời hoặc tải bài làm TXT, MP3, MP4, PNG, JPG, PDF.
- Có thể làm nhiều lượt; mỗi lượt được lưu riêng. Có thể nộp sau hạn, giáo viên thấy thời điểm gửi.

## 8. Kết quả thi đua và nhận xét

### Kết quả thi đua

Mỗi học sinh, mỗi bài giao chỉ lấy một lượt: **số câu đúng cao nhất**, rồi **thời gian ngắn nhất** nếu cùng điểm. Xếp hạng theo:

1. Số bài giao đã hoàn thành, giảm dần.
2. Tổng số câu đúng, giảm dần.
3. Tổng thời gian của những lượt được chọn, tăng dần.

Các chỉ số bằng nhau được đồng hạng; trẻ chưa có lượt hoàn thành chưa được gán hạng. Có lọc lớp. Đây là cách tính mặc định của bản V4, chưa có công cụ tùy chỉnh trọng số hay xếp hạng theo tuần/tháng.

Thời gian do máy chủ tính từ lúc bấm Bắt đầu đến khi gửi, **gồm cả thời gian nghỉ hoặc để trang mở**, tối đa ghi nhận 24 giờ/lượt; không phải đo thời gian chú ý học thực tế. Bài văn bản/âm thanh/video có số câu đúng để trống, vẫn tính hoàn thành khi đã nộp hợp lệ.

Phụ huynh xem dữ liệu con mình; bảng thi đua chỉ hiển thị cùng lớp với tên trẻ khác đã thay bằng “Bạn nhỏ …”. Admin xem toàn trường; giáo viên xem các lớp phụ trách.

### Game bên ngoài

Chỉ game thực hiện giao thức trong **KET_NOI_GAME.md** mới gửi được điểm. Điểm tự game báo về được đánh dấu **chờ cô xác nhận**, không vào thi đua ngay. Cô kiểm tra rồi xác nhận trong phần nhận xét bài làm. Web không tự lấy điểm từ một link bất kỳ và không gán điểm giả khi không có kết quả.

### Nhận xét của cô

- **Nhận xét của cô → Nhận xét theo lớp**: chọn lớp, ghi nhận xét ở từng trẻ; bỏ trống trẻ chưa cần gửi.
- **Chi tiết bài làm → Viết nhận xét**: ghi nhận xét riêng bài, chọn sao động viên.
- **Tin nhắn**: trao đổi hai chiều riêng với gia đình trong web.
- **Chi tiết bài làm** có xuất CSV kết quả; dữ liệu thời gian/nguồn điểm hiển thị trên từng bài làm.

Thi đua để động viên, không dùng điểm game để kết luận mức phát triển hay năng lực toàn diện của trẻ.

## 9. Thông báo có ảnh và tin nhắn

- Admin đăng thông báo toàn trường hoặc từng lớp.
- Giáo viên đăng thông báo cho lớp mình phụ trách.
- Đính kèm một ảnh PNG/JPG mỗi thông báo, tải tối đa 25 MB.
- Sửa/xóa thông báo của mình; admin có quyền toàn trường.
- Chuông nhận thông báo bài giao, bài nộp, nhận xét, tin nhắn.
- Trang kiểm tra tin nhắn/chuông khoảng 12 giây/lần khi đang mở, không có hộp thoại; có nút Làm mới. Không gửi email/Zalo/SMS hay thông báo đẩy khi đóng trình duyệt.

## 10. Sao lưu, mật khẩu và vận hành

Dừng web bằng Ctrl+C rồi chạy:

```bash
python backup.py
```

Bản sao nằm trong `backups`, gồm SQLite và thư mục tệp. Không gồm cấu hình API AI; sau khôi phục cần cấu hình lại khóa nếu chưa giữ riêng. Phục hồi khi máy chủ đã dừng: giữ bản sao `data` hiện tại, giải nén bản sao để có `data/school.sqlite3` và `data/uploads`, chạy V4.

Quên mật khẩu admin: dừng chương trình, chạy `python reset_teacher_password.py` trên máy giữ dữ liệu và đặt lại tài khoản `cohoa`. Quên mật khẩu giáo viên/phụ huynh: admin đặt lại trong giao diện. Chương trình không có khôi phục qua email.

Mặc định web chỉ chạy trên máy cô tại localhost. Để phụ huynh dùng từ nhà, cần máy chủ hoạt động liên tục, HTTPS, tên miền, quản lý sao lưu và kiểm tra bảo mật. Không chỉ đưa lên host tĩnh là chạy được. Máy chủ chuẩn Python này dành cho phát triển/thử nghiệm và quy mô thử nhỏ, chưa phải hạ tầng được kiểm định cho trường học trên Internet. PIN bốn số được triển khai theo yêu cầu của cô; phụ huynh nên đổi mật khẩu khi bắt đầu dùng thật.

Biến môi trường: `SCHOOL_DATA_DIR`, `SCHOOL_HOST` (mặc định 127.0.0.1), `PORT` (8000), `SCHOOL_SECURE_COOKIE` (đặt 1 khi dùng HTTPS), `SCHOOL_TEACHER_PASSWORD` (chỉ khởi tạo lần đầu), `SCHOOL_OPEN_BROWSER`, `AI_API_URL`, `AI_MODEL`, `AI_API_KEY`.

Không đưa `data`, `backups`, khóa API hoặc hồ sơ trẻ lên Git công khai. Bản này có băm mật khẩu, phân quyền phía máy chủ, CSRF, cookie HttpOnly/SameSite, giới hạn thử đăng nhập, kiểm tra định dạng tệp và game HTML trong sandbox; chưa có quét virus, MFA hay kiểm định bảo mật độc lập.

## 11. Mã nguồn và kiểm thử

- `server.py`: API V4, phân quyền, tự sinh tài khoản, kho học liệu, AI, bài làm và thi đua.
- `engine.py`: tiện ích chung, schema gốc để nâng cấp từ V2 hoặc V3, phiên đăng nhập và truyền tệp.
- `static/app.js`: giao diện và hành vi; phần V4 mở rộng các chức năng gốc.
- `static/style.css`: Arial, cỡ chữ lớn và bố cục thích ứng máy tính/điện thoại.
- `static/assets/hero-3d.webp`: ảnh 3D tạo riêng bằng công cụ tạo ảnh tích hợp; bản web đã tối ưu dung lượng, không cần mạng ngoài để tải ảnh.
- `samples`: HTML kết nối điểm và JSON câu hỏi mẫu.
- `PHAN_TICH_GIAO_DIEN.md`: ánh xạ yêu cầu sang màn hình/chức năng.
- `KET_NOI_GAME.md`: giao thức tích hợp điểm.

Kiểm thử:

```bash
python -m unittest discover -s tests -v
```

Đã kiểm tra cú pháp Python/JavaScript và các luồng API: tài khoản, PIN, phân công lớp, quyền giáo viên/phụ huynh, giao bài, chấm điểm, nhận xét, tin nhắn, tệp, thông báo ảnh, sandbox/nonce game và cách ly khu mẫu. AI được kiểm tra bằng phản hồi giả lập có kiểm soát, **chưa gọi nhà cung cấp thật** vì chưa có khóa của cô. Mẫu MP3/MP4 trong kiểm thử là dữ liệu kiểm tra đường truyền, không thay thử phát tệp thật.

Chưa chạy đầy đủ kiểm thử trực quan trên Chrome/Edge và điện thoại trong môi trường tạo mã. Cô cần chạy thử với dữ liệu giả, một tệp MP3/MP4 thật, rồi mới dùng chính thức. Bản này không kèm khẳng định hoạt động với mọi game bên ngoài.

Ảnh banner: prompt dùng phong cách hoạt hình 3D, bé gái cặp hồng bên trái, bé trai cặp xanh bên phải, sân trường/vườn hoa/cầu vồng và khoảng trống giữa cho chữ HTML. Tạo bằng công cụ imagegen tích hợp, lưu trong `static/assets/hero-3d.webp`; không phải ảnh trẻ thật. Các hình là minh họa tĩnh phong cách 3D, có chuyển động CSS nhẹ, không phải nhân vật 3D tương tác thời gian thực.

Giấy phép mã: MIT. Mã và học liệu cần người lớn kiểm tra trước khi dùng cho trẻ.

## Kiểm thử bổ sung ở V4

```bash
python -m unittest discover -s tests -v
```

Bộ kiểm tra gồm 8 nhóm API, có thêm nộp bản thu riêng kèm tệp khác, quyền nghe/tải bản thu, các định dạng ghi âm, bài tự luyện và giao diện game.

Nếu có Node.js (chỉ cần cho kiểm thử, không cần để chạy web):

```bash
node --test tests/recorder.test.js
```

Có 5 kiểm thử giả lập về bật micro theo thao tác, tạm dừng/tiếp tục, dừng track, đóng lúc chờ quyền, giữ bản thu cũ khi không cấp quyền thu lại và dừng theo giới hạn thời gian. Đây không phải kiểm thử với micro/loa thật. Chưa kiểm tra trực quan đầy đủ hoặc thu/phát trên mọi điện thoại; cô cần thử thực tế với thiết bị sẽ dùng.

Tệp bổ sung: `static/audio-recorder.js` (quản lý micro), `static/v4.js` (giao diện game, âm lượng và nộp bài thu), `HUONG_DAN_THU_AM.txt`, `GAME_ASSET_PROMPTS.json` (prompt và đường dẫn ba ảnh mới). Toàn bộ ảnh được tạo bằng imagegen tích hợp và lưu cục bộ trong bộ mã; không dùng ảnh trẻ thật.
