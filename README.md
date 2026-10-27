# Group-2---Pattern-Matching

## TV4 Tuan

Oracle và bộ kiểm chứng độc lập: [docs/tv4/README.md](docs/tv4/README.md).

```powershell
py -B -X utf8 -m unittest discover -v
py -B -X utf8 -m tv4.validate --seed 11 --fuzz-cases 10000 --out docs/tv4/reports/my_seed11
```

Validator tách kết quả tìm kiếm trên mẫu chuẩn khỏi hợp đồng hoặc đầu việc còn mở; đọc trạng thái trong JSON, không chỉ số test đã pass. Tiến độ nhóm và phần Validation nằm trong docs/tv4/.
