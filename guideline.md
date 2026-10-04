# CAR BBOX ANNOTATION GUIDELINE — Xanh SM / GreenSM

## 0. Document Control

| Trường                  | Giá trị                                                                     |
| ----------------------- | --------------------------------------------------------------------------- |
| Dự án                   | GreenSM Data Centric Challenge                                              |
| Phiên bản               | 1.0 (bản khởi tạo; cần được team/reviewer phê duyệt trước khi khóa dataset) |
| Loại nhãn               | Object detection, bounding box định dạng YOLO                               |
| Người phụ trách quy tắc | Reviewer / người phụ trách annotation của team                              |
| Phạm vi áp dụng         | Ảnh được đưa vào tập dữ liệu của dự án, gồm cả ảnh negative                 |

Mọi annotator phải dùng cùng phiên bản guideline. Quyết định cho ca ngoại lệ phải được ghi vào annotation log; khi thay đổi quy tắc, tăng phiên bản, thông báo cho cả team và rà soát lại các ảnh bị ảnh hưởng trước khi khóa dataset.

## 1. Task Objective & Annotation Philosophy

Tạo bộ nhãn nhất quán để huấn luyện và đánh giá mô hình YOLOv8n nhận diện **xe ô tô đang hoạt động dưới nhận diện Xanh SM / GreenSM** trong ảnh. Ưu tiên độ đúng của đối tượng hơn số lượng box: không bỏ sót xe đủ căn cứ, không gán nhãn xe khác chỉ vì màu tương tự, không đoán nhãn khi thiếu bằng chứng. Annotator và reviewer phải đưa ra cùng quyết định khi gặp cùng một trường hợp.

## 2. Annotation Scope

- **Bắt buộc theo challenge:** chỉ một class `GreenSM`, class ID `0`; mỗi xe thuộc class có đúng một bounding box YOLO. Xe không thuộc class không được gán box.
- Xét mọi xe có thể nhìn thấy trong ảnh, kể cả xe nhỏ, xa, bị che một phần hoặc sát rìa. Ảnh có nhiều xe Xanh SM thì gán riêng từng xe.
- Ảnh không có xe Xanh SM **đủ điều kiện gán nhãn** là ảnh negative/background; không có bounding box. Nếu trong ảnh có đối tượng nghi là Xanh SM nhưng chưa xác minh được, chuyển review trước khi xác nhận là negative.
- Chỉ gán nhãn **xe ô tô thật trong cảnh**; không gán nhãn xe trên màn hình, biển quảng cáo, ảnh in, đồ chơi hoặc hình phản chiếu. Không gán xe máy Xanh SM hoặc phương tiện khác (nếu xuất hiện); các trường hợp khác biệt phạm vi phải được reviewer chốt trước khi mở rộng class.
- Nếu dùng công cụ/model tạo box ban đầu, con người phải xem lại **từng box**, kiểm tra cả xe bị bỏ sót và xe bị gán sai.
- Với ảnh/frame lấy từ video, hạn chế đưa quá nhiều frame gần như giống hệt nhau vào dataset; quản lý nguồn để tránh trùng lặp giữa các tập train/val/test.

## 3. Ontology / Class Definition

| ID  | Tên class | Định nghĩa                                                                                | Không thuộc class                                                                                             |
| --- | --------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `0` | `GreenSM` | Ô tô trong cảnh có đủ dấu hiệu nhìn thấy được để xác định là xe dịch vụ Xanh SM / GreenSM | Ô tô màu xanh/cyan không rõ thương hiệu, xe VinFast cá nhân, xe hãng khác, xe máy, xe trong ảnh in/phản chiếu |

**Nhận diện bằng chứng:** logo/chữ `Xanh SM`, `Green SM`, dấu hiệu nhận diện dịch vụ trên thân xe hoặc biển/đèn nóc còn đọc/nhận ra được là bằng chứng mạnh. Màu sơn đặc trưng, kiểu xe và ngữ cảnh chỉ là dấu hiệu hỗ trợ, **không đủ nếu đứng riêng lẻ**. Không dùng tên file, chú thích nguồn, dự đoán model hay ký ức về cùng chiếc xe ở frame khác làm bằng chứng thay cho nội dung nhìn thấy trong ảnh. Nếu có dấu hiệu mâu thuẫn hoặc thương hiệu không thể xác minh, đưa vào review thay vì đoán.

## 4. Object Eligibility Rules

Gán nhãn khi đồng thời thỏa mãn:

1. Đó là **một ô tô thật** có phần thân hiện trong ảnh.
2. Có đủ chi tiết nhìn thấy được để xác định là xe Xanh SM theo mục 3; không chỉ dựa vào màu hoặc tên ảnh.
3. Có thể khoanh được một vùng xe nhìn thấy với box có diện tích dương, không phải một điểm/đốm mơ hồ.

Không có ngưỡng kích thước pixel cố định: xe nhỏ vẫn gán nếu nhận diện được. Không gán nếu chỉ thấy logo rời, bóng phản chiếu, phần thân quá ít để biết hãng, hoặc dấu hiệu chỉ là suy đoán. Các trường hợp có vẻ phù hợp nhưng chưa đủ chắc chắn phải ghi log và gửi reviewer; không tự tạo nhãn dương hoặc âm theo cảm tính.

## 5. Bounding Box Geometry Rules

- Một xe đủ điều kiện = một box chữ nhật song song với cạnh ảnh. Box bao sát **toàn bộ phần xe thực sự nhìn thấy** (các phần thân, kính, bánh xe nhìn thấy); không chia thành nhiều box cho đầu/thân xe hoặc các mảnh bị che.
- Với xe bị che khuất, lấy hình chữ nhật nhỏ nhất bao các **phần xe nhìn thấy** của cùng xe; có thể có vật che nằm bên trong box, nhưng không kéo box theo phần xe tưởng tượng phía sau vật che.
- Với xe chạm mép ảnh, box dừng tại mép ảnh; không ước lượng phần nằm ngoài ảnh. Không cố lấy người, xe khác, bóng đổ hoặc phần nền vào box. Phụ kiện gắn liền để nhận diện xe (ví dụ đèn nóc) được tính khi thấy rõ; không kéo box vì biển hiệu rời.
- Soát kỹ để mỗi box khớp đúng một xe khi các xe sát nhau; không dùng một box chung cho hai xe và không tạo box trùng lặp.
- Trước khi xuất nhãn, biểu diễn box bằng tọa độ pixel `(x_min, y_min, x_max, y_max)` với `0 ≤ x_min < x_max ≤ W`, `0 ≤ y_min < y_max ≤ H`, trong đó `W, H` là kích thước ảnh. Dòng YOLO xuất ra: `0 x_center y_center width height` với `(x_center, y_center, width, height) = ((x_min+x_max)/(2W), (y_min+y_max)/(2H), (x_max-x_min)/W, (y_max-y_min)/H)`. Bốn giá trị sau class ID phải được chuẩn hóa theo ảnh và nằm trong `[0, 1]`; `width`, `height` phải lớn hơn `0`.

## 6. Visibility & Occlusion Rules

- **Không bị che:** box bao sát phần xe nhìn thấy.
- **Bị che một phần** (người, cây, xe khác, cột...): vẫn gán nếu phần lộ ra đủ xác định là Xanh SM; bao các phần nhìn thấy thuộc cùng một xe, không vẽ box theo hình dáng dự đoán sau vật che.
- **Che nặng:** nếu không còn căn cứ nhận diện đáng tin cậy hoặc không phân định được xe với đối tượng khác, không tự gán; gửi reviewer. Ghi chú loại vật che và phần xe còn thấy nếu cần cho QA.
- Nếu hai xe chồng lấp nhau, đánh giá điều kiện nhận diện của **từng xe** và tạo box riêng cho từng xe đủ điều kiện.

## 7. Truncation Rules

Truncation là xe nằm một phần **ngoài khung ảnh**, khác với occlusion do vật thể trong ảnh che. Nếu phần còn lại đủ nhận diện thì gán box theo đúng phần còn nằm trong ảnh, cắt tại biên. Xe bị cắt ở góc ảnh hay sát mép áp dụng cùng quy tắc, không mở rộng box ra ngoài ảnh. Nếu chỉ thấy mảnh xe không đủ xác định, chuyển review hoặc loại theo quyết định của reviewer. Nếu đồng thời bị che và cắt, áp dụng cả mục 6 và mục 7.

## 8. Difficult / Ambiguous Cases

| Tình huống                                        | Cách xử lý                                                                                    |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Xe màu cyan/xanh, không thấy dấu hiệu thương hiệu | Không gán chỉ vì màu; nếu có nghi vấn thực sự, gửi reviewer.                                  |
| Xe VinFast cùng mẫu với taxi Xanh SM              | Không gán chỉ vì mẫu xe; cần bằng chứng nhận diện dịch vụ.                                    |
| Logo/chữ quá mờ, ngược sáng, bị che               | Phóng to ảnh gốc để kiểm tra, không suy từ tên file; chưa rõ thì gửi reviewer.                |
| Xe rất xa/nhỏ nhưng còn nhận diện được            | Gán một box sát phần xe nhìn thấy.                                                            |
| Xe hư hỏng/đổi màu, biển hiệu tháo rời            | Chỉ gán khi bằng chứng Xanh SM vẫn đủ rõ; nếu không, gửi reviewer.                            |
| Nhiều xe dính nhau, khó phân ranh                 | Dùng mép xe thấy được để tách từng box; nếu không xác định được đâu là từng xe, gửi reviewer. |

Reviewer có thể quyết định gán hoặc không gán cho trường hợp cụ thể dựa trên **chính ảnh đó**; lưu lý do và bằng chứng trong log để các ca tương tự về sau được xử lý thống nhất.

## 9. Scene-specific Edge Cases

- **Đường đông xe/bãi đỗ:** rà soát từng ô tô, kể cả xe phía sau, không khoanh cụm xe thành một box.
- **Đêm/mưa/sương mù/chói sáng:** chỉ dựa vào dấu hiệu thực sự quan sát được; không suy từ màu ánh đèn hoặc ngữ cảnh đường phố.
- **Kính, gương, màn hình và quảng cáo:** xe chỉ xuất hiện dưới dạng phản chiếu/hình hiển thị không thuộc phạm vi; nếu xe thật đồng thời xuất hiện trong cảnh, chỉ gán phần xe thật.
- **Xe tương tự thương hiệu trong ảnh negative:** giữ làm hard negative khi đã xác nhận không có xe Xanh SM đủ điều kiện; không biến ca chưa rõ thành negative mà không qua review.
- **Ảnh gần trùng từ cùng nguồn/video:** không cần thay đổi quy tắc box; khi chọn dữ liệu, tránh lặp quá mức và tránh để các frame gần trùng lọt sang các tập dữ liệu khác nhau.

## 10. Attributes & Metadata

Challenge chỉ yêu cầu **một class và bounding box**, không thêm class/attribute vào file label YOLO. Các thông tin phục vụ QA (nếu có) lưu riêng trong annotation log: `filename | annotator | issue_type | decision | reviewer | guideline_version | notes/evidence`. Có thể ghi `occlusion`, `truncation`, `small/far`, `uncertain`, `negative` trong `issue_type`, không xem đây là class. Dùng đúng tên file ảnh để truy vết và ghi quyết định reviewer trước khi đóng một ca mơ hồ.

## 11. Decision Trees

```text
Có ô tô thật nhìn thấy trong ảnh?
├─ Không → Không gán box; kiểm tra ảnh có đối tượng nghi vấn trước khi xác nhận negative.
└─ Có → Xét từng ô tô:
   ├─ Có đủ bằng chứng nhìn thấy để xác định Xanh SM?
   │  ├─ Có → Phần xe nhìn thấy đủ để đặt box?
   │  │  ├─ Có → Gán 1 box cho xe; nếu bị che/cắt thì theo mục 6–7.
   │  │  └─ Không → Gửi reviewer, không đoán box.
   │  ├─ Rõ ràng không → Không gán xe đó.
   │  └─ Chưa rõ → Ghi log, gửi reviewer; chưa chốt negative.
   └─ Lặp lại cho mọi xe khác trong ảnh.
```

Sau khi xét hết ảnh: nếu không có xe nào đủ điều kiện **và không còn ca chờ review**, xác nhận ảnh negative. Nếu có ca chờ review, chưa khóa nhãn ảnh.

## 12. Positive / Negative Examples

Các ví dụ sau là **tình huống minh họa quy tắc**, không phải kết luận nhãn cho một file cụ thể trong `data/`:

| Tình huống                                                        | Kết quả                                                |
| ----------------------------------------------------------------- | ------------------------------------------------------ |
| Ô tô thấy rõ chữ/logo Xanh SM trên thân, dù bị người che một phần | Positive: 1 box quanh phần xe nhìn thấy.               |
| Hai xe có dấu hiệu GreenSM rõ ràng trong cùng ảnh                 | Positive: 2 box, mỗi xe 1 box.                         |
| Xe Xanh SM cắt bởi mép ảnh nhưng logo và phần thân còn rõ         | Positive: box dừng tại mép ảnh.                        |
| Xe cyan không thấy bất kỳ dấu hiệu dịch vụ Xanh SM nào            | Negative cho xe đó: không gán box.                     |
| Xe VinFast cá nhân hoặc taxi hãng khác                            | Negative cho xe đó: không gán box.                     |
| Ảnh đường phố không có ô tô Xanh SM, đã rà soát hết xe            | Negative image: không có box.                          |
| Xe xanh rất xa, không đọc được dấu hiệu nhận diện                 | Chưa kết luận positive; đưa reviewer nếu còn nghi vấn. |

## 13. Common Annotation Errors

- Gán mọi xe màu xanh/cyan hoặc mọi xe VinFast là `GreenSM`.
- Bỏ sót xe nhỏ, xe sau vật che, xe ở mép ảnh; hoặc gán cả xe khi chỉ có một phần mơ hồ.
- Một xe có nhiều box, nhiều xe chung một box, box bao thêm người/xe bên cạnh hoặc box suy đoán cả phần bị che/ngoài ảnh.
- Nhầm phản chiếu/quảng cáo với ô tô thật; dùng tên file hoặc kết quả model thay bằng chứng trong ảnh.
- Xuất tọa độ pixel thay cho YOLO chuẩn hóa, dùng sai class ID hoặc để box vượt biên.
- Đánh dấu negative trong khi ảnh vẫn còn trường hợp chưa được reviewer chốt.

## 14. Quality Assurance Rules

Annotator tự kiểm tra toàn bộ ảnh và box trước khi bàn giao; reviewer kiểm tra lại nhãn và các ca đặc biệt. Chỉ khóa phiên bản dataset sau khi QA hoàn tất.

- [ ] Ảnh map đúng file label cùng tên cơ sở (đổi đuôi sang `.txt`); ảnh negative có file label rỗng nếu pipeline yêu cầu file tương ứng, tuyệt đối không có dòng box.
- [ ] Tất cả box dùng class ID `0`, đúng cú pháp `0 x_center y_center width height`, giá trị hữu hạn, tọa độ trong `[0,1]`, width/height dương.
- [ ] Không bỏ sót xe Xanh SM đủ điều kiện, kể cả xe xa, nhỏ, che khuất hoặc bị cắt mép.
- [ ] Không gán xe hãng khác, xe chỉ giống màu, xe máy hoặc hình xe không thật trong cảnh.
- [ ] Mỗi xe đúng một box; không box trùng hoặc box gộp nhiều xe.
- [ ] Box ôm sát phần nhìn thấy, không suy đoán phần khuất/ngoài ảnh, không lấy dư nền quá nhiều.
- [ ] Ảnh negative đã được rà soát, không còn đối tượng nghi vấn chưa qua review.
- [ ] Quyết định về occlusion, truncation và ca mơ hồ thống nhất với guideline hiện hành.
- [ ] Ca đặc biệt có filename, quyết định reviewer, phiên bản guideline và ghi chú/screenshot khi cần làm bằng chứng QA.
- [ ] Nếu dùng box sinh tự động, đã rà soát từng box và tìm xe bị bỏ sót.

## 15. Escalation & Exception Policy

Khi không thể xác định class hoặc ranh giới xe theo các mục trên: **không đoán**. Ghi vào log `filename | annotator | issue_type | decision (pending) | reviewer | guideline_version | notes/evidence`, mô tả phần xe/dấu hiệu đang thấy và câu hỏi cần chốt; gửi reviewer xem ảnh gốc. Reviewer ghi quyết định `label` / `do not label` / `exclude image` kèm lý do và cách đặt box nếu cần. `Exclude image` chỉ dùng khi không thể giải quyết an toàn; không tự biến ảnh chưa rõ thành negative. Nếu phát hiện một kiểu ca lặp lại, cập nhật guideline theo mục 16 và rà lại tất cả ảnh cùng loại đã xử lý trước đó.

## 16. Change Log

| Phiên bản | Thay đổi                                                                                            | Phạm vi cần rà soát                                                                                |
| --------- | --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| 1.0       | Tạo guideline ban đầu cho một class `GreenSM`, box YOLO, quy tắc nhận diện/che khuất/cắt mép và QA. | Team phê duyệt quy tắc trước khi khóa nhãn; rà soát toàn bộ dữ liệu đã gán theo quy tắc cũ nếu có. |

Khi chỉnh sửa: ghi phiên bản mới, ngày, người duyệt, mô tả thay đổi và danh sách ảnh/nhãn phải kiểm tra lại. Không khóa dataset cho đến khi những nhãn bị ảnh hưởng đã được reviewer xác nhận.
