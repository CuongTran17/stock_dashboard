HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG

KHOA TÀI CHÍNH KẾ TOÁN 1

QUẢN LÝ VÀ ỨNG DỤNG CƠ SỞ DỮ LIỆU
TRONG TÀI CHÍNH (FINTECH)

Đề tài: Quản lý và ứng dụng dữ liệu trong
website mua bán đồ công nghệ cũ

Giảng viên:  Trần Quốc Khánh

Lớp:  01
Nhóm sinh viên:  05

Các sinh viên:  Nguyễn Trung Dũng

Lương Thanh Hậu
Đỗ Hải Long
Nguyễn Dược Anh Minh
Nguyễn Hữu Việt

B22DCTC020
B22DCTC038
B22DCTC064
B22DCTC074
B22DCTC114

Hà Nội – 2025

MỤC LỤC

PHÂN CÔNG CÔNG VIỆC............................................................................... 3
CHƯƠNG I. TỔNG QUAN VỀ ĐỀ TÀI...........................................................4
1. Lý do chọn đề tài.......................................................................................... 4
2. Yêu cầu về chức năng...................................................................................6
3. Yêu cầu phi chức năng................................................................................. 6
CHƯƠNG II. PHÂN TÍCH VÀ THIẾT KẾ CÁC CHỈ SỐ THỐNG KÊ...... 7
1. Phân tích nhu cầu sử dụng các chỉ số thống kê............................................ 7
2. Dự đoán tổng lượng người dùng, đơn hàng và doanh số thông qua mô hình
ARIMA.............................................................................................................8
2.1.  Lý do lựa chọn mô hình...................................................................... 8
2.2. Cơ sở lý thuyết.....................................................................................9
2.3. Phương trình ARIMA........................................................................ 12
CHƯƠNG III. THIẾT KẾ VÀ TỔ CHỨC HỆ THỐNG ETL............................ 15
1. Mục tiêu của hệ thống ETL dữ liệu............................................................15
2. Quy trình xử lý dữ liệu............................................................................... 15
2.1. Extract................................................................................................ 16
2.2. Transform...........................................................................................17
2.3. Load................................................................................................... 18
2.4. Phân phối, giám sát dữ liệu và tối ưu truy vấn.................................. 19
CHƯƠNG IV. PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG............................21
1. Danh sách các tác nhân và mô tả.......................................................... 21
2. Biểu đồ UseCase tổng quát của hệ thống............................................. 22
3. Biểu đồ Use Case Chi tiết của hệ thống................................................23
4. Mô tả ca sử dụng...................................................................................27
5. Đặc tả ca sử dụng chi tiết......................................................................27
6. Thiết kế mô hình hoạt động.................................................................. 43
7. Bảng thực thể........................................................................................ 59
8. Biểu đồ lớp...........................................................................................71
CHƯƠNG V. CÁC BẢNG THỐNG KÊ.......................................................... 80
1. Người bán............................................................................................. 80
2. Admin................................................................................................... 88
CHƯƠNG VI. KẾT LUẬN............................................................................. 100
1. Thành tựu................................................................................................. 100
2. Hạn chế.....................................................................................................101
3. Hướng phát triển trong tương lai..............................................................102
TÀI LIỆU THAM KHẢO............................................................................... 103

2

PHÂN CÔNG CÔNG VIỆC

STT

Họ và tên

Mã sinh viên

Phân công công việc

Điểm

Nguyễn Trung
Dũng

B22DCTC020

Nguyễn Hữu
Việt

B22DCTC114

Đỗ Hải Long

B22DCTC064

- Xây dựng biểu đồ lớp
- Xây dựng biểu đồ tuần tự
- Xây dựng kịch bản ca sử dụng
- Xây dựng các chỉ số thống kê
- Làm báo cáo

- Xây dựng các chỉ số thống kê
- Xây dựng mô hình ARIMA
- Thiết kế cơ sở dữ liệu
- Làm báo cáo

- Xây dựng biểu đồ lớp
- Lập trình Back-end
- Lập trình Front-end
- Thiết kế cơ sở dữ liệu
- Làm báo cáo

Nguyễn Dược
Anh Minh

Lương Thanh
Hậu

B22DCTC074

- Phác thảo giao diện hệ thống
- Lập trình Front-end

B22DCTC038

- Lập trình Front-end
- Lập trình Back-end
- Thiết kế cơ sở dữ liệu

1

2

3

4

5

10

10

10

10

10

3

CHƯƠNG I. TỔNG QUAN VỀ ĐỀ TÀI

1. Lý do chọn đề tài

Trong bối cảnh thị trường thương mại điện tử ngày càng phát triển mạnh

mẽ, đặc biệt là sự trỗi dậy của phân khúc đồ điện tử cũ, một thị trường tiềm năng

xuất  phát  từ  thói  quen  tận  dụng  tối  đa  giá  trị  đồ  điện tử của tầng lớp thu nhập

trung  bình  ở  Việt  Nam.  Việc  nắm  bắt  và  phân  tích  dữ  liệu  bán  hàng một cách

hiệu  quả trở thành yếu tố then chốt quyết định sự thành công và khả năng cạnh

tranh  của  người bán. Đối với một website chuyên dành cho lĩnh vực đồ điện tử

cũ, nơi mà sự biến động về giá cả và nhu cầu thị trường có thể diễn ra rất nhanh

chóng,  thì việc thiếu một công cụ trực quan và mạnh mẽ để theo dõi các chỉ số

bán  hàng  sẽ  gây  ra  không  ít  khó  khăn  cho  cả  người  bán  và  nhà  quản  lý  sàn.

Chính  vì  lẽ  đó,  chúng  em  lựa  chọn  đề  tài  này  như  một  giải  pháp  cấp  thiết  và

mang lại nhiều lợi ích thiết thực cho website để giải quyết những nhu cầu sau.

Thứ nhất, tính cấp thiết của việc theo dõi hiệu quả bán hàng trong môi trường

cạnh tranh. Thị trường đồ điện tử cũ, dù tiềm năng, nhưng cũng đồng thời chứa

đựng sự cạnh tranh gay gắt từ nhiều nguồn khác nhau, bao gồm các đối thủ trực

tiếp,  các  nền  tảng  thương  mại  điện  tử  lớn  và  cả  những  giao  dịch  mua  bán  cá

nhân. Trong môi trường này, việc hiểu rõ hiệu suất bán hàng của từng sản phẩm,

từng danh mục là vô cùng quan trọng. Một dashboard trực quan sẽ cung cấp cái

nhìn  tổng  quan  và  chi  tiết  về  tình  hình  kinh  doanh,  giúp người bán và quản lý

nhanh  chóng  nhận  diện được những dòng sản phẩm bán chạy, những sản phẩm

khó  bán,  hiệu  quả  của  chiến  lược  định  giá,  từ  đó  đưa  ra  các  quyết  định  kinh

doanh kịp thời và chính xác. Nếu không có một công cụ như vậy, việc đánh giá

hiệu quả sẽ trở nên chậm chạp và dễ dẫn đến những quyết định sai lầm, bỏ lỡ cơ

hội tăng trưởng.

Thứ  hai,  nhu  cầu  tối  ưu  hóa  quy  trình  quản  lý  và  ra  quyết định dựa trên dữ

liệu.  Đối với nhà quản lý, việc giám sát hiệu suất của toàn bộ website, theo dõi

các chỉ số KPI (Key Performance Indicators) như tổng doanh thu, số lượng đơn

4

hàng,  tỷ  lệ  chuyển  đổi,  giá trị đơn hàng trung bình là nền tảng để đánh giá sức

khỏe của website và hoạch định chiến lược phát triển. Một dashboard được thiết

kế tốt sẽ tập hợp tất cả những dữ liệu quan trọng này vào một nơi duy nhất, được

trình  bày  một  cách  trực  quan  thông  qua  biểu  đồ,  đồ  thị  và  các  chỉ  số  tóm  tắt.

Điều này giúp nhà quản lý tiết kiệm thời gian tổng hợp và phân tích dữ liệu, dễ

dàng nhận ra các xu hướng, xác định các vấn đề tiềm ẩn và đưa ra các quyết định

dựa trên bằng chứng cụ thể thay vì cảm tính.

Thứ ba, hỗ trợ người bán cá nhân hóa trải nghiệm khách hàng và tăng cường

tương tác. Đối với người bán hàng trực tiếp trên website, dashboard không chỉ là

công cụ để theo dõi doanh số cá nhân mà còn là nguồn thông tin quý giá về hành

vi mua sắm của khách hàng. Thông qua việc phân tích các sản phẩm khách hàng

đã xem, các sản phẩm họ thêm vào giỏ hàng nhưng chưa mua, lịch sử mua hàng,

người bán có thể hiểu rõ hơn về sở thích và nhu cầu của từng nhóm khách hàng.

Dựa  trên  những  thông  tin  này,  họ  có  thể  thực  hiện  các  hoạt  động  cá nhân hóa

như  gợi  ý sản phẩm phù hợp, tạo các chương trình khuyến mãi nhắm mục tiêu,

và  tương  tác  với  khách  hàng  một  cách  hiệu  quả  hơn,  từ  đó  tăng  cường  sự  hài

lòng và lòng trung thành của khách hàng.

Thứ  tư,  khả  năng  phát  hiện  sớm  các  vấn  đề  và  cơ  hội  tiềm  năng.  Một

dashboard được thiết kế tốt có khả năng hiển thị dữ liệu theo thời gian thực hoặc

gần thời gian thực, cho phép người bán và quản lý theo dõi sát sao diễn biến của

các  chỉ  số  bán  hàng.  Bất  kỳ sự sụt giảm bất thường nào trong doanh số, sự gia

tăng đột biến trong tỷ lệ hủy đơn hàng, hay sự thay đổi trong hành vi của khách

hàng đều có thể được phát hiện kịp thời. Điều này cho phép doanh nghiệp nhanh

chóng ứng phó với các vấn đề phát sinh, giảm thiểu rủi ro và tận dụng các cơ hội

mới nổi. Ví dụ, nếu dashboard cho thấy một dòng sản phẩm cụ thể đang có nhu

cầu tăng cao đột ngột, người bán có thể chủ động tăng cường nguồn cung và các

hoạt động quảng bá liên quan.

5

2. Yêu cầu về chức năng

Người bán: Điều chỉnh được thời gian, khu vực áp dụng đối với các chỉ số

Admin: Điều chỉnh được thời gian, khu vực áp dụng đối với các chỉ số

3. Yêu cầu phi chức năng

-  Yêu cầu về hiệu suất:

+  Thời gian tải trang, hiện kết quả sau khi hiệu chỉnh thời gian, khu vực

của các chỉ số không quá 3 giây.

+  Hệ thống phải xử lý được tối thiểu 100 yêu cầu truy vấn đồng thời mà

không bị gián đoạn.

+  Hệ  thống  phải  cập  nhật  dữ  liệu  mỗi  ngày  ít  nhất  một  lần vì tính chất

của thị trường đồ cũ.

+  Hệ thống cần duy trì hoạt động liên tục trong các ngày trong năm, đặc

biệt là các dịp lễ để hoạt động thương mại điện tử diễn ra hiệu quả.

-

 Khả năng bảo trì và mở rộng:

+  Hệ  thống  phải  được thiết kế dễ hiệu, phải có tài liệu hướng dẫn và có

độ khó bảo trì vừa phải, dễ dàng xác định lỗi phần mềm nếu có vấn đề

+  Khi  lượng  người  bán  tăng  lên  theo  thời  gian,  dashboard  phải  có  khả

năng mở rộng theo mà không cần xây dựng một hệ thống mới.

-

 Tính thân thiện với người sử dụng:

+  Hệ thống phải có giao diện dễ nhìn, trực quan, các chỉ số được thể hiện

rõ ràng trên biểu đồ, màu chữ, cỡ chữ và đồ thị cần có sự đồng nhất và

không bị lẫn lộn với nhau.

+  Giao diện cần thay đổi phù hợp với từng kích thước màn hình, thiết bị

khác nhau như máy tính, điện thoại, máy tính bảng.

-

 Tính bảo mật:

+

 Mỗi người bán chỉ có thể truy cập dữ liệu của riêng họ

+

  Quản lý website có thể xem dữ liệu của toàn bộ các đơn hàng và cửa

hàng, nhưng không thể thay đổi hay chỉnh sửa những dữ liệu đó.

6

CHƯƠNG II. PHÂN TÍCH VÀ THIẾT KẾ CÁC CHỈ SỐ THỐNG KÊ

1. Phân tích nhu cầu sử dụng các chỉ số thống kê

Trong thị trường đồ điện tử cũ đầy tiềm năng, việc xây dựng một hệ thống

dashboard  trực  quan  và  giàu  thông  tin  đóng  vai  trò  then  chốt  trong  việc  định

hướng và tối ưu hóa hoạt động kinh doanh cho cả người bán lẫn quản trị viên. Vì

vậy  chúng  ta  cần  phân  tích  để  nắm  rõ  nhu  cầu  từng  vai  trò,  từ  đó  đưa  ra  các

thông  tin  phù  hợp,  trọng  tâm  và hữu ích nhất đối với từng vai trò, hỗ trợ trong

việc đưa ra quyết định dựa trên dữ liệu và giúp tăng hiệu suất kinh doanh.

Đối  với  người  bán,  dashboard  không  chỉ  là  nơi  hiển  thị  các  con  số khô

khan  mà  còn  là  công  cụ  đắc  lực  để  thấu  hiểu  hành vi khách hàng và nâng cao

hiệu  suất  bán hàng. Lượt truy cập cửa hàng chính là cánh cửa đầu tiên hé lộ sự

quan  tâm  của  thị  trường đối với gian hàng, từ đó giúp người bán đánh giá hiệu

quả của các chiến dịch quảng bá và điều chỉnh cách thức trưng bày sản phẩm sao

cho thu hút nhất.

Doanh  thu  và  số  đơn  hàng  là  những  cột  mốc  quan  trọng, phản ánh trực

tiếp  thành  quả  kinh  doanh,  đồng  thời giúp người bán xác định được những sản

phẩm chủ lực và thời điểm vàng để đẩy mạnh bán hàng. Đặc biệt, chỉ số giá trị

đơn hàng trung bình (AOV) mở ra cơ hội tăng trưởng doanh thu bền vững bằng

cách  khuyến  khích  khách  hàng  mua  thêm  hoặc  tập  trung  vào  các sản phẩm có

giá trị cao hơn.

Tỷ lệ chuyển đổi từ khách truy cập thành người mua hàng (CR) chính là

thước đo vàng cho thấy khả năng thuyết phục và hấp dẫn của gian hàng, đòi hỏi

người  bán  liên tục tối ưu hóa trải nghiệm mua sắm. Bên cạnh đó, trong một thị

trường nhạy cảm về chất lượng như đồ điện tử cũ, việc theo dõi sát sao tỷ lệ đổi

trả  không  chỉ  giúp  người  bán  nhận  diện  các  vấn  đề  về  sản  phẩm  mà  còn  xây

dựng lòng tin với khách hàng. Tỷ lệ bỏ giỏ hàng lại là lời cảnh báo về những rào

cản trong quy trình mua sắm, thôi thúc người bán tìm ra giải pháp để hoàn thiện

7

trải  nghiệm  người  dùng.  Cuối  cùng,  tỷ  lệ  khách  hàng  quay  lại  (PDR)  chính là

minh  chứng  cho  sự  hài  lòng  và  lòng  trung thành, tạo nên nền tảng khách hàng

vững chắc cho sự phát triển lâu dài.

Ở  cấp độ quản trị, dashboard mang đến một bức tranh toàn cảnh về hiệu

suất  của  cả  sàn  giao  dịch,  cung  cấp  những  thông  tin  chiến  lược  để  đưa  ra  các

quyết  định  quan  trọng.  Lượt  truy  cập  sàn  không  chỉ  cho  thấy  sức  hút tổng thể

của  nền  tảng  mà  còn  phản  ánh  hiệu  quả  của  các  chiến dịch marketing quy mô

lớn.  Lượng  người dùng là chỉ số quan trọng để theo dõi sự tăng trưởng và mức

độ tương tác của cộng đồng, tạo tiền đề cho sự phát triển bền vững.

Tổng doanh thu sàn và tổng số đơn hàng là những cột mốc kinh doanh vĩ

mô,  cho  thấy quy mô và tốc độ phát triển của thị trường đồ điện tử cũ trên nền

tảng. Giá trị đơn hàng trung bình (AOV) toàn sàn cung cấp cái nhìn tổng quan về

giá  trị  các  giao  dịch,  giúp  định  hướng  các  chương  trình  khuyến  mãi  và  chiến

lược giá.

Tỷ lệ chuyển đổi từ khách truy cập thành người mua hàng (CR) toàn sàn

đánh giá hiệu quả chung của nền tảng trong việc thu hút và giữ chân khách hàng.

Đặc biệt, tỷ lệ đổi trả toàn sàn là một chỉ số quan trọng về chất lượng sản phẩm

và uy tín của cả cộng đồng người bán, đòi hỏi admin phải có các chính sách và

biện pháp hỗ trợ phù hợp. Cuối cùng, tỷ lệ khách hàng quay lại (PDR) toàn sàn

chính  là  thước  đo  cho  sự  hài  lòng và lòng trung thành của người dùng với nền

tảng,  tạo  nên  nền  tảng  vững  chắc cho sự phát triển bền vững của thị trường đồ

điện tử cũ này.

2.  Dự  đoán  tổng  lượng  người  dùng,  đơn hàng và doanh số thông qua

mô hình ARIMA

2.1.  Lý do lựa chọn mô hình

Trong  bối  cảnh  thị  trường  đồ điện tử cũ đang trên đà phát triển, website

O’Tech đối mặt với một thách thức không nhỏ: làm thế nào để đưa ra các quyết

8

định kinh doanh chiến lược một cách chủ động và hiệu quả? Việc thiếu khả năng

dự đoán chính xác các chỉ số kinh doanh cốt lõi như tổng lượng người dùng, số

lượng  đơn  hàng  và  tổng  doanh  số  trong  tương  lai gần và xa, khiến sàn rơi vào

thế bị động. Điều này dẫn đến nhiều hệ lụy tiềm ẩn: khó khăn trong việc lên kế

hoạch marketing và các chương trình khuyến mãi phù hợp để thu hút người dùng

mới và thúc đẩy giao dịch, bất cập trong việc quản lý tài nguyên và cơ sở hạ tầng

để đáp ứng nhu cầu tăng trưởng hoặc suy giảm đột ngột, hạn chế khả năng đặt ra

các  mục  tiêu  tăng trưởng thực tế và xây dựng các chiến lược phát triển dài hạn

một cách tự tin và có cơ sở. Sự thiếu hụt một công cụ dự báo đáng tin cậy sẽ trở

thành một rào cản lớn cho sự phát triển bền vững và khả năng cạnh tranh của sàn

trong một thị trường ngày càng khốc liệt.

Để  giải  quyết  bài  toán  cấp  thiết  về  việc  dự  đoán  các  chỉ  số  kinh  doanh

quan  trọng,  mô  hình  ARIMA  (Autoregressive  Integrated  Moving  Average) nổi

lên  như  một  giải  pháp  mạnh  mẽ  và  phù  hợp. Với khả năng đặc biệt trong việc

phân tích và dự đoán các chuỗi thời gian, ARIMA có thể tận dụng lịch sử dữ liệu

về lượng người dùng, số lượng đơn hàng và doanh số đã thu thập được để nhận

diện  các  xu  hướng  tăng  trưởng  hoặc  suy  giảm,  các  yếu  tố  mùa  vụ  có  thể  ảnh

hưởng  đến  hoạt  động  kinh  doanh,  cũng  như  các  mối  tương  quan  tự động giữa

các giá trị theo thời gian. Bằng cách xây dựng các mô hình ARIMA phù hợp cho

từng  chỉ  số,  sàn  có  thể  tạo  ra  các  dự  báo  có  độ  chính  xác  cao về lượng người

dùng  mới,  số  lượng  đơn  hàng  dự kiến và tổng doanh số tiềm năng trong tương

lai. Thông tin dự đoán này sẽ trở thành nền tảng vững chắc để sàn chủ động lên

kế hoạch marketing, tối ưu hóa quản lý tài nguyên, đưa ra các quyết định chiến

lược  về  mở rộng và xây dựng các mục tiêu tăng trưởng thực tế, từ đó nâng cao

khả năng cạnh tranh và đảm bảo sự phát triển bền vững trong thị trường đồ điện

tử cũ đầy biến động.

2.2. Cơ sở lý thuyết

Mô  hình  ARIMA  (AutoRegressive  Integrated  Moving  Average)  là  một

công  cụ  thống  kê  mạnh  mẽ  và  phổ biến trong lĩnh vực dự báo chuỗi thời gian.

9

Điểm đặc biệt của ARIMA là khả năng mô hình hóa các chuỗi thời gian có tính

dừng  hoặc  có  thể  được  chuyển  đổi  thành  chuỗi dừng thông qua phép sai phân.

Mô  hình  này  kết  hợp  ba  thành  phần chính để nắm bắt các đặc điểm khác nhau

của  dữ  liệu  chuỗi  thời  gian, bao gồm: Tự hồi quy (AR), Sai phân (I), và Trung

bình trượt (MA).

2.2.1. AR (AutoRegressive - Tự hồi quy)

Thành phần tự hồi quy (AR) xem xét mối quan hệ giữa giá trị hiện tại của

chuỗi thời gian và các giá trị quá khứ của chính nó. Ý tưởng cốt lõi là giá trị tại

một  thời  điểm nhất định chịu ảnh hưởng bởi một số lượng nhất định các giá trị

trước  đó.  Mô  hình  AR  bậc  p,  ký  hiệu  là  AR(p),  được  biểu  diễn  bằng  phương

trình sau:

Trong đó:

 − 2  + ⋯ + ϕp  − p  + ϵt
 − 1  + ϕ2
  = c + ϕ1
𝑦
𝑦
𝑦
𝑡
𝑡
𝑡

𝑦
𝑡

●

 : Giá trị của chuỗi thời gian tại thời điểm t.
𝑦
𝑡

●  c: Hằng số (intercept) của mô hình.

●  ϕi  (i=1,2,…,p): Các hệ số hồi quy, đo lường mức độ ảnh hưởng của giá trị

quá khứ thứ i đến giá trị hiện tại.

●

−i  (i=1,2,…,p): Các giá trị quá khứ của chuỗi thời gian tại các thời điểm
𝑦
𝑡

t−1,t−2,…,t−p.

●  ϵt :  Thành  phần  nhiễu  trắng  (white  noise)  tại  thời  điểm t, giả định là các

biến ngẫu nhiên độc lập và có phân phối đồng nhất với kỳ vọng bằng 0 và

phương sai không đổi (ϵt ∼WN(0,σ2)).

Bậc  p  của  mô  hình  AR  xác  định  số  lượng  các  giá  trị  quá  khứ  được  sử

dụng để dự đoán giá trị hiện tại. Việc lựa chọn bậc p phù hợp là rất quan trọng để

nắm bắt đúng cấu trúc tự tương quan của chuỗi thời gian.

2.2.2. I (Integrated - Sai phân)

10

Thành  phần  sai  phân  (Integrated)  được  sử  dụng  khi  chuỗi  thời gian ban

đầu không dừng. Một chuỗi thời gian dừng là chuỗi có các đặc tính thống kê cơ

bản  (như trung bình và phương sai) không thay đổi theo thời gian. Nhiều chuỗi

thời  gian  kinh  tế  và  tài  chính  không  dừng  ở  dạng  ban đầu, thường thể hiện xu

hướng hoặc tính mùa vụ.

Để  làm  cho  chuỗi  thời  gian  trở  nên  dừng,  chúng  ta  thực  hiện  phép  sai

phân. Sai phân bậc nhất được tính bằng cách lấy hiệu giữa giá trị hiện tại và giá

trị ở thời điểm trước đó:

Δ   =
𝑦
𝑡

  −
𝑦
𝑡

𝑦

𝑡−2

Nếu chuỗi sau khi sai phân bậc nhất vẫn chưa dừng, chúng ta có thể tiếp

tục lấy sai phân bậc hai:

2
= Δ  −
𝑦
𝑦
Δ
𝑡
𝑡

Δ𝑦

  = (

 −
𝑦
𝑡

𝑦

 ) − ( − 1  −
𝑦
𝑡

𝑦

𝑡−1

 )  =

 − 2  − 1 +
𝑦
𝑦
𝑡
𝑡

𝑦

𝑡−2

𝑡−1

𝑡−2

Tổng  quát, nếu cần d lần lấy sai phân để chuỗi thời gian trở thành dừng,

ta  ký  hiệu  quá  trình  này  là  I(d).  Chuỗi  thời  gian  sau  khi  lấy  sai  phân  d  lần  sẽ

được mô hình hóa bằng các thành phần AR và MA.

2.2.3. MA (Moving Average - Trung bình trượt)

Thành phần trung bình trượt (MA) mô hình hóa mối quan hệ giữa giá trị

hiện tại của chuỗi thời gian và các sai số (nhiễu trắng) của các giá trị trong quá

khứ.  Thay  vì  dựa  trên  các  giá  trị  quá  khứ  của  chính  chuỗi  thời  gian,  MA  tập

trung  vào  các  "shock"  ngẫu  nhiên  đã  xảy  ra.  Mô  hình  MA  bậc  q,  ký  hiệu  là

MA(q), được biểu diễn bằng phương trình sau:

  = c + ϵt  + θ1 ϵt − 1  + θ2 ϵt − 2  + ⋯ + θq ϵt − q
𝑦
𝑡

Trong đó:

●

: Giá trị của chuỗi thời gian tại thời điểm t.
𝑦
𝑡

11

●  c: Hằng số (intercept) của mô hình.

●  ϵt : Thành phần nhiễu trắng tại thời điểm t.

●  θi   (i=1,2,…,q):  Các  hệ  số  trung bình trượt, đo lường mức độ ảnh hưởng

của sai số quá khứ thứ i đến giá trị hiện tại.

●  ϵt−i  (i=1,2,…,q): Các sai số trắng tại các thời điểm t−1,t−2,…,t−q.

Bậc  q  của  mô  hình  MA  xác  định  số  lượng  các  sai  số  quá  khứ  được  sử

dụng để mô hình hóa giá trị hiện tại. Thành phần MA giúp mô hình nắm bắt các

hiệu ứng ngắn hạn hoặc các "cú sốc" bất ngờ trong chuỗi thời gian.

2.3. Phương trình ARIMA

Mô hình ARIMA kết hợp cả ba thành phần tự hồi quy (AR), sai phân (I),

và  trung  bình  trượt  (MA)  để  mô hình hóa một chuỗi thời gian dừng sau khi đã

được sai phân d lần (nếu cần). Mô hình ARIMA được ký hiệu là ARIMA(p,d,q),

trong đó:

●  p:  Bậc  của  phần  tự  hồi  quy  (AR),  cho  biết  có bao nhiêu giá trị quá khứ

của chuỗi đã sai phân được sử dụng trong mô hình.

●  d: Số lần sai phân cần thiết để làm cho chuỗi thời gian trở nên dừng.

●  q:  Bậc của phần trung bình trượt (MA), cho biết có bao nhiêu sai số quá

khứ được sử dụng trong mô hình.

Phương trình tổng quát của mô hình ARIMA(p,d,q) có thể được viết dưới

dạng  toán  học phức tạp hơn khi kết hợp các toán tử trễ (lag operator) L, nhưng

về cơ bản, nó thể hiện mối quan hệ tuyến tính giữa giá trị hiện tại của chuỗi đã

sai  phân,  các  giá trị quá khứ của nó, và các sai số ngẫu nhiên ở hiện tại và quá

khứ.

Việc xác định đúng các bậc p, d, và q là bước quan trọng nhất trong việc

xây  dựng  mô  hình  ARIMA  phù  hợp.  Các  phương  pháp  như  phân  tích  hàm  tự

tương  quan  (ACF)  và  hàm  tự  tương  quan  từng  phần  (PACF)  thường  được  sử

dụng để ước lượng các bậc này. Sau khi xác định được các bậc, các hệ số của mô

12

hình  (ϕi  và θi ) sẽ được ước lượng bằng các phương pháp thống kê như phương

pháp  bình  phương  tối thiểu (least squares) hoặc phương pháp khả năng cực đại

(maximum likelihood).

2.3.1. Giả định mô hình

Để  mô  hình  ARIMA  hoạt động hiệu quả và cho ra các dự báo đáng tin cậy, dữ

liệu chuỗi thời gian cần thỏa mãn một số giả định quan trọng:

-  Tính  dừng  (Stationarity):  Đây  là  giả  định  cốt  lõi  của  mô  hình  ARIMA.

Một  chuỗi  thời  gian  được  gọi  là  dừng  nếu  các đặc tính thống kê của nó

không thay đổi theo thời gian. Cụ thể:

+  Trung  bình  không  đổi:  Giá  trị  trung  bình  của  chuỗi  phải  ổn  định

qua các thời điểm khác nhau.

+  Phương sai không đổi: Độ phân tán của dữ liệu xung quanh giá trị

trung bình phải ổn định.

+  Tự hiệp phương sai (Autocovariance) không đổi theo thời gian trễ:

Hiệp  phương  sai  giữa  các  giá  trị  tại  hai  thời  điểm  khác  nhau  chỉ

phụ  thuộc  vào  khoảng  thời  gian  trễ  giữa  chúng,  chứ  không  phụ

thuộc vào thời điểm cụ thể.

Nếu chuỗi thời gian không dừng, việc áp dụng trực tiếp mô hình ARIMA có thể

dẫn đến các dự báo sai lệch. Do đó, bước sai phân (thành phần 'I' trong ARIMA)

được sử dụng để chuyển đổi chuỗi không dừng thành chuỗi dừng.

-  Quan hệ tuyến tính: Mô hình ARIMA giả định rằng mối quan hệ giữa giá

trị hiện tại của chuỗi và các giá trị quá khứ, cũng như các sai số quá khứ,

là  tuyến  tính.  Điều này có nghĩa là sự thay đổi ở các biến quá khứ sẽ có

tác  động  tỷ  lệ  thuận  đến  giá  trị  hiện  tại.  Nếu  mối  quan  hệ  là  phi  tuyến

tính, các mô hình khác phức tạp hơn có thể phù hợp hơn.

13

2.3.2. Quy trình xây dựng mô hình

-

  Khám  phá  dữ  liệu:  Trực  quan  hóa  chuỗi  thời  gian  để  phát  hiện  xu

hướng, mùa vụ hoặc các mẫu bất thường.

-  Kiểm  tra  tính  dừng:  Sử  dụng  các  kiểm  định  thống  kê  như  ADF  Test

(Augmented  Dickey-Fuller)  hoặc  KPSS  Test để kiểm tra chuỗi thời gian

có dừng hay không.

-  Làm dừng chuỗi: Nếu chuỗi không dừng, lấy sai phân d lần để đạt được

tính dừng.

-  Xác  định  tham  số  pp  và  qq:  Sử  dụng  biểu  đồ  ACF  (Autocorrelation

Function) và PACF (Partial Autocorrelation Function) để chọn giá trị phù

hợp cho p và q.

-  Huấn luyện mô hình: Xây dựng mô hình ARIMA dựa trên các tham số

p, d, q.

-  Đánh  giá  mô  hình:  Sử  dụng  các  chỉ  số  đánh  giá  như  AIC  (Akaike

Information Criterion), BIC (Bayesian Information Criterion), hoặc MSE

(Mean Squared Error).

-  Dự báo: Sử dụng mô hình để dự báo giá trị tương lai.

14

 CHƯƠNG III. THIẾT KẾ VÀ TỔ CHỨC HỆ THỐNG ETL

1. Mục tiêu của hệ thống ETL dữ liệu

Hệ thống ETL được thiết kế theo định hướng modular – tách biệt rõ ràng

các tầng chức năng, đảm bảo dễ bảo trì, kiểm thử và mở rộng. Mỗi bước trong

pipeline đều được kiểm soát chặt chẽ bởi các nguyên tắc về chất lượng dữ liệu

(Data Quality), khả năng tái chạy (idempotency) và tính mở (extensibility). Mục

tiêu tổng thể bao gồm:

-  Trích xuất (Extract) và Kiểm soát chất lượng dữ liệu (Data Quality): Thu

thập dữ liệu thô một cách nhất quán từ các nguồn cơ sở dữ liệu giao dịch

chính. Đồng thời tự động xác thực và sàng lọc dữ liệu đầu vào, đảm bảo

tính toàn vẹn, định dạng chuẩn và tuân thủ logic kinh doanh.

-  Biến đổi (Transform): Chuyển hóa dữ liệu thô thành các chỉ số kinh

doanh (KPIs) có giá trị, chẳng hạn như doanh thu, số lượng đơn hàng, giá

trị đơn hàng trung bình (AOV). Đồng thời, thực hiện các phân tích

chuyên sâu đặc thù cho ngành hàng công nghệ cũ (ví dụ: tính toán khấu

hao, phân tích theo thương hiệu và tình trạng sản phẩm).

-  Tải (Load) và Phân phối (Distribute): Nạp dữ liệu đã qua xử lý vào Kho

dữ liệu (Data Warehouse) để phục vụ cho mục đích phân tích lâu dài và

đồng thời phân phối các KPI quan trọng qua hệ thống streaming (Kafka)

để cung cấp thông tin gần thời gian thực.

-  Trực quan hóa (Visualize): Đảm bảo dữ liệu KPI được hiển thị tức thì trên

các dashboard của website, phục vụ cho việc ra quyết định nhanh chóng.

2. Quy trình xử lý dữ liệu

Kiến trúc tổng thể của hệ thống được triển khai theo dạng ETL Pipeline

nhiều giai đoạn, với các khối xử lý được tách biệt rõ ràng theo từng chức năng

cụ thể. Mỗi giai đoạn được thiết kế để hoạt động độc lập, có khả năng fail-safe

và log chi tiết, phục vụ cho cả mục đích vận hành lẫn audit sau này.

15

2.1. Extract

Khởi động và lập lịch khởi chạy:

Pipeline  được  điều  phối  bởi  cơ  chế  lập  lịch  nội  bộ,  sử  dụng  Spring

Scheduler  của  Spring  Boot.  Mỗi  pipeline  chính  có  thể  được  cấu  hình  để  chạy

định kỳ hoặc kích hoạt thủ công qua REST API. Cơ chế này cho phép hệ thống

có thể tự động khởi chạy hệ thống ETL theo lịch định kỳ, bao gồm các loại chính

sau:

-  1:00 AM hàng ngày: Chạy batch job toàn diện cho dữ liệu của ngày hôm

trước (Day -1). Đây là luồng chính, xử lý khối lượng dữ liệu lớn và thực

hiện các tính toán phức tạp.

-  Hàng giờ: Chạy các job nhỏ hơn để cập nhật các chỉ số quan trọng, cung

cấp  dữ  liệu  "gần  thời  gian  thực"  (near  real-time)  cho  các hoạt động cần

phản ứng nhanh.

-  Mỗi 5 phút: Chạy một tác vụ kiểm tra để giám sát trạng thái của pipeline,

đảm bảo hệ thống luôn sẵn sàng.

Trích xuất dữ liệu (Extract):

Giai  đoạn  này  tập  trung  vào  việc  lấy  dữ  liệu  thô  từ  hệ  thống  nguồn

(OLTP).  DataExtractorService  được  thiết  kế  theo  nguyên  tắc  trách  nhiệm  đơn

(Single  Responsibility  Principle),  chỉ  chịu  trách  nhiệm  kết  nối và trích xuất dữ

liệu.  Pipeline  kết  nối  trực  tiếp  đến  các  bảng  giao  dịch  như  orders,  users,

products,  v.v.  Toàn  bộ  logic  truy  vấn  được  viết  theo  hướng  tối  ưu  hóa

performance.  Đầu  ra  là  đối  tượng  ExtractedData  chứa  dữ  liệu  thô  kèm  theo

metadata ban đầu gồm:

-  Thời điểm trích xuất

-  Số lượng bản ghi

-  Source name

-  Định danh tracking

16

Việc đóng gói logic trích xuất vào một service riêng giúp trừu tượng hóa

nguồn dữ liệu. Nếu trong tương lai, nguồn dữ liệu thay đổi hoặc mở rộng theo

nhu cầu của admin, chúng ta chỉ cần cập nhật service này mà không ảnh hưởng

đến phần còn lại của pipeline.

2.2. Transform

Kiểm soát chất lượng dữ liệu (Data Quality Gate):

Đây là bước tối quan trọng để ngăn chặn hiện tượng "rác vào, rác ra"

(Garbage In, Garbage Out). Dữ liệu không đáng tin cậy sẽ dẫn đến những phân

tích sai lệch và quyết định kinh doanh thiếu cơ sở. Vì vậy chúng em thực hiện

bước này để kiểm soát chất lượng dữ liệu cho hệ thống ETL

-  Tự động rà soát dữ liệu dựa trên một bộ quy tắc (ruleset) được định nghĩa

trước: kiểm tra giá trị NULL ở các trường quan trọng, xác thực định dạng

(ngày tháng, email), kiểm tra tính hợp lệ của logic kinh doanh (vd: ngày

giao hàng không thể trước ngày đặt hàng), và phát hiện các giá trị ngoại

lai (outliers).

-  Phát ra cảnh báo: Hệ thống sẽ tính toán một "điểm chất lượng" (quality

score). Nếu điểm này dưới một ngưỡng cho phép, một cảnh báo sẽ được

gửi đến đội ngũ kỹ thuật kèm theo log chi tiết về các lỗi phát hiện được

trong khi hệ thống pipeline vẫn tiếp tục hoạt động, giúp nhanh chóng xác

định và khắc phục sự cố trong khi vẫn đảm bảo tính liên tục của dòng dữ

liệu.

Biến đổi dữ liệu (Transform):

Đây là nơi dữ liệu thô được "chuyển đổi" thành thông tin hữu ích. Giai

đoạn này được chia thành hai service riêng biệt để đảm bảo tính module và dễ

bảo trì:

17

-  DataTransformerService: Chịu trách nhiệm thực hiện các phép biến đổi

và tính toán KPI chung cho mọi mô hình kinh doanh:

-  Tổng hợp (aggregate) dữ liệu để tính toán doanh thu, số đơn hàng.

-  Nối (join) các bảng để làm giàu dữ liệu cho mục đích phân tích

người dùng

-  TechMarketplaceTransformerService: Chứa các logic biến đổi đặc thù

cho ngành hàng công nghệ cũ. Việc tách riêng logic này giúp hệ thống dễ

dàng mở rộng sang các ngành hàng khác trong tương lai mà không làm

phức tạp hóa core logic:

-  Nhận diện các nhóm khách hàng trung thành theo chu kỳ nâng cấp

(upgrade cycle).

-  Phân loại thương hiệu (Apple, Dell, Sony...) và tình trạng sản

phẩm (Like new, used,...).

-  Toàn bộ dữ liệu sau xử lý được chuẩn hóa thành các cấu trúc

TransformedData, chứa đầy đủ chỉ số, timestamp, định danh seller hoặc

buyer (nếu có), và các phân đoạn thời gian (day/week/month) sẵn sàng

đưa vào kho dữ liệu.

 2.3. Load

Lưu trữ dữ liệu (Load):

Giai đoạn cuối cùng của chu trình ETL, nơi dữ liệu được ghi vào hệ thống đích.

-  Đích: Bảng Fact_monthly_sales, fact_customer_behavior,

fact_tech_buyer_behavior trong kho dữ liệu . Đây là một bảng Fact được

thiết kế theo mô hình dimensional modeling, tối ưu cho các truy vấn phân

tích.

-  Phương thức: Sử dụng cơ chế UPSERT (UPDATE nếu đã tồn tại,

INSERT nếu chưa). Điều này đảm bảo tính toàn vẹn dữ liệu và cho phép

pipeline có thể chạy lại nhiều lần mà không tạo ra các bản ghi trùng lặp

(idempotency).

18

-  Kiểm soát xung đột: Áp dụng Optimistic Locking (Khóa lạc quan). Mỗi

bản ghi sẽ có một trường phiên bản (version). Khi cập nhật, hệ thống sẽ

kiểm tra xem phiên bản có khớp không. Nếu không, điều đó có nghĩa là

một tiến trình khác đã cập nhật bản ghi, giao dịch hiện tại sẽ bị hủy và thử

lại. Cơ chế này đảm bảo tính nhất quán dữ liệu trong môi trường có nhiều

tiến trình ghi đồng thời mà không làm giảm hiệu năng như Pessimistic

Locking.

2.4. Phân phối, giám sát dữ liệu và tối ưu truy vấn

Phân phối qua Kafka (Real - Time Streaming):

Để phục vụ nhu cầu real-time, thay vì chỉ ghi vào DWH, hệ thống còn

đẩy các thông tin quan trọng vào một message broker.

-  Mô hình: Sử dụng mô hình Producer-Consumer của Kafka. Pipeline ETL

đóng vai trò là Producer, gửi các "sự kiện" (events) vào các topic khác

nhau (kpi-updates, system-metrics, alerts).

-  Ý nghĩa: Kiến trúc này giúp tách rời (decouple) hệ thống ETL khỏi các hệ

thống tiêu thụ dữ liệu. Các Consumer (như dashboard, hệ thống giám sát,

hệ thống kiểm toán) có thể đăng ký vào các topic tương ứng để nhận dữ

liệu một cách độc lập và gần như ngay lập tức mà không tạo thêm tải cho

hệ thống ETL chính.

Dashboard Cache:

Để đảm bảo trải nghiệm người dùng cuối (các nhà phân tích, quản lý) là

tốt nhất, việc truy vấn trực tiếp vào kho dữ liệu cho mỗi lần tải dashboard là

không tối ưu.

-  Cơ chế: DashboardCacheService lắng nghe các sự kiện từ Kafka. Khi có

một KPI mới được cập nhật, service này sẽ tính toán trước các dữ liệu

19

tổng hợp thường dùng và lưu vào một bộ đệm (cache) tốc độ cao (như

Redis).

-  Lợi ích: Giúp dashboard tải lên gần như tức thì, giảm đáng kể độ trễ và

giảm tải cho kho dữ liệu chính.

Điều phối dữ liệu(Orchestration):

ETLOrchestrator là "bộ não" của cả hệ thống, chịu trách nhiệm điều phối tuần tự

và xử lý lỗi của các bước trên:

1.  Gọi DataExtractorService.

2.  Chuyển output cho QualityCheckService.

3.  Nếu chất lượng đạt, gọi các TransformerService.

4.  Cuối cùng, gọi LoadService để ghi dữ liệu và kích hoạt Kafka

producer.

Ghi lại kết quả của mỗi lần chạy vào một bảng ETLResult, bao gồm thời

gian bắt đầu/kết thúc, trạng thái (thành công/thất bại), điểm chất lượng, và thông

điệp lỗi (nếu có). Dữ liệu log này là vô giá cho việc giám sát, gỡ lỗi và đánh giá

hiệu suất của pipeline.

20

CHƯƠNG IV. PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG

1. Danh sách các tác nhân và mô tả

- Danh sách các tác nhân

+  Người  mua  (Customer):  Khách  hàng  truy  cập  vào  Website  để  tìm

kiếm, đặt mua sản phẩm và đặt mua.

+  Người  bán  (Seller):  Người  bán  là  tùy chọn mở khóa tài khoản người

bán của người mua để bán mặt hàng của mình trên sàn, người bán trả lời

phản hồi của khách hàng và xem thống kê doanh thu.

+  Quản  lý  (Admin):  Kiểm  soát  trang  Web, đảm bảo bảo mật đồng thời

ngăn chặn các hành vi vi phạm chính sách của người mua và người bán.

- Danh sách ca sử dụng:

U1: Đăng nhập: Người dùng đăng nhập vào Website

U2: Đăng xuất: Người dùng đăng xuất khỏi Website

U3: Đăng ký: Người dùng đăng ký tài khoản

U4: Gửi thông báo: Admin gửi thông báo đến người dùng

U5: Xem hiệu suất bán hàng Shop: Người bán xem hiệu suất bán hàng hiển

thị  trên  Dashboard:  Doanh  thu,  Số  đơn  hàng,  giá  trị  đơn  hàng trung bình

(AOV), Tỷ lệ số đơn hàng bị đổi/trả.

U6:  Quản  lý  sản  phẩm  Shop:  Người  bán  quán  lý  các  sản phẩm đang bày

bán trong shop của mình

U7:  Quản  lý  đơn  hàng  Shop:  Người  bán  quản  lý  trạng  thái các đơn hàng

trong shop của mình.

U8: Xem dự báo xu hướng Shop: Người bán xem biểu đồ dự báo xu hướng

các chỉ tiêu: Số người dùng, Số đơn hàng, Doanh thu (của Shop)

U9: Xem hiệu suất người dùng Shop: Người bán xem hiệu suất người dùng

dịch vụ của shop hiển thị trên Dashboard: Lượt truy cập Shop, Tỷ lệ khách

21

hàng quay lại (PDR) Shop, Tỷ lệ chuyển đổi từ khách truy cập thành người

mua hàng (CR).

U10: Xuất dữ liệu Shop: Người bán  xuất dữ liệu theo nhu cầu

U11:  Xem  Hiệu  suất  hoạt  động  Website:  Admin xem hiệu suất hoạt động

của Website trên Dashboard: Tổng giá trị giao dịch, Giá trị đơn hàng trung

bình (AOV), Tổng doanh thu nền tảng (PV).

U12: Xem Hiệu suất người dùng Website: Admin xem hiệu suất hoạt động

của Website trên Dashboard: Lượt truy cập Website, Số lượng người dùng

mới  (Tháng/Quý/Năm),  Tỷ  lệ  chuyển  đổi  từ  người  truy  cập  thành  người

mua hàng (CR), Tỷ lệ khách hàng quay lại (PDR).

U13: Xem dự báo xu hướng Website: Admin xem biểu đồ dự báo xu hướng

chỉ tiêu: Số người dùng, Số đơn hàng, Doanh thu

U14:  Quản  lý  sản  phẩm  Website: Admin Xem danh mục sản phẩm, Quản

lý đơn hàng, Kiểm duyệt sản phẩm.

2. Biểu đồ UseCase tổng quát của hệ thống

22

Hình 1. Biểu đồ Use Case Tổng quát

3. Biểu đồ Use Case Chi tiết của hệ thống

Hình 2: Biểu đồ Use Case Chi tiết

Hình 3. Phân rã ca sử dụng Xem hiệu suất bán hàng Shop

23

Hình 4. Phân rã ca sử dụng Quản lý sản phẩm shop

Hình 5. Phân rã ca sử dụng Quản lý đơn hàng Shop

24

Hình 6. Phân rã ca sử dụng Xem dự báo xu hướng Shop

Hình 7. Phân rã ca sử dụng Xem Hiệu suất người dùng Shop

Hình 8. Phân rã ca sử dụng Xem Hiệu suất hoạt động Website

25

Hình 9. Phân rã ca sử dụng Xem Hiệu suất người dùng Website

Hình 10. Phân rã ca sử dụng Xem dự báo xu hướng Website

Hình 11. Phân rã ca sử dụng Quản lý sản phẩm Website

26

4. Mô tả ca sử dụng

1. Đăng nhập và quản lý tài khoản người dùng (U1, U2, U3):

Người dùng có thể đăng ký tài khoản trên hệ thống để bắt đầu sử dụng các

dịch  vụ  của  Website.  Sau  khi  đăng  ký  thành  công,  họ  có  thể  đăng  nhập  bằng

thông tin tài khoản để truy cập các chức năng phù hợp với vai trò của mình như

mua  hàng,  quản  lý  shop  hay  quản  trị  Website.  Khi  không  còn  sử  dụng,  người

dùng có thể thực hiện thao tác đăng xuất để đảm bảo an toàn thông tin.

2. Quản lý và phân tích hiệu suất bán hàng của Shop (U5, U6, U7, U8,

U9, U10):

Người  bán  sau  khi  đăng  nhập  có  thể  quản  lý  toàn  bộ  hoạt  động  kinh

doanh của shop mình trên nền tảng. Họ có thể cập nhật, chỉnh sửa danh mục sản

phẩm,  theo  dõi  và  xử  lý  đơn  hàng  theo từng trạng thái. Thông qua Dashboard,

người bán có thể xem báo cáo hiệu suất bán hàng (doanh thu, số đơn, AOV, tỷ lệ

đổi/trả),  phân  tích  hành  vi  người  dùng,  theo  dõi  tỷ  lệ  chuyển  đổi  (CR),  tỷ  lệ

khách hàng quay lại (PDR), và xuất dữ liệu để phục vụ cho công tác quản lý nội

bộ hoặc báo cáo.

3. Quản trị và vận hành hệ thống Website dành cho Admin (U4, U11,

U12, U13, U14):

Admin  có  quyền quản lý toàn bộ hoạt động trên hệ thống. Họ có thể gửi

thông  báo  đến  người dùng, giám sát hiệu suất vận hành Website qua các chỉ số

như  tổng  giá  trị  giao  dịch,  doanh  thu  nền  tảng  (PV),  lượt  truy  cập,  số  lượng

người dùng mới, tỷ lệ chuyển đổi và PDR. Ngoài ra, Admin còn có thể xem các

biểu đồ dự báo xu hướng phát triển nền tảng và quản lý danh mục sản phẩm toàn

hệ thống, bao gồm cả việc kiểm duyệt sản phẩm và xử lý đơn hàng trên Website.

5. Đặc tả ca sử dụng chi tiết

5.1. Đăng nhập

27

Tên Use Case

Đăng nhập

Tác nhân chính

Người mua, Người bán, Admin

Điều kiện trước

Người  dùng  truy  cập  vào  Website  và  đã  có  tài  khoản

đăng nhập

Đảm bảo tối thiểu

Hệ thống yêu cầu người dùng đăng nhập lại

Điều kiện sau

Người dùng đăng nhập thành công

Kích hoạt

Nhấn nút “Đăng nhập”

Chuỗi sự kiện chính:

1. Trên trang chủ Người dùng nhấn nút “Đăng nhập”

2. Màn hình hiển thị giao diện đăng nhập

3. Người dùng tùy chọn đăng nhập bằng tài khoản Google, Facebook hoặc đăng

nhập bằng tài khoản và mật khẩu.

4.  Nếu  đăng  nhập  bằng  tài  khoản  và  mật  khẩu,  hệ  thống kiểm tra lại thông tin

đăng nhập

5. Hệ thống hiển thị giao diện trang chủ

28

Ngoại lệ:

4.1. Hệ thống thông báo thông tin đăng nhập không chính xác

 4.1.1. Người dùng thực hiện lại

Bảng 1. Đặc tả ca sử dụng Đăng nhập

5.2. Đăng xuất

Tên Use Case

Đăng xuất

Tác nhân chính

Người mua, Người bán, Admin

Điều kiện trước

Người dùng truy cập vào Website

Đảm bảo tối thiểu

Điều kiện sau

Người dùng đăng xuất thành công

Kích hoạt

Nhấn nút “Đăng xuất”

29

Chuỗi sự kiện chính:

1. Người dùng nhấn vào biểu tượng người dùng trên trang chủ

2. Giao diện hiển thị tùy chọn cho người dùng

3. Người dùng nhấn nút “Đăng xuất”

4. Hệ thống hiển thị cửa sổ xác thực người dùng muốn đăng xuất

5. Người dùng nhấn “Đồng ý”

6. Màn hình hiển thị giao diện Trang chủ chưa đăng nhập

Ngoại lệ:

5.3. Đăng ký

Bảng 2. Đặc tả ca sử dụng Đăng xuất

Tên Use Case

Đăng ký

Tác nhân chính

Người mua, Người bán

Điều kiện trước

Người mua, Người bán chưa có tài khoản

Đảm bảo tối thiểu

Hệ thống yêu cầu người dùng đăng ký lại

Điều kiện sau

Người mua, Người bán đăng ký tài khoản thành công

Kích hoạt

Nhấn nút “Đăng ký”

30

Chuỗi sự kiện chính:

1. Người dùng nhấn nút “Đăng ký” hoặc Đăng ký bằng Google/Facebook

2. Hệ thống hiển thị giao diện đăng ký tài khoản

3. Người dùng điền thông tin đăng ký theo yêu cầu

4. Hệ thống kiểm tra thông tin hợp lệ

5.  Màn  hình  hiển  thị  thông  báo  đăng  ký  thành  công  và  chuyển  về  giao  diện

Trang chủ

Ngoại lệ:

4.1. Hệ thống thông báo thông tin đăng ký không hợp lệ

 4.1.1. Người dùng thực hiện đăng ký lại

Bảng 3. Đặc tả ca sử dụng Đăng ký

5.4. Gửi thông báo

Tên Use Case

Gửi thông báo

Tác nhân chính

Admin

Điều kiện trước

Đảm bảo tối thiểu

Hệ thống yêu cầu Admin đăng ký lại

Điều kiện sau

31

Kích hoạt

Nhấn nút “Gửi thông báo”

Chuỗi sự kiện chính:

1. Admin nhấn nút “Gửi thông báo” trên trang chủ

2. Admin chọn người muốn gửi thông báo rồi gửi cho người đó

3, Hệ thống thông báo “Gửi thông báo” thành công

Ngoại lệ:

Bảng 4. Đặc tả ca sử dụng Gửi thông báo

5.5. Xem hiệu suất bán hàng Shop

Tên Use Case

Xem hiệu suất bán hàng Shop

Tác nhân chính

Người bán

Điều kiện trước

Người bán truy cập vào Website và đã có tài khoản đăng

nhập

Đảm bảo tối thiểu

Hệ thống yêu cầu người bán đăng nhập lại

Điều kiện sau

Người bán đăng nhập thành công

Kích hoạt

Nhấn nút “Xem”

32

Chuỗi sự kiện chính:

1. Trên trang chủ Người bán nhấn nút “Biểu tượng người dùng”

2. Hệ thống hiển thị “Thanh chức năng người dùng”

3. Người bán chọn “Thống kê”

4. Hệ thống hiển thị Bảng thống kê

5. Người bán chọn “Hiệu suất bán hàng”

6.  Hệ  thống  hiển  thị:  Doanh  thu,  Số  đơn  hàng,  giá  trị  đơn  hàng  trung  bình

(AOV), Tỷ lệ số đơn hàng bị đổi/trả.

Ngoại lệ:

Bảng 5. Đặc tả ca sử dụng Xem hiệu suất bán hàng Shop

5.6. Quản lý sản phẩm Shop

Tên Use Case

Quản lý sản phẩm Shop

Tác nhân chính

Người bán

Điều kiện trước

Người bán chưa có tài khoản

Đảm bảo tối thiểu

Hệ thống yêu cầu người bán đăng ký lại

Điều kiện sau

Người bán đăng ký tài khoản thành công

Kích hoạt

Nhấn nút “Thêm/Sửa/Xóa sản phẩm”

33

Chuỗi sự kiện chính:

1. Trên trang chủ Người bán nhấn nút “Biểu tượng người dùng”

2. Hệ thống hiển thị “Thanh chức năng người dùng”

3. Người bán chọn “Quản lý sản phẩm”

4. Hệ thống hiển thị danh mục sản phẩm

5.  Người  bán  “Thêm”,  “Sửa”,  “Xóa”  sản  phẩm  trong  danh  mục  sản  phẩm  của

mình.

Ngoại lệ:

5.1. Hệ thống thông báo thông tin không hợp lệ

 5.1.1. Người dùng thực hiện lại

Bảng 6. Đặc tả ca sử dụng Quản lý sản phẩm Shop

5.7. Quản lý đơn hàng Shop

Tên Use Case

Quản lý đơn hàng Shop

Tác nhân chính

Người bán

Điều kiện trước

Người bán chưa có tài khoản

Đảm bảo tối thiểu

Hệ thống yêu cầu người bán đăng ký lại

Điều kiện sau

Người bán đăng ký tài khoản thành công

34

Kích hoạt

Thực hiện Xem và cập nhật đơn hàng

Chuỗi sự kiện chính:

1. Trên trang chủ Người bán nhấn nút “Biểu tượng người dùng”

2. Hệ thống hiển thị “Thanh chức năng người dùng”

3. Người bán chọn “Đơn bán”

4. Hệ thống hiển thị Đơn bán hàng

5. Người bán “Xem đơn hàng” hoặc “Sửa trạng thái đơn hàng”

6. Hệ thống lưu thay đổi vào cơ sở dữ liệu

Ngoại lệ:

6.1. Hệ thống thông báo thông tin không hợp lệ

6.1.1. Người bán thực hiện lại

Bảng 7. Đặc tả ca sử dụng Quản lý đơn hàng Shop

5.8. Xem dự báo xu hướng Shop

Tên Use Case

Xem dự báo xu hướng Shop

Tác nhân chính

Người bán

Điều kiện trước

Người bán chưa có tài khoản

Đảm bảo tối thiểu

Hệ thống yêu cầu người bán đăng ký lại

35

Điều kiện sau

Người bán đăng ký tài khoản thành công

Kích hoạt

Xem các biểu đồ

Chuỗi sự kiện chính:

1. Trên trang chủ Người bán nhấn nút “Biểu tượng người dùng”

2. Hệ thống hiển thị “Thanh chức năng người dùng”

3. Người bán chọn “Thống kê”

4. Hệ thống hiển thị Bảng thống kê

5. Người bán chọn “Xem dự báo”

6. Hệ thống hiển thị: Số người dùng, Số đơn hàng, Doanh thu được dự báo trong

3 tháng tới

Ngoại lệ:

Bảng 8. Đặc tả ca sử dụng Xem dự báo xu hướng của Shop

5.9. Xem Hiệu suất người dùng Shop

Tên Use Case

Xem Hiệu suất người dùng Shop

Tác nhân chính

Người bán

Điều kiện trước

Người bán chưa có tài khoản

36

Đảm bảo tối thiểu

Hệ thống yêu cầu người bán đăng ký lại

Điều kiện sau

Người bán đăng ký tài khoản thành công

Kích hoạt

Xem các biểu đồ

Chuỗi sự kiện chính:

1. Trên trang chủ Người bán nhấn nút “Biểu tượng người dùng”

2. Hệ thống hiển thị “Thanh chức năng người dùng”

3. Người bán chọn “Thống kê”

4. Hệ thống hiển thị Bảng thống kê

5. Người bán chọn “Xem Hiệu suất người dùng”

6. Hệ thống hiển thị: Số người dùng, Số đơn hàng, Doanh thu được dự báo trong

3 tháng tới

Ngoại lệ:

Bảng 9. Đặc tả ca sử dụng Xem Hiệu suất người dùng Shop

5.10. Xuất dữ liệu

Tên Use Case

Xuất dữ liệu

Tác nhân chính

Người bán

37

Điều kiện trước

Người bán chưa có tài khoản

Đảm bảo tối thiểu

Hệ thống yêu cầu người bán đăng ký lại

Điều kiện sau

Người bán đăng ký tài khoản thành công

Kích hoạt

Chọn dữ liệu và nhấn “Xuất file”

Chuỗi sự kiện chính:

1. Trên trang chủ Người bán nhấn nút “Biểu tượng người dùng”

2. Hệ thống hiển thị “Thanh chức năng người dùng”

3. Người bán chọn “Thống kê”

4. Hệ thống hiển thị Bảng thống kê

5. Người bán chọn dữ liệu muốn xuất rồi chọn “Xuất file”

Ngoại lệ:

Bảng 10. Đặc tả ca sử dụng Xuất dữ liệu

5.11. Xem hiệu suất hoạt động Website

Tên Use Case

Xem Hiệu suất hoạt động Website

Tác nhân chính

Admin

38

Điều kiện trước

Đảm bảo tối thiểu

Hệ thống yêu cầu Admin đăng ký lại

Điều kiện sau

Admin đăng ký tài khoản thành công

Kích hoạt

Chọn mục muốn xem

Chuỗi sự kiện chính:

1. Trên trang chủ Admin nhấn nút “Thống kê”

2. Hệ thống hiển thị Bảng thống kê

3. Admin chọn “Hiệu suất hoạt động”

4.  Hệ  thống  hiển  thị  Dashboard:  Tổng  giá  trị  giao dịch, Giá trị đơn hàng trung

bình (AOV), Tổng doanh thu nền tảng (PV).

Ngoại lệ:

Bảng 11. Đặc tả ca sử dụng Xem Hiệu suất hoạt động Website

5.12. Xem Hiệu suất người dùng Website

Tên Use Case

Xem Hiệu suất người dùng

Tác nhân chính

Admin

Điều kiện trước

39

Đảm bảo tối thiểu

Hệ thống yêu cầu Admin đăng ký lại

Điều kiện sau

Admin đăng ký tài khoản thành công

Kích hoạt

Chọn mục muốn xem

Chuỗi sự kiện chính:

1. Trên trang chủ Admin nhấn nút “Thống kê”

2. Hệ thống hiển thị Bảng thống kê

3. Admin chọn “Hiệu suất người dùng”

4.  Hệ  thống  hiển  thị  Dashboard:  Lượt  truy  cập  Website,  Số  lượng  người  dùng

mới  (Tháng/Quý/Năm),  Tỷ  lệ  chuyển  đổi  từ  người  truy  cập  thành  người  mua

hàng (CR), Tỷ lệ khách hàng quay lại (PDR).

Ngoại lệ:

Bảng 12. Đặc tả ca sử dụng Xem Hiệu suất người dùng Website

5.13. Xem dự báo xu hướng Website

Tên Use Case

Xem dự báo xu hướng Website

Tác nhân chính

Admin

Điều kiện trước

40

Đảm bảo tối thiểu

Hệ thống yêu cầu Admin đăng ký lại

Điều kiện sau

Admin đăng ký tài khoản thành công

Kích hoạt

Chọn mục muốn xem

Chuỗi sự kiện chính:

1. Trên trang chủ Admin nhấn nút “Thống kê”

2. Hệ thống hiển thị Bảng thống kê

3. Admin chọn “Dự báo”

4. Hệ thống hiển thị Dashboard dự báo xu hướng: Số người dùng, Số đơn hàng,

Doanh thu

Ngoại lệ:

Bảng 13. Đặc tả ca sử dụng Xem dự báo xu hướng Website

5.14. Quản lý sản phẩm Website

Tên Use Case

Quản lý sản phẩm Website

Tác nhân chính

Admin

Điều kiện trước

Đảm bảo tối thiểu

Hệ thống yêu cầu Admin đăng ký lại

41

Điều kiện sau

Admin đăng ký tài khoản thành công

Kích hoạt

Chọn mục muốn xem

Chuỗi sự kiện chính:

1. Trên trang chủ Admin nhấn nút “Quản lý sản phẩm”

2.  Admin  “Xem sản phẩm”, “Xem đơn hàng”, “Kiểm duyệt sản phẩm” = Đồng

ý/Từ chối

Ngoại lệ:

Bảng 14. Đặc tả ca sử dụng Quản lý sản phẩm Website

42

6. Thiết kế mô hình hoạt động

6.1. Biểu đồ hoạt động

Hình 1. Biểu đồ hoạt động ca sử dụng Đăng nhập

43

Hình 2. Biểu đồ hoạt động ca sử dụng Đăng xuất

Hình 3. Biểu đồ hoạt động ca sử dụng Đăng ký

44

Hình 4. Biểu đồ hoạt động ca sử dụng  Gửi thông báo

Hình 5. Biểu đồ hoạt động ca sử dụng Xem Hiệu suất bán hàng Shop

45

Hình 6. Biểu đồ hoạt động ca sử dụng Quản lý sản phẩm Shop

46

Hình 7 Biểu đồ hoạt động ca sử dụng Quản lý đơn hàng Shop

47

Hình 8. Biểu đồ ca sử dụng Xem dự báo xu hướng Shop

48

Hình 9. Biểu đồ hoạt động ca sử dụng Xem Hiệu suất người dùng Shop

49

Hình 10. Biểu đồ hoạt động ca sử dụng Xuất dữ liệu

50

Hình 11. Biểu đồ hoạt động ca sử dụng Xem Hiệu suất hoạt động Website

51

Hình 12. Biểu đồ hoạt động ca sử dụng Xem Hiệu suất người dùng Website

52

Hình 13. Biểu đồ hoạt động ca sử dụng Xem dự báo xu hướng Website

53

Hình 14. Biểu đồ hoạt động ca sử dụng Quản lý sản phẩm Website

54

6.2. Biểu đồ tuần tự

Hình 1. Biểu đồ tuần tự ca sử dụng Đăng nhập

Hình 2. Biểu đồ tuần tự ca sử dụng Đăng xuất

Hình 3. Biểu đồ tuần tự ca sử dụng Đăng ký

55

Hình 4. Biểu đồ tuần tự ca sử dụng Gửi thông báo

Hình 5. Biểu đồ tuần tự ca sử dụng Xem Hiệu suất bán hàng Shop

Hình 6. Biểu đồ tuần tự ca sử dụng Quản lý sản phẩm Shop

56

Hình 7. Biểu đồ tuần tự ca sử dụng Quản lý đơn hàng Shop

Hình 8. Biểu đồ tuần tự ca sử dụng Xem dự báo xu hướng Shop

Hình 9. Biểu đồ tuần tự ca sử dụng Xem hiệu suất người dùng Shop

57

Hình 10. Biểu đồ tuần tự ca sử dụng Xuất dữ liệu
Shop

Hình 11. Biểu đồ tuần tự ca sử dụng Xem Hiệu suất hoạt động Website

Hình 12. Biểu đồ tuần tự ca sử dụng Xem Hiệu suất người dùng Website

Hình 13. Biểu đồ tuần tự ca sử dụng Xem Dự báo xu hướng Website

58

Hình 14. Biểu đồ tuần tự ca sử dụng Quản lý sản phẩm Website

7. Bảng thực thể

7.1. Bảng Users

STT

THUỘC
TÍNH

DATA TYPE

MÔ TẢ

RÀNG BUỘC

1

2

3

4

5

6

7

8

9

user_id

INT UNSIGNED  ID của người dùng

email

VARCHAR(255)

Địa chỉ email của
người dùng

PK,
AUTO_INCREMENT

UNIQUE, NOT NULL

password

VARCHAR(255)  Mật khẩu

NOT NULL

phone_number  VARCHAR(20)

Số điện thoại của
người dùng

UNIQUE NULL

first_name  VARCHAR(100)  Tên của người dùng

NULL

last_name

VARCHAR(100)  Họ của người dùng

NULL

dob

DATE

Ngày sinh của người
dùng

NULL

avatar_url  VARCHAR(2048)  URL hình đại diện

NULL

role

ENUM

10

is_active

BOOLEAN

Vai trò của người dùng

NOT NULL, DEFAULT
'Customer'

Trạng thái hoạt động
của người dùng

NOT NULL, DEFAULT
TRUE

59

11

created_at

TIMESTAMP  Thời gian tạo tài khoản

12

updated_at

TIMESTAMP

Thời gian cập nhật tài
khoản

DEFAULT
CURRENT_TIMESTA
MP

DEFAULT
CURRENT_TIMESTA
MP ON UPDATE
CURRENT_TIMESTA
MP

13

last_login

TIMESTAMP

Thời gian đăng nhập
cuối cùng

NULL

7.2. Bảng  account_addresses

STT  THUỘC TÍNH

DATA TYPE

MÔ TẢ

RÀNG BUỘC

1

2

3

4

5

6

7

8

9

address_id

user_id

INT
UNSIGNED

INT
UNSIGNED

ID của địa chỉ

PK, AUTO_INCREMENT

ID người dùng

FK → users(user_id), NOT
NULL

city

VARCHAR(100)  Thành phố

NOT NULL

district

VARCHAR(100)  Quận/Huyện

NOT NULL

ward

street

VARCHAR(100)  Phường/Xã

NOT NULL

VARCHAR(255)  Đường

NOT NULL

address_type

ENUM

Loại địa chỉ
(Home, Company,
Warehouse)

NOT NULL, DEFAULT
'Home'

is_default

BOOLEAN

Địa chỉ mặc định

NOT NULL, DEFAULT
FALSE

created_at

TIMESTAMP

Thời gian tạo địa
chỉ

DEFAULT
CURRENT_TIMESTAMP

10

updated_at

TIMESTAMP

Thời gian cập nhật
địa chỉ

DEFAULT
CURRENT_TIMESTAMP
ON UPDATE
CURRENT_TIMESTAMP

60

7.3. Bảng verification_details

STT  THUỘC TÍNH

DATA TYPE

MÔ TẢ

RÀNG BUỘC

1

2

3

4

5

6

7

8

9

verify_id

INT UNSIGNED

ID xác minh

user_id

INT UNSIGNED

ID người dùng

is_verified

BOOLEAN

Trạng thái xác minh

PK,
AUTO_INCREMENT

FK → users(user_id),
UNIQUE, NOT
NULL

NOT NULL,
DEFAULT FALSE

national_id

VARCHAR(20)

Số ID quốc gia duy
nhất

UNIQUE NULL

front_image_url  VARCHAR(2048)  URL ảnh mặt trước

NULL

back_image_url  VARCHAR(2048)  URL ảnh mặt sau

NULL

verified_at

TIMESTAMP

Thời gian xác minh

NULL

created_at

TIMESTAMP

Thời gian tạo chi tiết
xác minh

DEFAULT
CURRENT_TIMEST
AMP

updated_at

TIMESTAMP

Thời gian xác nhận

7.4. Bảng sellers

STT

THUỘC TÍNH

DATA TYPE

MÔ TẢ

RÀNG BUỘC

1

2

user_id

INT
UNSIGNED

ID người bán

is_approved

BOOLEAN

Trạng thái phê duyệt
của người bán

3

is_selling_active

BOOLEAN

Trạng thái kinh doanh
của người bán

PK, FK →
users(user_id)

NOT NULL,
DEFAULT
FALSE

NOT NULL,
DEFAULT
FALSE

61

4

5

6

1

2

3

4

5

6

momo_account  VARCHAR(15)

Chi tiết tài khoản
MoMo của người bán

NULL

approved_at

TIMESTAMP  Thời gian phê duyệt

NULL

created_at

TIMESTAMP

Thời gian tạo tài khoản
người bán

7

updated_at

TIMESTAMP

Thời gian cập nhật tài
khoản người bán

DEFAULT
CURRENT_TIM
ESTAMP

DEFAULT
CURRENT_TIM
ESTAMP ON
UPDATE
CURRENT_TIM
ESTAMP

7.5. Bảng categories

STT  THUỘC TÍNH

DATA TYPE

MÔ TẢ

RÀNG BUỘC

category_id

INT UNSIGNED

ID danh mục

PK,
AUTO_INCREMENT

name

VARCHAR(100)  Tên danh mục

NOT NULL

description

MEDIUMTEXT

avatar_url

VARCHAR(2048)

Mô tả chi tiết danh
mục

URL hình đại diện
danh mục

NULL

NULL

parent_category
_id

INT UNSIGNED

ID danh mục cha

created_at

TIMESTAMP

Thời gian tạo danh
mục

7

updated_at

TIMESTAMP

Thời gian cập nhật
danh mục

FK →
categories(category_id
), NULL

DEFAULT
CURRENT_TIMEST
AMP

DEFAULT
CURRENT_TIMEST
AMP ON UPDATE
CURRENT_TIMEST
AMP

62

7.6. Bảng products

STT  THUỘC TÍNH

DATA TYPE

MÔ TẢ

RÀNG BUỘC

1

product_id

INT UNSIGNED

ID sản phẩm

2

seller_user_id

INT UNSIGNED

ID người bán

PK,
AUTO_INCREME
NT

FK →
sellers(user_id),
NOT NULL

FK →
categories(categor
y_id), NOT NULL

3

4

5

6

7

8

9

category_id

INT UNSIGNED

ID danh mục sản
phẩm

name

VARCHAR(255)  Tên sản phẩm

NOT NULL

description

MEDIUMTEXT  Mô tả sản phẩm

NULL

price

DECIMAL(12, 2)  Giá sản phẩm

NOT NULL

status

ENUM

Trạng thái sản
phẩm (Pending,
Available, ...)

NOT NULL,
DEFAULT
'Pending'

is_approved

BOOLEAN

Trạng thái phê
duyệt sản phẩm

NOT NULL,
DEFAULT FALSE

approved_at

TIMESTAMP

Thời gian phê duyệt
sản phẩm

NULL

10

created_at

TIMESTAMP

Thời gian tạo sản
phẩm

DEFAULT
CURRENT_TIME
STAMP

11

listed_at

TIMESTAMP

Thời gian niêm yết
sản phẩm

NULL

12

updated_at

TIMESTAMP

Thời gian cập nhật
sản phẩm

DEFAULT
CURRENT_TIME
STAMP ON
UPDATE
CURRENT_TIME
STAMP

63

7.7. Bảng product_images

STT  THUỘC TÍNH

DATA TYPE

MÔ TẢ

RÀNG BUỘC

1

2

3

4

5

image_id

INT UNSIGNED

ID hình ảnh

product_id

INT UNSIGNED

ID sản phẩm

PK,
AUTO_INCREMENT

FK →
products(product_id),
NOT NULL

image_url

VARCHAR(2048)  URL hình ảnh  NOT NULL

is_thumbnail

BOOLEAN

Trạng thái hình
ảnh đại diện

NOT NULL,
DEFAULT FALSE

created_at

TIMESTAMP

Thời gian tạo
hình ảnh

DEFAULT
CURRENT_TIMESTA
MP

7.8. Bảng shopping_carts

STT  THUỘC TÍNH

DATA TYPE

MÔ TẢ

RÀNG BUỘC

1

2

cart_id

INT UNSIGNED

ID giỏ hàng

user_id

INT UNSIGNED

ID người dùng

3

created_at

TIMESTAMP

4

updated_at

TIMESTAMP

Thời gian tạo
giỏ hàng

Thời gian cập
nhật giỏ hàng

PK,
AUTO_INCREMENT

FK → users(user_id),
UNIQUE, NOT
NULL

DEFAULT
CURRENT_TIMEST
AMP

DEFAULT
CURRENT_TIMEST
AMP ON UPDATE
CURRENT_TIMEST
AMP

64

7.9. Bảng cart_items

STT  THUỘC TÍNH

DATA TYPE

MÔ TẢ

RÀNG BUỘC

1

cart_item_id

INT
UNSIGNED

ID mục trong giỏ

2

3

4

cart_id

INT
UNSIGNED

ID giỏ hàng

product_id

INT
UNSIGNED

ID sản phẩm

added_at

TIMESTAMP

Thời gian thêm
vào giỏ

PK,
AUTO_INCREM
ENT

FK →
shopping_carts(car
t_id), NOT NULL

FK →
products(product_i
d), NOT NULL

DEFAULT
CURRENT_TIME
STAMP

7.10. Bảng orders

STT  THUỘC TÍNH

DATA TYPE

MÔ TẢ

RÀNG BUỘC

1

2

3

4

order_id

INT

Mã đơn hàng

PK,
AUTO_INCREM
ENT

user_id

INT

Người dùng (khách
hàng) tạo đơn hàng

FK →
users(user_id)

shipping_address
_id

INT

Địa chỉ giao hàng

order_time

TIMESTAMP

Thời gian đặt hàng

FK →
account_addresses
(address_id)

DEFAULT
CURRENT_TIME
STAMP

5

payment_method

ENUM

Phương thức thanh
toán (Momo, COD)

NOT NULL

65

6

7

8

9

total_amount

DECIMAL(12, 2)

Tổng số tiền của
đơn hàng

status

ENUM

Trạng thái đơn hàng

NOT NULL

NOT NULL,
DEFAULT
'Pending'

notes

MEDIUMTEXT

Ghi chú của khách
hàng

NULL

created_at

TIMESTAMP

Thời gian tạo đơn
hàng

10

updated_at

TIMESTAMP

Thời gian cập nhật
đơn hàng

DEFAULT
CURRENT_TIME
STAMP

DEFAULT
CURRENT_TIME
STAMP ON
UPDATE
CURRENT_TIME
STAMP

7.11. Bảng order_details

STT

THUỘC TÍNH

DATA TYPE

MÔ TẢ

RÀNG BUỘC

1

order_detail_id

INT

Mã chi tiết đơn hàng

2

3

order_id

INT

Đơn hàng tương ứng

product_id

INT

Sản phẩm trong đơn
hàng

PK,
AUTO_INCRE
MENT

FK →
orders(order_id)

FK →
products(product
_id)

4

price_at_purchase  DECIMAL(12, 2)

Giá sản phẩm khi
đặt hàng

NOT NULL

66

7.12. Bảng reviews

STT  THUỘC TÍNH

DATA TYPE

MÔ TẢ

1

2

review_id

INT

Mã đánh giá

order_id

INT

Đơn hàng tương ứng với
đánh giá

3

reviewer_user_id

INT

Người đánh giá (khách
hàng)

4

seller_user_id

INT

Người bán được đánh giá

RÀNG
BUỘC

PK,
AUTO_INC
REMENT

FK →
orders(order_
id)

FK →
users(user_id
)

FK →
sellers(user_i
d)

NOT NULL,
CHECK
(rating
BETWEEN 1
AND 5)

5

6

7

8

9

rating

INT

Đánh giá của khách hàng
(từ 1 đến 5)

comment

MEDIUMTEXT

Bình luận của khách
hàng về sản phẩm

NULL

review_time

TIMESTAMP  Thời gian đánh giá

DEFAULT
CURRENT_
TIMESTAM
P

seller_response  MEDIUMTEXT  Phản hồi của người bán  NULL

response_time

TIMESTAMP

Thời gian phản hồi của
người bán

NULL

67

4

5

6

7.13. Bảng complaints

STT

THUỘC TÍNH

DATA TYPE  MÔ TẢ

RÀNG BUỘC

1

2

complaint_id

INT

Mã khiếu nại

PK,
AUTO_INCREM
ENT

complainant_user
_id

INT

Người khiếu nại
(khách hàng)

FK →
users(user_id)

3

reported_user_id

INT

Người bị khiếu nại
(người bán hoặc
người dùng khác)

FK →
users(user_id)

order_id

INT

Đơn hàng liên quan
đến khiếu nại

FK →
orders(order_id),
NULL nếu không
có liên quan

reason

MEDIUMTEXT  Lý do khiếu nại

NOT NULL

status

ENUM

7

resolution_notes  MEDIUMTEXT

Trạng thái khiếu nại
(Pending,
Reviewing,
Resolved...)

NOT NULL,
DEFAULT
'Pending'

Ghi chú giải quyết
khiếu nại

NULL

8

created_at

TIMESTAMP

Thời gian tạo khiếu
nại

9

updated_at

TIMESTAMP

Thời gian cập nhật
khiếu nại

DEFAULT
CURRENT_TIM
ESTAMP

DEFAULT
CURRENT_TIM
ESTAMP ON
UPDATE
CURRENT_TIM
ESTAMP

68

7.14. Bảng refunds

STT

THUỘC
TÍNH

DATA TYPE

MÔ TẢ

RÀNG BUỘC

1

2

3

4

5

refund_id

INT

Mã hoàn tiền

PK,
AUTO_INCREMENT

order_id

user_id

INT

INT

Đơn hàng tương ứng
với yêu cầu hoàn tiền

FK → orders(order_id)

Người yêu cầu hoàn tiền  FK → users(user_id)

reason

MEDIUMTEXT  Lý do yêu cầu hoàn tiền  NOT NULL

status

ENUM

Trạng thái yêu cầu hoàn
tiền

NOT NULL,
DEFAULT 'Pending'

6

admin_notes  MEDIUMTEXT

Ghi chú của admin về
yêu cầu hoàn tiền

NULL

7

requested_at

TIMESTAMP

Thời gian yêu cầu hoàn
tiền

8

updated_at

TIMESTAMP

Thời gian cập nhật yêu
cầu hoàn tiền

DEFAULT
CURRENT_TIMEST
AMP

DEFAULT
CURRENT_TIMEST
AMP ON UPDATE
CURRENT_TIMEST
AMP

7.15. Bảng Notifications

STT  THUỘC TÍNH

DATA TYPE

MÔ TẢ

RÀNG BUỘC

1

2

3

notification_id

BIGINT

Mã thông báo

PK,
AUTO_INCREMENT

recipient_user_id

INT

Người nhận thông
báo

FK → users(user_id)

sender_info

VARCHAR(100)  Thông tin người

NOT NULL,

69

gửi

DEFAULT 'System'

type

title

ENUM

Loại thông báo

NOT NULL

VARCHAR(255)

Tiêu đề của thông
báo

NULL

content

MEDIUMTEXT

Nội dung thông
báo

NOT NULL

link_url

VARCHAR(2048)

URL liên kết nếu
có

NULL

is_read

BOOLEAN

Trạng thái đã đọc
hay chưa

NOT NULL,
DEFAULT FALSE

read_at

TIMESTAMP

Thời gian đọc
thông báo

NULL

4

5

6

7

8

9

10

created_at

TIMESTAMP

Thời gian tạo thông
báo

DEFAULT
CURRENT_TIMEST
AMP

70

8. Biểu đồ lớp

8.1. Biểu đồ lớp

8.2. Thuộc tính và quan hệ giữa các lớp

Định
nghĩa

Lớp User là lớp cơ sở trừu tượng, chứa thông
tin và hành vi chung cho tất cả người dùng
trong hệ thống (Customer, Seller, Admin).

-  user_id: Định danh duy nhất của người

dùng.

-  email: Email đăng nhập, duy nhất.
-  phone_number: Số điện thoại, duy nhất

Thuộc
tính

nếu có.
first_name: Tên.
-
last_name: Họ.
-
-  dob: Ngày sinh.
-  avatar_url: URL ảnh đại diện.
-

role: Vai trò của người dùng trong hệ
thống.
refund_momo_account: Tài khoản
Momo (10 số) để nhận hoàn tiền.
is_active: Trạng thái kích hoạt (do
Admin quản lý).

-

-

-  created_at: Thời điểm tạo tài khoản.
-  updated_at: Thời điểm cập nhật gần nhất.
last_login: Thời điểm đăng nhập gần
-

71

nhất.

-
-

register(details): Đăng ký xác thực
login(email, password): Đăng nhập vào
hệ thống.
logout(): Đăng xuất khỏi hệ thống.

-
-  updateProfile(details): Cập nhật thông tin

Phương
thức

cá nhân.

-  changePassword(oldPass, newPass):

-

-

Thay đổi mật khẩu.
requestVerification(details): Gửi yêu cầu
xác minh tài khoản.
fileComplaint(reportedUser, order,
reason): Tạo khiếu nại mới.

-  viewNotifications(): Xem danh sách

thông báo.

-  markNotificationRead(notificationId):

Đánh dấu thông báo đã đọc.

Định
nghĩa

Kế thừa từ lớp User, đại diện cho khách hàng
thực hiện các hoạt động mua sắm.

Phương
thức

-

searchProducts(query, filters): Tìm kiếm
sản phẩm.

-  viewProductDetails(productId): Xem chi

tiết sản phẩm.

-  addToCart(product): Thêm sản phẩm vào

-

giỏ hàng.
removeFromCart(cartItemId): Xóa sản
phẩm khỏi giỏ hàng.

-  viewCart(): Xem giỏ hàng.
-  placeOrder(addressId, paymentMethod):

Đặt hàng.

-  viewOrderStatus(orderId): Xem trạng

thái đơn hàng.

-  viewOrderHistory(): Xem lịch sử mua

hàng.

-  confirmOrderReceived(orderId): Xác

-

nhận đã nhận hàng.
requestReturn(orderId, reason): Yêu cầu
trả hàng/hoàn tiền.

-  cancelOrder(orderId): Hủy đơn hàng.
reviewSeller(sellerUserId, orderId,
-
rating, comment): Đánh giá người bán.
requestBecomeSeller(): Gửi yêu cầu trở

-

72

thành người bán.

-  chatWithAI(query): Tương tác với AI hỗ

trợ.

Định
nghĩa

Kế thừa từ lớp User, đại diện cho người dùng có
chức năng bán hàng.

Thuộc
tính

Phương
thức

-

-

is_approved: Trạng thái phê duyệt bán
hàng bởi Admin.
is_selling_active: Trạng thái người dùng
tự bật/tắt chức năng bán hàng.

-  momo_account: Tài khoản Momo của

người bán để nhận thanh toán.

-  approved_at: Thời điểm được Admin

phê duyệt.

-  addProduct(details): Thêm sản phẩm.
-  updateProduct(productId, details): Cập

nhật thông tin sản phẩm.

-  deleteProduct(productId): Xóa sản phẩm.
-  viewListedProducts(): Xem danh sách

-

sản phẩm đang bán.
respondToReview(reviewId, response):
Phản hồi đánh giá của khách hàng.
-  viewSalesHistory(): Xem lịch sử bán

hàng.

-  updateOrderStatus(orderId, status): Cập

nhật trạng thái đơn hàng.

-  viewRevenueStats(): Xem thống kê

doanh thu.

-  confirmOrderShipped(orderId): Xác

nhận đã gửi hàng.

-  processRefund(refundId): Xử lý yêu cầu

-

hoàn tiền.
toggleSellingActive(isActive): Bật/tắt
chức năng bán hàng.

Định
nghĩa

Kế thừa từ lớp User, đại diện cho quản trị viên
với các quyền quản lý hệ thống cơ bản.

Phương
thức

-  verifyUser(verifyId): Xác minh tài khoản

người dùng.

-  verifySeller(sellerUserId): Duyệt yêu cầu

trở thành người bán.

-  verifyProduct(productId): Duyệt sản

73

phẩm đăng bán.

-  changeUserStatus(userId): Khóa/Mở

-

-

khoá tài khoản người dùng.
reviewComplaint(complaintId,
resolution): Xem xét và xử lý khiếu nại.
sendNotification(userId, message): Gửi
thông báo đến người dùng.

-  viewWebsiteStatistics(): Xem thống kê

-

hoạt động website.
reviewReturnRequest(refundId,
approve): Duyệt yêu cầu hoàn tiền.

Định
nghĩa

Kế thừa từ lớp Admin, có thêm các quyền quản
lý cao cấp nhất

Phương
thức

-  createAdminUser(details): Tạo tài khoản

Admin mới.

-  deleteAdminUser(adminUserId): Xóa tài

-

khoản Admin.
setUserRole(userId, role): Thay đổi vai
trò của người dùng.

-  manageSystemSettings(): Quản lý các

cài đặt hệ thống.

Định
nghĩa

Lưu trữ thông tin địa chỉ liên kết với một người
dùng. Một người dùng có thể có nhiều địa chỉ.

Thuộc
tính

-  address_id: Định danh duy nhất của địa

chỉ.

-  city: Tỉnh/Thành phố.
-  district: Quận/Huyện.
-  ward: Phường/Xã.
-
street: Số nhà, tên đường.
-  address_type: Loại địa chỉ.
-

is_default: Địa chỉ mặc định hay không.

Phương
thức

-  getFullAddress(): Trả về chuỗi địa chỉ

đầy đủ.

74

Định
nghĩa

Đại diện cho một thông báo được gửi đến người
dùng (từ hệ thống hoặc Admin).

Thuộc
tính

-  notification_id: Định danh duy nhất của

-

thông báo.
sender_info: Thông tin người gửi
('System' hoặc tên Admin).
type: Loại thông báo.
-
-
title: Tiêu đề thông báo.
-  content: Nội dung thông báo.
link_url: URL liên kết (nếu có).
-
is_read: Trạng thái đã đọc hay chưa.
-
read_at: Thời điểm đọc thông báo.
-
-  created_at: Thời điểm tạo thông báo.

Phương
thức

-  markAsRead(): Đánh dấu thông báo là

đã đọc.

Định
nghĩa

Lưu trữ thông tin và trạng thái xác minh tài
khoản của người dùng.

Thuộc
tính

-  verify_id: Định danh duy nhất của bản

-

ghi xác minh.
is_verified: Trạng thái đã xác minh hay
chưa.

-  national_id: Số CCCD/CMND.
-

front_image_url: URL ảnh mặt trước
CCCD/CMND.

-  back_image_url: URL ảnh mặt sau

CCCD/CMND.

-  verified_at: Thời điểm được xác minh.

Phương
thức

-  updateStatus(isAdmin, status): Cập nhật

trạng thái xác minh.

Định
nghĩa

Đại diện cho danh mục sản phẩm. Có thể có cấu
trúc cha-con.

Thuộc
tính

-  category_id: Định danh duy nhất của

danh mục.

-  name: Tên danh mục.
-  description: Mô tả danh mục.
-  avatar_url: URL ảnh đại diện cho danh

75

mục.

-  parentCategory: Danh mục cha (nếu có).

Phương
thức

-  getSubcategories(): Lấy danh sách các

danh mục con.

-  getProducts(): Lấy danh sách sản phẩm

thuộc danh mục này.

Định
nghĩa

Đại diện cho một sản phẩm được đăng bán bởi
người bán.

-  product_id: Định danh duy nhất của sản

phẩm.

-  name: Tên sản phẩm.
-  description: Mô tả chi tiết sản phẩm.
-  price: Giá bán.
-
-

status: Trạng thái của sản phẩm.
is_approved: Trạng thái phê duyệt bởi
Admin.

-  created_at: Thời điểm đăng sản phẩm.
-  updated_at: Thời điểm cập nhật sản

-

phẩm
listed_at: Thời điểm sản phẩm được đưa
lên bán chính thức.

-  getDetails(): Lấy thông tin chi tiết sản

phẩm.

-  getImages(): Lấy danh sách hình ảnh của

sản phẩm.

-  updateStatus(status): Cập nhật trạng thái

-

sản phẩm.
setApproved(isAdmin, status): Đặt trạng
thái phê duyệt (do Admin).

Thuộc
tính

Phương
thức

Định
nghĩa

Lưu trữ thông tin về một hình ảnh của sản
phẩm. Một sản phẩm có thể có nhiều hình ảnh.
Có quan hệ hợp thành với Product.

Thuộc
tính

-

-
-

image_id: Định danh duy nhất của hình
ảnh.
image_url: URL của hình ảnh.
is_thumbnail: Là ảnh đại diện
(thumbnail) hay không.

76

Định
nghĩa

Đại diện cho giỏ hàng của một khách hàng. Mỗi
khách hàng có một giỏ hàng.

Thuộc
tính

-  cart_id: Định danh duy nhất của giỏ

hàng.

Phương
thức

-  addItem(product): Thêm sản phẩm vào

-

giỏ.
removeItem(cartItemId): Xóa sản phẩm
khỏi giỏ.

-  getItems(): Lấy danh sách các sản phẩm

trong giỏ.

-  getTotalPrice(): Tính tổng số tiền của các

sản phẩm trong giỏ.

-  clearCart(): Xóa tất cả sản phẩm khỏi

giỏ.

Định
nghĩa

Đại diện cho một sản phẩm cụ thể nằm trong
giỏ hàng. Có quan hệ hợp thành với
ShoppingCart.

Thuộc
tính

-  cart_item_id: Định danh duy nhất của

mục trong giỏ.

-  product: Tham chiếu đến sản phẩm được

thêm vào.

Định
nghĩa

Đại diện cho một đơn hàng được đặt bởi khách
hàng.

Thuộc
tính

Phương
thức

-  order_id: Định danh duy nhất của đơn

hàng.

-  order_time: Thời điểm đặt hàng.
-  payment_method: Phương thức thanh

-

toán.
total_amount: Tổng giá trị các sản phẩm
trong đơn hàng.
-
status: Trạng thái hiện tại của đơn hàng.
-  notes: Ghi chú của khách hàng cho đơn

hàng.

-  getOrderDetails(): Lấy danh sách chi tiết

các sản phẩm trong đơn hàng.

-  calculateTotal(): Tính tổng giá trị đơn

hàng.

-  updateStatus(status): Cập nhật trạng thái

đơn hàng.

77

-  getShippingAddress(): Lấy thông tin địa

chỉ giao hàng.

-  getCustomer(): Lấy thông tin khách hàng

đặt đơn.

Định
nghĩa

Đại diện cho chi tiết một sản phẩm trong một
đơn hàng. Có quan hệ hợp thành với Order.

Thuộc
tính

-  order_detail_id: Định danh duy nhất của

dòng chi tiết.

-  product: Tham chiếu đến sản phẩm được

mua.

-  price_at_purchase: Giá của sản phẩm tại

thời điểm đặt hàng.

Định
nghĩa

Đại diện cho một đánh giá của khách hàng về
người bán.

Thuộc
tính

-

review_id: Định danh duy nhất của đánh
giá.
-
rating: Điểm đánh giá (từ 1 đến 5 sao).
-  comment: Nội dung bình luận đánh giá.
review_time: Thời điểm đánh giá.
-
seller_response: Phản hồi của người bán
-
đối với đánh giá.
response_time: Thời điểm người bán
phản hồi.

-

Phương
thức

-  addResponse(seller, response): Thêm

phản hồi từ người bán.

Định
nghĩa

Đại diện cho một khiếu nại do người dùng gửi
về một người dùng khác hoặc một đơn hàng.

-  complaint_id: Định danh duy nhất của

-
-
-

khiếu nại.
reason: Lý do khiếu nại.
status: Trạng thái xử lý khiếu nại.
resolution_notes: Ghi chú về kết quả xử
lý của Admin.

-  created_at: Thời điểm tạo khiếu nại.

-  updateStatus(admin, status, notes): Cập

Thuộc
tính

Phương
thức

78

nhật trạng thái và ghi chú xử lý (do
Admin).

Định
nghĩa

Đại diện cho một yêu cầu hoàn tiền liên quan
đến một đơn hàng.

Thuộc
tính

-

-
-

refund_id: Định danh duy nhất của yêu
cầu hoàn tiền.
reason: Lý do yêu cầu hoàn tiền.
status: Trạng thái xử lý yêu cầu hoàn
tiền.

-  admin_notes: Ghi chú của Admin về việc

-

xử lý.
requested_at: Thời điểm yêu cầu hoàn
tiền.

Phương
thức

-  updateStatus(admin, status, notes): Cập
nhật trạng thái và ghi chú xử lý (do
Admin).

79

CHƯƠNG V. CÁC BẢNG THỐNG KÊ

1. Người bán

1.1. Hiệu suất bán hàng

1.1.1. Doanh thu

Tổng  giá  trị  của  tất  cả  các  đơn  hàng  mà  người  bán  đã  bán  thành  công

trong  một  khoảng  thời  gian  được  lựa chọn. Đơn hàng thành công thường được

hiểu là các đơn hàng đã được giao đến tay người mua và không có yêu cầu hoàn

trả.

Tính bằng cách cộng tổng giá trị tiền tệ của tất cả các đơn hàng có trạng

thái "đã giao hàng thành công" trong khoảng thời gian được chỉ định.

Ý nghĩa đối với người bán:

Chỉ số doanh thu là chỉ số trực tiếp nhất thể hiện hiệu quả hoạt động bán

hàng của người bán. Doanh thu cao chứng tỏ người bán đang bán được nhiều sản

phẩm với tổng giá trị lớn và ngược lại, từ đó đánh giá được hiệu quả kinh doanh

của  cửa hàng trong thời gian đó. Đồng thời nó cũng giúp ước tính quy mô hoạt

80

động kinh doanh của cửa hàng, từ đó có kế hoạch mở rộng hoặc điều chỉnh phù

hợp.

Sự  thay  đổi  trong  doanh  thu  là  một  điều  đáng  để  lưu  ý  đối  với các cửa

hàng,  nếu  doanh  thu  tăng  cửa  hàng  cần  tìm hiểu nguyên nhân khiến doanh thu

tăng,  từ  đó  đưa  ra  các  hành động nhằm duy trì lợi thế này. Ngược lại, việc suy

giảm doanh thu có thể là một dấu hiệu báo động, thúc đẩy người bán phải tìm ra

lý do khiến cửa hàng sụt giảm doanh số và có biện pháp khắc phục phù hợp.

1.1.2. Số đơn hàng

Tổng số lượng các đơn hàng mà người mua đã đặt mua thành công từ cửa

hàng của người bán trong một khoảng thời gian nhất định. Mỗi đơn hàng, bất kể

số lượng sản phẩm bên trong, được tính là một đơn vị.

Tính bằng cách cộng tổng số lượng tất cả các đơn hàng có trạng thái "đã

giao hàng thành công" trong khoảng thời gian được chỉ định.

Ý nghĩa đối với người bán:

Chỉ số này giúp chủ cửa hàng đánh giá được khối lượng giao dịch của cửa

hàng,  từ  đó  phản  ánh  được tình hình kinh doanh cũng như là thước đo tốt nhất

thể hiện hiệu quả của các hoạt động nhằm nâng cao số lượng đơn hàng của cửa

hàng  trước  đó. Người bán cần quan tâm đến chỉ số này để có thể đánh giá hiệu

quả  hoạt  động,  nắm  bắt  nhu  cầu  người  mua  và  dựa  trên  cơ sở này để dự đoán

nhu cầu của người mua trong tương lai.

Chỉ số này nên được thống kê bằng số và biểu đồ đường (line chart) theo

thời  gian,  có  so  sánh  với  cùng  kỳ  của  đơn  vị

thời  gian

trước

(tuần/tháng/quý/năm) để nhận biết xu hướng.

81

1.1.3. Giá trị đơn hàng trung bình (AOV)

  Giá  trị đơn hàng trung bình là số tiền trung bình mà một khách hàng chi

tiêu cho mỗi đơn hàng mua thành công tại cửa hàng của người bán.

AOV =

𝑇ổ𝑛𝑔 𝑑𝑜𝑎𝑛ℎ 𝑡ℎ𝑢
𝑇ổ𝑛𝑔 𝑠ố đơ𝑛 ℎà𝑛𝑔 ℎ𝑜à𝑛 𝑡ấ𝑡

 x 100%

-  Tổng  số  đơn  hàng  hoàn  tất  là  số  đơn  hàng  có  trạng  thái  đã  giao  thành

công

-  Tổng  doanh  thu  là  tổng  giá  trị  của  các  đơn  hàng  có  trạng  thái  đã  giao

thành công

Ý nghĩa đối với người bán:

Giá  trị  đơn hàng trung bình thể hiện phân khúc khách hàng mục tiêu mà

cửa  hàng  đang  nhắm  đến  và  phục  vụ,  người  bán  cần  chú  ý  đến  chỉ  số  này  để

phán  đoán  nhu  cầu  sản  phẩm  của  người  mua,  từ  đó  đưa  ra các lựa chọn chính

xác  hơn trong chiến lược về giá, nâng cao tỷ lệ mua hàng và thỏa mãn nhu cầu

của các khách hàng tiềm năng.

Chỉ số này nên sử dụng biểu đồ đường (line chart) theo thời gian để theo

dõi sự biến động của giá trị đơn hàng trung bình.

1.1.4. Số đơn đổi trả/hoàn tiền

Số lượng đơn đổi trả đóng vai trò như một “dấu hiệu cảnh báo” cho chất

lượng sản phẩm của chính cửa hàng. Khi số đơn đổi trả càng nhiều thì có nghĩa

là cửa hàng càng có nhiều nguy cơ quảng cáo sai sự thật về sản phẩm hoặc chất

lượng sản phẩm không đạt kỳ vọng như cam kết. Đây là một chỉ số đặc biệt quan

trọng  trong  ngành  hàng  secondhand,  giúp  đánh  giá  độ uy tín của người bán và

chất lượng hàng hóa. Người bán cần kiểm soát số lượng đơn đổi trả ở mức thấp

nhất  có  thể  để  tối  ưu  hóa  nguồn  lực,  thời  gian  và  giữ  uy  tín lâu dài với khách

hàng.

82

1.1.5. Xây dựng biểu đồ thể hiện xu hướng (Line chart)

Sử dụng biểu đồ đường (Line chart) để thể hiện xu hướng giúp người bán

theo dõi các chỉ tiêu:

-  Doanh thu

-  Số đơn hàng

-  Giá trị đơn hàng trung bình (AOV)

-  Số đơn hàng đổi trả

Biểu đồ đường sẽ hỗ trợ tốt nhất sự thay đổi xu hướng của các chỉ số trên

theo thời gian, dễ dàng phát hiện những điểm bất thường (tăng vọt hay giảm đột

ngột)  của các chỉ số từ đó giúp người bán có những thay đổi phù hợp, tức thời.

Biểu  đồ  đường  còn  giúp  người  bán  so  sánh  nhiều  chuỗi  chỉ  số  trên  cùng  một

biểu  đồ,  đưa ra kết luận giữa sự tương quan của các chỉ số với nhau. Và hỗ trợ

dự báo xu hướng các chỉ số trong tương lai.

Biểu đồ được xây dựng đo lường theo khung thời gian: Tháng/Quý/Năm

Hình 1.1. Thống kê doanh thu và giá trị đơn hàng trung bình phía Người

bán

83

1.2. Hiệu suất người dùng

1.2.1. Lượt truy cập (Visits)

Số lượt truy cập thể hiện tổng số lần người dùng truy cập vào gian hàng,

website  hoặc  ứng  dụng  bán  hàng  trong  một  khoảng thời gian nhất định, bất kể

người dùng đó là mới hay cũ.

Ý  nghĩa  đối với người bán: Đo lường mức độ quan tâm của khách hàng,

đánh  giá  hiệu quả các kênh tiếp cận khách hàng, phản ánh sức hấp dẫn của sản

phẩm hoặc thương hiệu.

1.2.2. Tỷ lệ khách hàng quay lại (PDR)

  Chỉ  số  này thể hiện tỷ lệ phần trăm số khách hàng đã mua hàng từ

cửa  hàng  của người bán ít nhất hai lần trở lên trên tổng số khách hàng đã

từng mua hàng.

PDR  =

𝐾ℎá𝑐ℎ ℎà𝑛𝑔 đã 𝑡ℎự𝑐 ℎ𝑖ệ𝑛 í𝑡 𝑛ℎấ𝑡 ℎ𝑎𝑖 𝑙ầ𝑛 𝑚𝑢𝑎 ℎà𝑛𝑔
𝑇ổ𝑛𝑔 𝑠ố 𝑘ℎá𝑐ℎ đã 𝑚𝑢𝑎 ℎà𝑛𝑔

 x 100%

Ý nghĩa đối với người bán:

Chỉ số này đo lường sự hài lòng, sự trung thành của khách hàng đối với

sản  phẩm  của  người  bán.  chỉ  số  này  cũng  chỉ  được  áp  dụng  trong  trường  hợp

người bán bán ít nhất từ hai sản phẩm trở lên và người mua quay trở lại.

Chỉ  số  này  giúp  người  bán  biết được chiến lược bán hàng trên website

của  mình  có  hiệu quả hay không, đồng thời giúp người bán có những kế hoạch

tiết  kiệm  chi  phí  do  chi  phí  giữ  chân  khách  hàng  thấp  hơn  chi  phí  tìm  kiếm

khách mới.

Tỉ lệ PDR cao dự đoán khả năng tăng trưởng doanh thu trong tương lai

nếu người bán có ý định kinh doanh đồ cũ chuyên nghiệp trên Website.

84

Hình 1.2.2. Thống kê số liệu truy cập của khách hàng phía Người bán

1.2.3. Tỷ lệ chuyển đổi từ khách truy cập thành người mua hàng (CR)

Chỉ số này thể hiện tỷ lệ phần trăm số khách hàng truy cập vào cửa hàng

của  người  bán  và thực hiện thành công ít nhất một đơn hàng trong một khoảng

thời gian nhất định.

CR =

𝑆ố đơ𝑛 ℎà𝑛𝑔
𝑇ổ𝑛𝑔 𝑙ượ𝑡 𝑡𝑟𝑢𝑦 𝑐ậ𝑝

 x 100%

-  Tổng  số  đơn  hàng  hoàn  tất  là  số  đơn  hàng  có  trạng  thái  đã  giao  thành

công

-  Tổng số lượt truy cập theo thời gian lựa chọn

Ý nghĩa của chỉ số đối với người bán:

Thể hiện hiệu quả của người bán trong việc biến traffic thành doanh thu.

Đây  là  một  trong  những  tỷ  lệ  được  chú  trọng  nhất  trong  lĩnh  vực  thương  mại

điện  tử  vì  nó  biểu  thị  khả  năng  biến  đổi  lượt  truy  cập  thành  đơn  hàng,  tức  là

những lần truy cập thực sự tạo ra đơn hàng thành công. Người bán nên tìm cách

nâng cao chỉ số này lên để tối ưu hóa nguồn lực và lợi nhuận của bản thân.

85

Hình 1.2.3. Thống kê tỷ lệ chuyển đổi từ khách truy cập thành người mua

hàng

1.2.4. Xây dựng biểu đồ thể hiện xu hướng

Sử dụng biểu đồ đường (Line chart) để thể hiện xu hướng giúp người bán

theo dõi các chỉ tiêu:

-  Lượt truy cập

-  Tỉ lệ khách hàng quay lại (PDR)

-  Tỉ lệ chuyển đổi từ khách truy cập thành người mua hàng (CR)

Biểu đồ đường sẽ hỗ trợ tốt nhất sự thay đổi xu hướng của các chỉ số trên

theo thời gian, dễ dàng phát hiện những điểm bất thường (tăng vọt hay giảm đột

ngột)  của các chỉ số từ đó giúp người bán có những thay đổi phù hợp, tức thời.

Biểu  đồ  đường  còn  giúp  người  bán  so  sánh  nhiều  chuỗi  chỉ  số  trên  cùng  một

biểu  đồ,  đưa ra kết luận giữa sự tương quan của các chỉ số với nhau. Và hỗ trợ

dự báo xu hướng các chỉ số trong tương lai.

Biểu đồ được xây dựng đo lường theo khung thời gian: Tháng/Quý/Năm.

86

1.3. Biểu đồ dự đoán theo ARIMA (trong 3 tháng tới)

Biểu đồ đường thể hiện số người dùng của 9 tháng gần nhất và 3 tháng

tới  giúp  Người  bán  theo  dõi  sự  tăng  trưởng  của  cộng  đồng  mua  bán  trên  nền

tảng. Khi số lượng người dùng tăng đều, đặc biệt là người mua, cơ hội tiếp cận

khách hàng tiềm năng và mở rộng doanh số của Người bán sẽ cao hơn. Dữ liệu

dự  báo  3  tháng  tới  cũng  giúp  Người  bán  chuẩn  bị  kế  hoạch  nhập  hàng,  điều

chỉnh  tồn  kho  và  lên  chiến  lược  bán  hàng  phù  hợp  với  đà  tăng  trưởng  của  thị

trường.

Biểu đồ đường thể hiện số đơn hàng của 9 tháng gần nhất và 3 tháng tới

giúp Người bán đánh giá sức mua thực tế trên sàn. Việc theo dõi xu hướng tăng

giảm  đơn  hàng  qua  các  tháng  hỗ  trợ  Người  bán  điều  chỉnh  các  chương  trình

khuyến mãi, ưu đãi hoặc chiến lược marketing phù hợp với nhu cầu khách hàng.

Dự  báo  đơn  hàng  trong 3 tháng tới còn giúp Người bán chủ động lập kế hoạch

bán hàng, chuẩn bị nguồn hàng và tối ưu vận hành để tận dụng các giai đoạn cao

điểm mua sắm.

Biểu  đồ đường thể hiện doanh thu của 9 tháng gần nhất và 3 tháng tới

giúp  Người bán theo dõi trực tiếp kết quả kinh doanh của chính cửa hàng mình

theo thời gian. Việc quan sát xu hướng doanh thu tăng hay giảm giúp Người bán

đánh giá được hiệu quả các chiến dịch marketing, chương trình khuyến mãi, điều

chỉnh danh mục sản phẩm và giá bán phù hợp. Dữ liệu dự báo doanh thu 3 tháng

tới còn hỗ trợ Người bán chủ động xây dựng kế hoạch tài chính, nhập hàng, tối

ưu kho vận và chuẩn bị các chương trình ưu đãi kịp thời để nắm bắt các cơ hội

tăng trưởng doanh thu trong tương lai.

87

2. Admin

2.1. Hiệu suất hoạt động

2.1.1. Tổng giá trị giao dịch

Tổng  giá trị giao dịch (GMV - Gross Merchandise Value) là tổng số tiền

của tất cả các đơn hàng được đặt trên website trong một khoảng thời gian, chưa

trừ các khoản hoàn tiền, hủy đơn hay phí vận hành.

Ý nghĩa đối với Admin:

Chỉ số này đo lường quy mô hoạt động của sàn thương mại điện tử, lượng

mua,  bán  hàng  hóa  được  giao  dịch  thành công trên nền tảng. Thể hiện mức độ

chi  tiêu  và  sự  sẵn  sàng  của  khách  hàng  cho  việc  chi  tiêu  qua  sàn,  là  cơ  sở  để

đánh giá tiềm năng và sức phát triển của Website. Nhưng vì website bán đồ công

nghệ  cũ  nên  chỉ  số  này  có  thể  biến  động mạnh hơn so với các sàn thương mại

điện tử khác, thiên về phản ánh sức mua nhiều hơn số lượng đơn hàng.

88

2.1.2. Giá trị đơn hàng trung bình (AOV)

  Giá  trị đơn hàng trung bình là số tiền trung bình mà một khách hàng chi

tiêu cho mỗi đơn hàng mua thành công tại cửa hàng của người bán.

AOV =

𝑇ổ𝑛𝑔 𝑑𝑜𝑎𝑛ℎ 𝑡ℎ𝑢
𝑇ổ𝑛𝑔 𝑠ố đơ𝑛 ℎà𝑛𝑔 ℎ𝑜à𝑛 𝑡ấ𝑡

 x 100%

-  Tổng  số  đơn  hàng  hoàn  tất  là  số  đơn  hàng  có  trạng  thái  đã  giao  thành

công

-  Tổng  doanh  thu  là  tổng  giá  trị  của  các  đơn  hàng  có  trạng  thái  đã  giao

thành công

Ý nghĩa đối với ADMIN:

Đối với ADMIN quản lý hệ thống, AOV giúp đánh giá mức độ chi tiêu và

sức  mua  của  khách hàng. AOV cao cho thấy khách hàng có xu hướng mua các

sản phẩm giá trị cao hơn như điện thoại đời mới, laptop cao cấp hoặc mua nhiều

sản  phẩm  cùng  lúc  trong  một  đơn hàng. Ngược lại, AOV thấp có thể phản ánh

khách hàng mua các phụ kiện nhỏ lẻ, hoặc chỉ mua thử các sản phẩm giá trị thấp,

từ  đó  có  thể  cần  xem  lại  chất  lượng  dịch  vụ  hoặc  danh  mục  sản  phẩm  trên

website.

89

Chỉ  số  AOV  còn  giúp  ADMIN  đánh  giá  hiệu  quả  của  các  chương trình

upsell, cross-sell hoặc combo khuyến mãi. Nếu AOV tăng sau khi triển khai các

chương trình bán kèm sản phẩm (ốp lưng, tai nghe, sạc…), điều đó chứng tỏ các

chiến dịch tăng giá trị giỏ hàng đang phát huy tác dụng. Dựa vào AOV, ADMIN

cũng có thể cân nhắc tối ưu danh mục sản phẩm, tăng tỷ trọng các mặt hàng có

giá trị cao để cải thiện hiệu quả kinh doanh lâu dài.

Ngoài ra, AOV còn là cơ sở quan trọng để ADMIN lập kế hoạch vận hành

và tối ưu chi phí marketing. Khi AOV cao, mỗi đơn hàng mang lại doanh thu lớn

hơn,  từ  đó  có  thể  phân  bổ  chi phí quảng cáo, khuyến mãi, logistics hợp lý hơn

mà vẫn đảm bảo lợi nhuận. Đồng thời, việc nắm bắt AOV giúp ADMIN có căn

cứ dự báo doanh thu, lên kế hoạch kho vận và đánh giá hiệu quả vận hành toàn

hệ thống thương mại điện tử.

2.1.3. Tổng Doanh Thu Nền Tảng (Platform Revenue)

Đo  lường  thu  nhập  của  sàn  dựa  trên  phí  giao  dịch  giữa  người  mua  và

người bán thông qua mua hàng trung gian trên sàn.

Ý nghĩa đối với Admin:

Tổng  doanh  thu  của  toàn  bộ  website  là  chỉ  số  quan  trọng  giúp  Admin

đánh giá hiệu quả vận hành và hoạt động kinh doanh của hệ thống. Đây là căn cứ

để  xác  định  mức  độ  tăng  trưởng,  xu  hướng  tiêu  dùng  của  khách  hàng  và  hiệu

suất của từng kênh bán hàng. Đối với Admin, chỉ số này không chỉ phản ánh kết

quả cuối cùng của các hoạt động kỹ thuật, marketing và vận hành, mà còn hỗ trợ

việc phân bổ tài nguyên, nâng cấp hệ thống, đảm bảo ổn định trong các giai đoạn

cao  điểm.  Đồng  thời,  tổng  doanh  thu  còn  là  nền  tảng để xây dựng báo cáo, đề

xuất chiến lược và phát hiện các bất thường có thể ảnh hưởng đến hiệu quả hoạt

động của website.

90

2.1.3. Tổng số đơn hàng (Total orders)

Đo  lường  hiệu  suất  kinh  doanh  của  của  toàn  bộ  các  cửa  hàng  đang bày

bán trên Website.

Ý nghĩa đối với Admin

Tổng  số  đơn  hàng  là  một  chỉ  số  cực  kỳ  quan  trọng  đối  với  Admin  của

website, vì nó không chỉ phản ánh mức độ thành công của website trong việc thu

hút  và  chuyển  đổi  khách  hàng,  mà  còn  giúp  Admin  đánh  giá hiệu quả của các

chiến dịch marketing, quảng cáo và chiến lược bán hàng.

Khi  số  lượng  đơn  hàng  tăng,  Admin  có  thể  khẳng  định  rằng  hệ  thống

đang  hoạt  động  ổn  định,  giao  diện  người  dùng  dễ  sử  dụng,  và quy trình thanh

toán  không  gặp  vấn đề. Điều này cũng giúp Admin nhận diện những thời điểm

cao  điểm, từ đó có thể dự báo nhu cầu hạ tầng, tăng cường khả năng xử lý đơn

hàng và tránh tình trạng quá tải hệ thống.

Ngoài  ra,  tổng  số  đơn  hàng  cũng là căn cứ để Admin phối hợp chặt chẽ

với  các  bộ  phận  khác  như  kho  vận,  chăm  sóc khách hàng và kế toán, đảm bảo

đơn  hàng  được  xử  lý  nhanh  chóng  và  chính  xác,  đồng  thời  cải  thiện quy trình

vận hành và chăm sóc khách hàng.

2.1.3. Tổng số đơn hàng bị đổi trả

Tổng  số  đơn  hàng  đổi  trả  trên  website  thương  mại  điện  tử  bán  đồ công

nghệ cũ phản ánh mức độ chính xác giữa thông tin mô tả sản phẩm và chất lượng

thực tế, đồng thời đo lường sự hài lòng và niềm tin của khách hàng. Chỉ số này

giúp ADMIN đánh giá hiệu quả kiểm định chất lượng, vận hành hậu mãi và phát

hiện sớm các vấn đề về sản phẩm, quy trình bán hàng hoặc vận chuyển. Số đơn

đổi  trả  tăng  cao  có thể cho thấy thông tin sản phẩm chưa đầy đủ, kiểm tra chất

lượng chưa chặt chẽ hoặc trải nghiệm mua hàng chưa tốt, từ đó ảnh hưởng trực

tiếp đến uy tín và chi phí vận hành của sàn.

91

Ý nghĩa đối với ADMIN

Đối  với  ADMIN,  tổng  số  đơn  hàng  đổi trả là chỉ số quan trọng để kiểm

soát chất lượng toàn bộ quy trình vận hành. Chỉ số này giúp ADMIN đánh giá độ

chính xác của mô tả sản phẩm, hiệu quả quy trình kiểm định hàng hóa trước khi

bán  và  chất  lượng  dịch  vụ  hậu  mãi.  Số  đơn đổi trả tăng cao cảnh báo sớm các

vấn đề tiềm ẩn như sai lệch thông tin, kiểm tra chất lượng chưa kỹ, đóng gói vận

chuyển kém hoặc chính sách chăm sóc khách hàng chưa hợp lý. Việc theo dõi sát

sao chỉ số này giúp ADMIN chủ động điều chỉnh quy trình, đảm bảo uy tín sàn

và tối ưu chi phí vận hành.

2.1.4. Xây dựng biểu đồ thể hiện xu hướng

-  Biểu đồ đường (Line chart):

Sử dụng biểu đồ đường (Line chart) để thể hiện xu hướng giúp người bán

theo dõi các chỉ tiêu:

-  Tổng giá trị giao dịch (GMV)

-  Giá trị đơn hàng trung bình (AOV)

-  Tổng doanh thu nền tảng (platform Revenue)

-  Tổng số đơn hàng (Total orders)

-  Tổng số đơn hàng bị đổi trả

Biểu đồ đường sẽ hỗ trợ tốt nhất sự thay đổi xu hướng của các chỉ số trên

theo thời gian, dễ dàng phát hiện những điểm bất thường (tăng vọt hay giảm đột

ngột)  của các chỉ số từ đó giúp người bán có những thay đổi phù hợp, tức thời.

Biểu  đồ  đường  còn  giúp  người  bán  so  sánh  nhiều  chuỗi  chỉ  số  trên  cùng  một

biểu  đồ,  đưa ra kết luận giữa sự tương quan của các chỉ số với nhau. Và hỗ trợ

dự báo xu hướng các chỉ số trong tương lai.

92

2.2. Hiệu suất người dùng

2.2.1. Lượt truy cập Website

Đo lường tổng số lượt người dùng truy cập vào toàn bộ website trong một

khoảng thời gian được chọn lọc. Điều này bao gồm tất cả các trang, từ trang chủ,

trang danh mục sản phẩm, trang chi tiết sản phẩm, trang cửa hàng của người bán,

đến các trang thông tin khác.

Thống kê tổng số lượng truy cập vào tất cả các trang của website theo thời

gian được chọn.

Ý nghĩa đối với ADMIN:

Chỉ  số  này  cho  thấy mức độ quan tâm và sự thu hút của website đối với

người dùng internet. Admin có thể xem sự biến đổi tăng giảm theo thời gian của

chỉ  số.  Giúp  Admin  có  đánh  giá  tổng quan về các bài viết, sản phẩm nào đang

thu  hút  người  dùng  trên  trang  bán hàng đồ điện tử cũ. Từ đó có thể điều chỉnh

chiến lược nội dung phù hợp với nhu cầu, đồng thời có các chính sách linh hoạt,

phù hợp với những người bán trên Website. Khả năng “traffic” của website đưa

đến Admin nhận định về mức độ nhu cầu của người dùng đối với các sản phẩm

đang có trên website

2.2.2. Số lượng người dùng mới (Tháng/Quý/Năm)

Số lượng người dùng mới thể hiện tổng số người bán và người mua đăng

ký  tài  khoản  mới  trên  nền  tảng  trong một khoảng thời gian (Tháng/Quý/Năm).

Chỉ  số  này  phản  ánh  mức  độ  hấp  dẫn  và  khả  năng  thu  hút  người  dùng  của

website,  đồng  thời  là  chỉ  báo  quan  trọng  về  sức  tăng  trưởng  hệ  sinh  thái  mua

bán.

Ý nghĩa đối với ADMIN:

Đối  với ADMIN, số lượng người dùng mới là chỉ số quan trọng để đánh

giá  hiệu  quả  thu  hút và mở rộng tệp người dùng trên nền tảng. Số lượng người

93

bán mới phản ánh sức hút của sàn đối với nhà cung cấp, đảm bảo đa dạng nguồn

hàng,  còn  số  lượng  người mua mới cho thấy mức độ lan tỏa thương hiệu và sự

hấp  dẫn  của sản phẩm, dịch vụ. Việc theo dõi chỉ số này giúp ADMIN kịp thời

điều chỉnh các chiến dịch marketing, chính sách hỗ trợ người bán mới, cũng như

kiểm soát chất lượng người dùng đầu vào để duy trì sự phát triển bền vững cho

toàn hệ thống.

2.2.3. Tỷ lệ chuyển đổi từ khách truy cập thành người mua hàng (CR)

Chỉ số này thể hiện tỷ lệ phần trăm số khách hàng truy cập vào cửa hàng

của  người  bán  và thực hiện thành công ít nhất một đơn hàng trong một khoảng

thời gian nhất định.

CR =

𝑆ố đơ𝑛 ℎà𝑛𝑔
𝑇ổ𝑛𝑔 𝑙ượ𝑡 𝑡𝑟𝑢𝑦 𝑐ậ𝑝

 x 100%

-  Tổng  số  đơn  hàng  hoàn  tất  là  số  đơn  hàng  có  trạng  thái  đã  giao  thành

công

-  Tổng số lượt truy cập theo thời gian lựa chọn

Ý nghĩa đối với Admin:

94

Dựa  vào  chỉ  số  này  Admin  đánh  giá  khả  năng,  xu  hướng  thu  hút  của

khách hàng đối với mặt hàng, người bán hàng nào thông qua hình thức cửa hàng,

chính  sách  hậu  mãi  của  người  bán  từ  đó  điều  chỉnh  linh  hoạt  các  chính  sách

nhằm thúc đẩy mua hàng trên các trang người bán có độ phản hồi tốt, mặt hàng

chất lượng hơn, được đánh giá cao hơn.

2.2.4. Tỉ lệ khách hàng quay lại (PDR)

 Chỉ số này thể hiện tỷ lệ phần trăm số khách hàng đã mua hàng từ Wesite

ít nhất hai lần trở lên trên tổng số khách hàng đã từng mua hàng.

PDR  =

𝐾ℎá𝑐ℎ ℎà𝑛𝑔 đã 𝑡ℎự𝑐 ℎ𝑖ệ𝑛 í𝑡 𝑛ℎấ𝑡 ℎ𝑎𝑖 𝑙ầ𝑛 𝑚𝑢𝑎 ℎà𝑛𝑔
𝑇ổ𝑛𝑔 𝑠ố 𝑘ℎá𝑐ℎ đã 𝑚𝑢𝑎 ℎà𝑛𝑔

 x 100%

Ý nghĩa đối với Admin

Tỷ lệ khách hàng quay lại (PDR) có ý nghĩa quan trọng đối với Admin vì

nó phản ánh mức độ hài lòng và trung thành của khách hàng. PDR cao cho thấy

khách hàng có trải nghiệm mua sắm tích cực và sẵn sàng quay lại, đồng thời cho

thấy hiệu quả của các chiến lược giữ chân khách hàng.

Điều  này  giúp  Admin  tối  ưu  hóa  chi  phí,  vì  việc  giữ  khách  hàng  cũ

thường  hiệu  quả  hơn  thu  hút  khách  hàng  mới.  Ngoài ra, PDR còn giúp Admin

phát hiện vấn đề trong sản phẩm hoặc dịch vụ, từ đó cải thiện chất lượng và tăng

sự hài lòng của khách hàng. PDR cũng là chỉ số quan trọng để dự báo doanh thu

dài hạn và lập kế hoạch phát triển bền vững.

95

2.2.5. Xây dựng biểu đồ thể hiện xu hướng

Biểu đồ đường thể hiện Người dùng mới, lượt truy cập web, Tổng số đơn

hàng  và  đơn  đổi  trả  hàng  theo  thời  gian  giúp  ADMIN  và  Người  bán  quan  sát

tổng  thể  toàn bộ hành trình mua sắm của khách hàng trên nền tảng. Qua đó, có

thể  theo  dõi  được  mức  độ  thu  hút  người  dùng  mới,  hiệu  quả  thu  hút  lượt truy

cập, khả năng chuyển hóa thành đơn hàng, đồng thời giám sát mức độ phát sinh

đổi trả hàng hóa. Việc quan sát liên tục các chỉ số này giúp phát hiện sớm những

thay  đổi  bất  thường,  từ  đó  điều  chỉnh  kịp  thời  chiến lược marketing, vận hành

kho,  chăm  sóc  khách  hàng  và  chính  sách  đổi  trả  để  duy  trì sự ổn định và tăng

trưởng của hệ thống.

Biểu  đồ  đường  thể  hiện  xu  hướng  tỷ  lệ  chuyển  đổi  từ  khách  truy  cập

thành người mua và tỷ lệ đơn đổi trả hàng theo thời gian giúp đánh giá sâu hơn

hiệu quả hoạt động của sàn và chất lượng dịch vụ. Tỷ lệ chuyển đổi cao cho thấy

khả  năng  thuyết  phục  khách  mua  hàng  tốt,  nội  dung  sản  phẩm  hấp  dẫn,  chính

sách  bán  hàng  hiệu  quả;  ngược lại, tỷ lệ đổi trả cao lại phản ánh các vấn đề về

chất lượng sản phẩm, thông tin mô tả chưa chính xác hoặc trải nghiệm hậu mãi

chưa tốt. Việc theo dõi đồng thời hai tỷ lệ này giúp Người bán và ADMIN nhanh

chóng  nhận  biết  điểm  mạnh,  điểm  yếu  trong  quá  trình  vận  hành và điều chỉnh

kịp thời để tối ưu hiệu quả kinh doanh.

96

3.2.3. Biểu đồ dự đoán theo ARIMA (3 tháng tới)

Biểu đồ đường thể hiện số người dùng của 9 tháng gần nhất và 3 tháng

tới giúp theo dõi tốc độ tăng trưởng người dùng trên nền tảng, bao gồm cả người

mua và người bán. Khi số lượng người dùng tăng ổn định, điều đó phản ánh sự

hấp dẫn và khả năng thu hút khách hàng mới của website, mở rộng cơ hội kinh

doanh  và  tăng  trưởng  doanh  số  cho  người  bán.  Phần  dự  báo  3  tháng  tới  giúp

người  bán  có  cơ  sở  lập  kế  hoạch  nhập hàng, marketing và phát triển sản phẩm

phù hợp với đà tăng trưởng người dùng.

Biểu đồ đường thể hiện số đơn hàng của 9 tháng gần nhất và 3 tháng tới

giúp  người  bán  đánh  giá  xu  hướng  tiêu  dùng  thực  tế  trên  sàn.  Qua  đó,  có  thể

nhận  diện  được  những  thời  điểm  đơn  hàng  tăng  mạnh do mùa vụ, khuyến mãi

hoặc  chiến  dịch  marketing  hiệu  quả.  Số  liệu  dự  báo  3  tháng  tiếp  theo  hỗ  trợ

người bán chủ động chuẩn bị hàng hóa, điều chỉnh chương trình bán hàng và sẵn

sàng nguồn lực vận hành để đón đầu các giai đoạn cao điểm mua sắm.

Biểu  đồ đường thể hiện doanh thu của 9 tháng gần nhất và 3 tháng tới

phản  ánh  trực  tiếp  kết  quả  kinh  doanh của từng người bán theo thời gian. Việc

theo dõi xu hướng doanh thu giúp người bán đánh giá được hiệu quả chiến lược

kinh doanh, quản lý tốt hơn kế hoạch tài chính, điều chỉnh giá bán, danh mục sản

phẩm và các chương trình khuyến mãi. Dữ liệu dự báo 3 tháng tới là cơ sở quan

trọng để người bán lập kế hoạch tăng trưởng doanh thu, tối ưu lợi nhuận và tận

dụng tốt các cơ hội kinh doanh trong tương lai.

97

98

99

CHƯƠNG VI. KẾT LUẬN

Trong  bối  cảnh  dữ  liệu  đang  ngày  càng  trở  thành  một  nguồn  lực  chiến

lược, việc tổ chức, khai thác và chuyển hóa dữ liệu thành tri thức có giá trị thực

tiễn  là  yếu  tố  then  chốt  cho  sự phát triển của các nền tảng thương mại điện tử.

Với mục tiêu đó, đề tài “Quản lý và ứng dụng dữ liệu trong website mua bán đồ

công nghệ cũ” đã tập trung vào việc thiết kế một kiến trúc phân tích dữ liệu có

tính  hệ  thống,  bền  vững  và  định  hướng  mở  rộng.  Sau  đây  chúng  em xin được

tổng kết những thành tựu, hạn chế và hướng phát triển trong tương lai của đề tài.

1. Thành tựu

-  Xây  dựng  hệ  thống  phân  tích  và  thiết kế chi tiết: Đã tiến hành phân tích sâu

rộng  các  yêu  cầu  chức  năng  và  phi  chức  năng  cho  cả  hai  đối  tượng  người

dùng  chính  là  Người  bán  và  Admin.  Hệ  thống  được  thiết kế hoàn chỉnh với

các biểu đồ Use Case, biểu đồ hoạt động, và biểu đồ tuần tự, mô tả rõ ràng các

luồng tương tác của người dùng với hệ thống.

-  Thiết  kế  một  quy  trình  ETL  (Extract  -  Transform  -  Load):  Đề  tài đã đề xuất

một  kiến  trúc  ETL  modular,  có  khả  năng  mở  rộng,  với  các  giai  đoạn  được

định nghĩa rõ ràng từ trích xuất dữ liệu, kiểm soát chất lượng, biến đổi dữ liệu

thô  thành  các  chỉ  số  kinh  doanh (KPIs), cho đến việc tải dữ liệu vào kho dữ

liệu.  Việc tích hợp các công nghệ như Spring Scheduler để lập lịch và Kafka

để phân phối dữ liệu gần thời gian thực cho thấy một định hướng thiết kế hiện

đại và hiệu quả.

-  Ứng  dụng mô hình dự báo nâng cao: Đề tài không chỉ dừng lại ở việc thống

kê  dữ  liệu  quá  khứ  mà  còn  đi  sâu  vào  ứng  dụng mô hình dự báo chuỗi thời

gian ARIMA để dự đoán các chỉ số quan trọng như tổng lượng người dùng, số

đơn hàng và doanh thu. Điều này cung cấp một công cụ mạnh mẽ, giúp Người

bán  và  Admin  chuyển từ việc phản ứng bị động sang việc ra quyết định một

cách chủ động và có chiến lược.

100

-  Thiết kế Dashboard trực quan và các chỉ số thống kê ý nghĩa: Đã phân tích và

thiết kế các bảng thống kê (Dashboard) chuyên biệt cho Người bán và Admin.

Các chỉ số như Doanh thu, Giá trị đơn hàng trung bình (AOV), Tỷ lệ chuyển

đổi  (CR),  Tỷ  lệ  khách  hàng  quay lại (PDR) được lựa chọn cẩn thận để cung

cấp  cái  nhìn  toàn  diện  từ hiệu suất bán hàng tổng thể đến hành vi của người

dùng,  giúp  tối  ưu  hóa  hoạt  động  kinh  doanh  và  nâng  cao trải nghiệm khách

hàng.

-  Xây  dựng  cơ  sở  dữ  liệu  và  kiến  trúc  hệ  thống  hoàn  chỉnh:  Đã  thiết  kế  một

lược  đồ  cơ  sở  dữ  liệu  quan  hệ  chi  tiết,  bao  gồm  15  bảng  thực thể, đảm bảo

tính toàn vẹn và khả năng lưu trữ hiệu quả cho toàn bộ hoạt động của website.

Cùng với đó, biểu đồ lớp (Class Diagram) cũng được xây dựng, định nghĩa rõ

ràng  các  đối  tượng,  thuộc  tính  và  mối  quan  hệ  trong  hệ  thống, tạo nền tảng

vững chắc cho việc phát triển phần mềm sau này.

2. Hạn chế

-  Mô hình dữ liệu được đơn giản hóa: Quy trình ETL được thiết kế dựa trên giả

định rằng dữ liệu được trích xuất từ các hệ thống nguồn (OLTP) có cấu trúc rõ

ràng  và  nhất  quán.  Trong  môi  trường  thực  tế,  dữ  liệu  có  thể  đến  từ  nhiều

nguồn  phân  tán, thiếu cấu trúc và không đồng nhất, điều này sẽ làm cho giai

đoạn "Extract" (Trích xuất) và "Transform" (Biến đổi), đặc biệt là khâu kiểm

soát chất lượng, trở nên phức tạp hơn nhiều so với mô hình lý thuyết.

-  Các giới hạn nội tại của mô hình dự báo ARIMA: Mặc dù mô hình ARIMA là

một công cụ mạnh mẽ để phân tích chuỗi thời gian, nó vẫn có những giả định

và hạn chế nhất định. Mô hình này giả định rằng mối quan hệ trong dữ liệu là

tuyến tính và chuỗi thời gian phải có tính dừng (hoặc được chuyển đổi thành

chuỗi  dừng).  Do  đó,  mô  hình  có  thể  không  nắm  bắt  được các xu hướng phi

tuyến  tính  phức tạp hoặc các ảnh hưởng đột ngột từ các yếu tố bên ngoài (ví

dụ như một chiến dịch marketing đặc biệt, sự xuất hiện của đối thủ cạnh tranh

mạnh) mà không được phản ánh trong dữ liệu lịch sử.

101

3. Hướng phát triển trong tương lai

Từ những hạn chế trên, có thể đề xuất các hướng phát triển và cải tiến cho đề tài

trong tương lai:

-  Tích  hợp  các  mô  hình  Machine  Learning  nâng  cao:  Ngoài  ARIMA,  có

thể  nghiên  cứu  và  áp  dụng  các  mô  hình  học  máy  khác  như  Prophet,

LSTM  cho  việc  dự  báo  để  tăng  độ  chính  xác,  hoặc  các  thuật  toán phân

cụm  (Clustering)  để  phân  khúc  khách hàng, và xây dựng hệ thống gợi ý

sản  phẩm  (Recommendation  System)  để  cá  nhân  hóa  trải  nghiệm  mua

sắm.

-  Mở  rộng  hệ  thống  phân  tích thời gian thực: Phát triển sâu hơn hệ thống

sử  dụng  Kafka  để xây dựng các dashboard có khả năng cập nhật dữ liệu

theo  thời  gian  thực  và  thiết lập hệ thống cảnh báo tự động khi phát hiện

các anomalie (bất thường) trong dữ liệu kinh doanh.

-  Xây  dựng  khung  A/B Testing: Tích hợp một framework cho phép Admin

và  người  bán  thực  hiện  các  thử  nghiệm  A/B ( thử nghiệm các giao diện

khác  nhau, các chương trình khuyến mãi) và sử dụng hệ thống phân tích

dữ liệu để đo lường hiệu quả một cách chính xác.

102

TÀI LIỆU THAM KHẢO

Đặng, Thị Việt Đức; Trần, Quốc Khánh (2022), Bài giảng Quản lý và ứng dụng
cơ sở dữ liệu trong tài chính, Học viện Công nghệ Bưu chính Viễn thông

Spring Boot Documentation, https://docs.spring.io/spring-boot/

MySQL Documentation, https://dev.mysql.com/doc/

React Documentation, https://react.dev/

Apache Kafka Documentation, https://kafka.apache.org/documentation/

George E. P. Box, Gwilym M. Jenkins, Gregory C. Reinsel, and Greta M. Ljung,
Time Series Analysis: Forecasting and Control

103

