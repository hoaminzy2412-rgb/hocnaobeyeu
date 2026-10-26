# Kết nối game bên ngoài với kết quả học tập

## Phạm vi

- Nhập **JSON** tạo trò chơi gốc trong hệ thống: hệ thống tự chấm đáp án ở máy chủ và đưa vào bảng thi đua.
- Tải **HTML một tệp** hoặc dán **link HTTPS**: game chạy trong iframe. Chỉ nhận được điểm nếu tác giả game thực hiện giao thức dưới đây.
- Không có cách chung để lấy điểm từ mọi link Canva, Wordwall, YouTube hoặc website bất kỳ. Website ngoài có thể chặn iframe hoặc cần cookie/quyền không được cấp trong khung cách ly. Khi đó dùng nút Mở trang game, kết quả ngoài cửa sổ riêng không tự ghi nhận.
- Bản này chưa hỗ trợ tải gói ZIP, SCORM hoặc H5P. Có thể đưa game HTML tự chứa và JSON vào kho. Tệp HTML có thể dùng tài nguyên HTTPS/data URI được phép, nhưng nên nhúng tài nguyên vào cùng tệp để dễ chạy.

## Giao thức postMessage

1. Khi sẵn sàng, game gửi đến trang cha:

```javascript
parent.postMessage({type: 'hocnaobeoi:ready'}, '*');
```

2. Web gửi về game, không kèm tên trẻ, mã học sinh hoặc mật khẩu:

```javascript
{
  type: 'hocnaobeoi:init',
  nonce: 'chuoi_ngau_nhien_cua_luot_choi',
  preview: false
}
```

3. Game lắng nghe chỉ từ `parent`, lưu nonce của lượt chơi:

```javascript
let currentNonce = '';
let preview = true;
window.addEventListener('message', event => {
  if (event.source !== parent || event.data?.type !== 'hocnaobeoi:init') return;
  currentNonce = event.data.nonce;
  preview = event.data.preview;
});
```

4. Khi hoàn thành, game gửi số câu đúng và tổng số câu:

```javascript
if (!preview && currentNonce) {
  parent.postMessage({
    type: 'hocnaobeoi:result',
    nonce: currentNonce,
    correct: 4,
    total: 5
  }, '*');
}
```

`correct` và `total` phải là số nguyên; `0 ≤ correct ≤ total ≤ 1000`, total > 0. Không truyền `student_id`, tên trẻ hoặc token đăng nhập vào game.

## Cách thử với tệp mẫu

1. Đăng nhập admin hoặc giáo viên.
2. **Game và bài tập → Tải game HTML**.
3. Chọn `samples/game-dem-qua.html`, đặt tên game và đánh dấu **Game hỗ trợ giao thức gửi kết quả**.
4. Lưu vào kho và giao cho một lớp/học sinh.
5. Dùng vai phụ huynh, mở bài và chơi hết ba câu.
6. Điểm lưu vào **Chi tiết bài làm**, trạng thái **chờ cô xác nhận**.
7. Giáo viên kiểm tra, vào **Nhận xét**, đánh dấu xác nhận kết quả game ngoài. Điểm mới được đưa vào thi đua.

## Quy tắc ghi nhận

- Iframe không có quyền đọc tài khoản, cơ sở dữ liệu hoặc cookie ứng dụng.
- HTML tải lên chạy với CSP sandbox và không có `allow-same-origin`.
- Trang cha chỉ nhận sự kiện từ đúng `contentWindow` của iframe đang mở và đúng nonce.
- Máy chủ kiểm tra phiên phụ huynh, quyền học sinh, lượt giao, nonce và ngăn nộp lại một lượt đã hoàn thành.
- Thời gian do máy chủ tính từ bắt đầu đến khi nhận kết quả, không tin đồng hồ game.
- **Điểm của game ngoài là dữ liệu game tự báo**, không phải máy chủ tự chấm được. Nonce giúp gắn đúng lượt chơi, không chứng minh điểm đúng. Vì vậy cần giáo viên kiểm tra trước khi xếp hạng.
- Link hoặc HTML không có giao thức: chỉ mở trải nghiệm, không tự tạo lượt hoàn thành/điểm giả.

## Tệp JSON để chấm trực tiếp

Cấu trúc trong `samples/game-mau.json`. Mỗi câu có `question`, `options` (2–4 lựa chọn) và `answer` (chỉ số bắt đầu từ 0). Dùng **Nhập JSON**, kiểm tra rồi **Lưu vào kho**. Với cách này, phụ huynh không nhận đáp án đúng trước khi làm bài; máy chủ tự tính điểm từ bộ đáp án đã lưu.
