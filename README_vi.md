# CausaMem - Hệ Thống Trí Nhớ Nhân Quả

> Cho Agent AI của bạn một trí nhớ suốt đời | Hệ Thống Trí Nhớ Nhân Quả cho Agent AI

[English](README_en.md) | [中文](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Tiếng Việt](README_vi.md)

---

## Bối cảnh

CausaMem là hệ thống trí nhớ độc lập cho Agent AI. Sau khi phát triển xong, chúng tôi đã tham khảo [Claude-Mem](https://github.com/thedotmack/claude-mem) và triển khai chức năng cốt lõi **nén có cấu trúc bằng AI**, mở rộng thêm khả năng **suy luận nhân quả**.

## Tính năng chính

| Tính năng | Mô tả |
|-----------|--------|
| Trí nhớ 4 lớp | Sự kiện → Dòng thời gian → Quan hệ → Tóm tắt |
| Nén có cấu trúc AI | Tự động trích xuất decided/learned/completed/next_steps |
| Suy luận nhân quả | Suy ra cause (nguyên nhân) / effect (hệ quả) |
| Tìm kiếm 3 động cơ | Vector + FTS5 + Chuỗi nhân quả |
| Wiki có thể đọc | Định dạng Obsidian Wiki |
| Thẻ loại | DECISION / INSIGHT / BUG / FEATURE / CHANGE / DAILY |

## Khởi đầu nhanh

```bash
git clone https://github.com/MaiHHConnect/MHH-Causality-Memory.git
cd MHH-Causality-Memory
cd scripts/gbrain
python gbrain.py put-structured memory-2026 "Chúng tôi đã thảo luận về hệ thống trí nhớ, quyết định dùng cấu trúc 4 lớp"
python gbrain.py causal "tri nho"
```

## Ghi nhận

Được lấy cảm hứng từ [Claude-Mem](https://github.com/thedotmack/claude-mem).

## Giấy phép

MIT License
