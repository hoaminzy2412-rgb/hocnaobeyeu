# Phân tích giao diện V4 theo yêu cầu của cô Hoa

## Phong cách chung

- Ảnh minh họa 3D có bé trai, bé gái đeo cặp đến trường; vườn hoa, thỏ, cầu vồng, trường học. Dùng tại trang đăng nhập, banner và thẻ học liệu.
- Chữ là **Arial/Helvetica**, không dùng kiểu chữ trang trí khó đọc. Nội dung chính khoảng 17–20 px, tiêu đề 25–49 px, nút bấm 15–17 px tùy màn hình; ghi chú nhỏ hơn.
- Hồng–xanh–vàng pastel, nút bo tròn, icon trực quan. Hiệu ứng nhẹ có tắt theo tùy chọn giảm chuyển động của thiết bị.
- Menu trái trên máy tính; thu gọn bằng ☰ trên màn hình nhỏ. Chữ, nút, số liệu là thành phần web thật, không phải chụp ảnh mẫu làm nền.

## Các mục đã triển khai

| Mục | Chi tiết chức năng | Phần mã chính |
|---|---|---|
| Trang chủ | Banner 3D, số lớp/trẻ/bài làm/nhận xét từ dữ liệu thật, học liệu và thông báo gần đây | `renderPage` trong app.js; `.hero`, `.stats` trong CSS |
| Trường / Năm học | Admin nhập tên, địa chỉ, điện thoại, hiệu trưởng; thêm/sửa năm học, chọn năm đang dùng | `POST /api/school`, `/api/years` |
| Khối học | Nhà trẻ, mẫu giáo bé/nhỡ/lớn; thêm/sửa khối và độ tuổi | `grades`, `gradeEditor`, `/api/grades` |
| Lớp học | Tạo/sửa lớp, chọn khối/năm học/giáo viên; xem danh sách trẻ | `classEditor`, `/api/classes` |
| Giáo viên | Admin tự nhập tài khoản, mật khẩu; sửa tên, đặt lại mật khẩu, khóa/mở; phân công ở lớp | `teacherEditor`, `/api/teachers`, `/api/teachers/reset`, `/api/teachers/status` |
| Học sinh / Phụ huynh | Admin thêm trẻ; máy chủ tự sinh mã và tài khoản, PIN bốn số cuối; hiển thị thông tin cho gia đình; sửa/xóa có kiểm tra liên kết | `studentEditor`, `/api/students`, `/api/parents/reset` |
| Game và bài tập | Các tab tạo thủ công, tải HTML, MP3, MP4, link, AI, JSON; có loại văn bản trong biểu mẫu | `resourceEditor`, `aiEditor`, `jsonImport`, `/api/resources`, `/api/ai/generate` |
| Kho game học mà chơi | Kho dùng chung với biên soạn, tìm kiếm/lọc loại, xem thử/giao bài, sửa/xóa khi phù hợp | `renderResources`, `resourceCard` |
| Giao bài tập | Lớp/cá nhân; admin thêm phạm vi toàn trường; hạn và lời dặn, thông báo cho gia đình | `assignEditor`, `/api/assignments` |
| Nghe thơ truyện cùng bé | Kho MP3/MP4, nghe/xem trực tiếp, có thể giao thành bài | `resources.category=stories` |
| Giai điệu của bé | Kho MP3/MP4 riêng cho âm nhạc | `resources.category=music` |
| Kết quả thi đua | Số bài hoàn thành, số câu đúng/tổng, thời gian, xếp hạng; mỗi bài chọn một lượt tốt nhất | `ranking` phía máy chủ, trang `rankings` |
| Chi tiết bài làm | Bài nộp văn bản/tệp, đáp án, điểm, thời gian, trạng thái điểm game ngoài, nhận xét/sao, xuất CSV | `/api/plays/start`, `/api/attempts`, `/api/reviews` |
| Nhận xét của cô | Theo danh sách lớp, từng bài, hoặc tin nhắn riêng; thông báo đến phụ huynh | `classComment`, `/api/class-reviews` |
| Thông báo của cô | Toàn trường hoặc lớp; đính kèm một ảnh PNG/JPG; sửa/xóa theo quyền | `newsEditor`, `/api/news` |
| Tin nhắn | Hai chiều, theo từng gia đình, cập nhật theo chu kỳ/làm mới | `/api/messages`, `/api/messages/read` |
| Ban giám khảo | Không mật khẩu, dữ liệu riêng, đổi admin/giáo viên/phụ huynh | `/api/demo/start`, `/api/demo/switch` |

## Quyền và quan hệ dữ liệu

- Admin quản lý trường; giáo viên chỉ nhìn các lớp, hồ sơ, bài làm và gia đình được phân công. Kho học liệu được dùng chung trong trường.
- Mỗi lớp có một giáo viên phụ trách; mỗi giáo viên có thể phụ trách nhiều lớp.
- Mỗi học sinh mới có một tài khoản gia đình tự tạo. Các liên kết cũ từ V2 được giữ.
- Học liệu gắn lượt giao; lượt giao gắn lớp hoặc học sinh; lượt bắt đầu gắn phiên phụ huynh, học sinh và nonce; bài làm lưu điểm và thời gian ở máy chủ.
- Game native dùng đáp án ở máy chủ. Game bên ngoài tự báo điểm được phân loại riêng, không tự vào thi đua.
- Thông báo ảnh và tệp học liệu có đường dẫn kiểm tra quyền; không mở thẳng thư mục dữ liệu ra ngoài.

## Những giới hạn cần biết để trình diễn đúng

1. AI chỉ sinh bộ câu hỏi JSON từ API đã cấu hình, chưa sinh mọi loại game tự do hoặc ảnh/video.
2. Dán link không đồng nghĩa lấy được điểm; xem `KET_NOI_GAME.md` và game mẫu để tích hợp.
3. HTML tải lên là một tệp tự chứa; chưa đọc ZIP, SCORM, H5P.
4. Ảnh nhân vật phong cách 3D là ảnh tĩnh với hiệu ứng CSS nhẹ; không phải mô hình 3D tương tác.
5. Tải tệp tối đa 25 MB; khả năng phát MP4 còn phụ thuộc codec/trình duyệt.
6. Đây là source code để chạy/kiểm thử, chưa được host công khai. Cần triển khai máy chủ/HTTPS để gia đình truy cập từ nhà.
7. Hình minh họa và bố cục được làm mới theo tinh thần ảnh cô gửi; không sao chép đúng từng điểm ảnh.

## Kịch bản thử đầy đủ

1. Vào khu giám khảo, vai Admin, xem Trường/Năm học/Khối/Lớp.
2. Tạo giáo viên, phân công lớp; thêm trẻ và xem mã/PIN được sinh.
3. Tạo game bằng nhập JSON mẫu, lưu và giao cho lớp hoặc cá nhân.
4. Chuyển Phụ huynh, làm bài đến khi nhận điểm.
5. Chuyển Giáo viên, xem bài làm, nhận xét và mở bảng thi đua.
6. Nhận xét theo danh sách lớp, nhắn gia đình, đăng thông báo kèm ảnh.
7. Tải `samples/game-dem-qua.html`, chọn hỗ trợ kết nối; giao/cho chơi để xem trạng thái điểm ngoài chờ xác nhận.
8. Khi dùng tài khoản thật và đã có API, thử một lần Tạo game AI, kiểm tra bản nháp rồi lưu.

## Nâng cấp trực quan và ghi âm ở V4

| Vùng/chức năng | Thay đổi |
|---|---|
| Màn hình chơi | Ba nền 3D vườn ong/đại dương/sân khấu; câu hỏi trên khung sáng; thẻ đáp án có nhân vật trang trí; có dấu chọn và tiến độ |
| Trình phát | Nút phát có tiếng, bật/tắt tiếng, thanh âm lượng; giữ điều khiển gốc cho MP3/MP4 |
| Thu âm | Xin quyền micro theo thao tác, đồng hồ, tạm dừng/tiếp tục, dừng, nghe lại, thu lại, tải về |
| Nộp bài | Bản thu riêng trong `attempts.recording_id`; tệp phụ ở `file_id`, tránh ghi đè |
| Nghe bài của trẻ | Audio player trực tiếp trong danh sách kết quả và chi tiết bài làm; kiểm tra quyền khi tải |
| Tự luyện | Gia đình tự mở kho thơ/truyện hoặc âm nhạc để thu/nộp; bài tự luyện tách khỏi thi đua |

`v4.js` mở rộng giao diện V3 và được tải sau `app.js`, `audio-recorder.js`. Khởi tạo ứng dụng diễn ra sau khi các phần này được tải. Ảnh WebP mới nằm ở `static/assets/garden-game.webp`, `ocean-game.webp`, `music-game.webp`.
