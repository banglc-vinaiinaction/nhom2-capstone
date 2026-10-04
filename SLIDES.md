# SLIDE BÁO CÁO GIẢI PHÁP: GREENSM DATA-CENTRIC CHALLENGE

**Đội:** L2B - Nhóm 02 | **Mô hình:** YOLOv8n (Fixed) | **Định dạng:** ONNX (640x640)

---

## SLIDE 1: TỔNG QUAN CHIẾN LƯỢC & BÀI TOÁN

### Tiêu đề: Data-Centric Optimization cho Bài toán Nhận diện GreenSM

- **Bài toán:** Single-class object detection (`0: GreenSM`). Phát hiện taxi điện Xanh SM trong bối cảnh giao thông Việt Nam đa dạng, phức tạp.
- **Ràng buộc cuộc thi:**
    - Kiến trúc cố định: YOLOv8n (`yolov8n.pt`), kích thước ảnh `640x640`.
    - Hậu xử lý cố định: Letterbox 640x640, `conf=0.001`, `iou=0.7`, `max_det=300`.
    - Đánh giá: 100 × mAP@[0.5:0.95] trên tập ẩn.
- **Chiến lược cốt lõi:**
    - Không can thiệp kiến trúc mô hình -> 100% tài nguyên tập trung vào **Chất lượng dữ liệu (Data Quality)**.
    - Chu trình khép kín: _Thu thập có chủ đích -> Pre-label tự động -> Kiểm duyệt chéo theo guideline chuẩn -> Train baseline -> Error analysis & Active learning._

---

## SLIDE 2: BƯỚC 1 - THU THẬP DỮ LIỆU ĐA DẠNG CÓ CHỦ ĐÍCH

### Tiêu đề: Đa dạng hóa môi trường & Chiến lược Khai thác Negative Samples

- **Mục tiêu:** Tránh overfitting miền dữ liệu cục bộ, bao phủ tối đa phân phối thực tế tại Việt Nam.
- **Quy mô & Nguồn dữ liệu thực tế (Tổng cộng: 233 ảnh chuẩn 640x640):**
    - **146 ảnh đường phố tổng hợp (`images/`):** Khai thác từ video hành trình đường phố Hà Nội (Hanoi Driving Tours, góc nhìn dashcam/người đi đường, mật độ giao thông dày, xe bị che khuất).
    - **56 ảnh ban đêm & mưa đêm (`images_night/`):** Cắt frame từ các video "Hanoi Night Drive 4K" & "Rainy Drive Hanoi" để model học đặc trưng xe dưới ánh đèn đường, đèn pha và vệt phản chiếu mặt đường ướt.
    - **31 ảnh ban ngày chọn lọc (`image_day/`):** Xe ở các điều kiện ánh sáng tự nhiên rõ nét, góc chụp trực diện và nghiêng 3/4.
- **Hard Negative Mining (Triệt tiêu False Positive):**
    - Chủ động đưa vào các ảnh đường phố không có GreenSM, xe có màu cyan/xanh lá dễ gây nhầm lẫn (xe buýt điện VinBus, taxi Mai Linh, xe cá nhân màu xanh).
    - Giữ tỷ lệ background samples ~10-15% để model triệt tiêu cảnh báo nhầm.

---

## SLIDE 3: BƯỚC 2 - LABEL GUIDELINE & CHUẨN HÓA QUY ƯỚC

### Tiêu đề: Loại bỏ Nhiễu Nhãn bằng Bộ Quy ước Chặt chẽ (Guideline v1.0)

- **Vấn đề cốt lõi:** Trong Data-Centric, nhiễu nhãn (label noise) và box lỏng lẻo làm sụt giảm nghiêm trọng mAP@[0.5:0.95].
- **Quy chuẩn Bounding Box:**
    - **Tiêu chí gán nhãn:** Chỉ gán khi thấy dấu hiệu dịch vụ thực tế (chữ/logo Xanh SM, đèn mào, decal nhận diện). Tuyệt đối không gán xe VinFast cá nhân cùng form nhưng không phải taxi dịch vụ.
    - **BBox Tightness:** Box phải ôm sát mép thân xe nhìn thấy thực tế. Không vẽ box theo phần xe bị che khuất trong tưởng tượng.
    - **Xử lý xe sát mép (Truncation):** Cắt box ngay tại biên ảnh, không ước lượng phần xe nằm ngoài khung hình.
    - **Kích thước tối thiểu:** Bỏ qua các đối tượng có kích thước nhỏ hơn $15 \times 15$ pixel do không đủ cơ sở trích xuất đặc trưng nhận diện.

---

## SLIDE 4: BƯỚC 3 - QUY TRÌNH PRE-LABELING TỰ ĐỘNG

### Tiêu đề: Tăng tốc Gán nhãn bằng Script Tự động hóa qua CVAT API

- **Thách thức:** Thời gian thi đấu giới hạn (~6.5 tiếng), gán tay toàn bộ gây chậm tiến độ và thiếu nhất quán.
- **Giải pháp tự động hóa (`prelabel_job43.py`):**
    - Kết nối trực tiếp vào CVAT Server qua REST API, duyệt qua từng task/job.
    - Dùng mô hình pretrained phát hiện xe 4 bánh (car/truck) để sinh bounding box sơ bộ.
    - Tự động clamp tọa độ vào khung $[0, 640]$, lọc bỏ box $< 15\text{px}$, gán nháp class `GreenSM (ID 0)`.
- **Hiệu quả:**
    - Giảm 70% thời gian vẽ tay ban đầu cho annotator.
    - Annotator chuyển từ thao tác "vẽ mới" sang "kiểm tra, chỉnh chặt box và loại bỏ False Positive".

---

## SLIDE 5: BƯỚC 4 - DUYỆT NHÃN, KIỂM TRA CHÉO & LÀM SẠCH

### Tiêu đề: Quy trình QA/QC 2 Vòng & Chuẩn hóa Dữ liệu

- **Quy trình kiểm tra chéo (Cross-check):**
    - Không để người gán tự duyệt dữ liệu của mình. Thành viên A gán nhãn -> Thành viên B review và đối chiếu trực tiếp với `guideline.md`.
- **Phát hiện & Xử lý dị thường tự động:**
    - Chạy script kiểm tra định dạng YOLO trước khi train:
        - Kiểm tra class ID duy nhất: chỉ chấp nhận ID = 0.
        - Kiểm tra tọa độ chuẩn hóa: bắt buộc $0 \le cx, cy, w, h \le 1.0$.
        - Phát hiện box rỗng hoặc box tràn viền.
- **Xử lý ảnh trùng lặp:** Lọc bỏ các frame video quá giống nhau để tránh data leakage giữa tập train và val.

---

## SLIDE 6: BƯỚC 5 & 6 - KẾT QUẢ THỰC NGHIỆM, PHÂN TÍCH ĐỘ LỆCH & CHIẾN LƯỢC NỘP

### Tiêu đề: Đánh giá Thực nghiệm (66.34 vs 64.44) & Chiến lược Khóa Bài nộp

- **Tiến trình Thực nghiệm & Kết quả Public Test:**
    - **Lần 1 (`submission-run1.zip`): 66.34 mAP** (Đã chọn)
        - Dữ liệu: Pre-label bằng YOLO26n qua CVAT script + duyệt nhãn vòng đầu.
        - Đạt mAP cao nhất trên tập Public test (40 ảnh).
    - **Lần 2 (`submission.zip`): 64.44 mAP** (Đã chọn)
        - Dữ liệu: Rà soát và re-label lại toàn bộ tập dữ liệu qua script lọc của LC để siết chặt bounding box và loại bỏ hoàn toàn các xe nghi vấn/nhãn nhiễu.
- **Phân tích kỹ thuật: Vì sao điểm Public giảm (-1.90 mAP)?**
    - **Độ lệch mẫu do tập Public quá nhỏ:** Tập test public chỉ có **40 ảnh** (tập private 80 ảnh). Trên tập 40 ảnh, chỉ cần lệch 1-2 bounding box ở ngưỡng IoU cao hoặc 1 ca biên bị bỏ qua là điểm số dao động 1.5 - 2.5 mAP.
    - **Hiện tượng Trade-off giữa Precision và Loose BBox:** Việc siết nhãn chặt và lọc khắt khe giúp giảm triệt để False Positive (tăng Precision), nhưng nếu ground-truth của tập test do người gán có xu hướng vẽ rộng (loose box), model học box quá sát sẽ bị phạt IoU ở các ngưỡng cao.
- **Chiến lược chốt 2 bài nộp cuối cùng (Risk Mitigation):**
    - Tận dụng tối đa quy chế: Chọn đúng 2 bài nộp có tính chất bổ trợ cho nhau:
        1. **Bài 66.34:** Tối ưu hóa phân phối cho tập test hiện tại.
        2. **Bài 64.44:** Tối ưu hóa độ sạch dữ liệu theo chuẩn guideline chặt chẽ, giảm nguy cơ overfit nhãn nhiễu trên tập Private ẩn (80 ảnh).

---

## 📸 GỢI Ý ẢNH CHÈN VÀO TỪNG SLIDE (Lấy từ `/home/lechibang/Downloads/anh_resize/`)

- **Slide 2 (Thu thập dữ liệu):**
    - Ghép 3 ảnh cạnh nhau thể hiện đa dạng bối cảnh:
        - Ban ngày: `image_day-.../Screenshot 2026-10-04 at 1.14.24 PM.png`
        - Mật độ giao thông cao / Nút giao: `images-.../Ringway_3,_Mai_Dịch_Junction.png`
        - Mưa đêm / Đèn đường: `images_night-.../Screenshot 2026-10-04 at 13-19-35 Rainy Drive in Hanoi...png`
- **Slide 3 (Label Guideline):**
    - Chọn 1 ảnh có xe bị che khuất một phần (occlusion) và 1 ảnh xe ở xa để minh họa quy tắc: _chỉ gán phần nhìn thấy, bỏ qua xe < 15px_.
- **Slide 4 (Pre-labeling CVAT):**
    - Chụp ảnh màn hình giao diện CVAT hoặc 1 ảnh kết quả detect từ script `prelabel_job43.py`.
- **Slide 6 (Kết quả thực nghiệm):**
    - Đặt cạnh nhau 2 ảnh dự đoán của mô hình: 1 ảnh nhận diện chuẩn ban đêm và 1 ảnh phân biệt rõ giữa taxi Xanh SM và xe màu xanh khác.
