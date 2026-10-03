# Boshlash

Bu tayyor montaj papkasi. Ichida ikki xil uslub, skriptlar, shablonlar va sun'iy demo bor. Hech kimning yuzi, shaxsiy videosi yoki API kaliti yo'q.

1. ZIPni alohida papkaga oching. Python 3.12 va FFmpeg o'rnating. Terminalda `ffmpeg -version` va `ffprobe -version` ishlashi kerak.
2. PowerShellni shu papkada ochib, `powershell -ExecutionPolicy Bypass -File .\setup.ps1` yozing.
3. Avval README'dagi demo buyruqlarini sinab ko'ring. Demo uchun API kalit kerak emas. Videodagi ovoz test signali; matn haqiqiy transkript emas.
4. O'z videongizni yangi nom bilan olib kiring: `.venv/Scripts/python.exe -X utf8 scripts/toolkit.py init "D:\video.mp4" birinchi_video`.
5. O'zingiz ishlatadigan AI'ga `PROMPT_FOR_YOUR_AI.md` matnini yuboring. U `CLAUDE.md` / `AGENTS.md`ni o'qib, montajni rejalashtirsin.
6. Yangi video bo'lsa transkript va so'z vaqtlarini yarating. Tayyor transkript bo'lsa qayta transkripsiya qilmang. API kalitni faqat o'z kompyuteringizda saqlang.
7. Gaplar tartibini `cuts.json`da yozing, `render.py`ni ishlating, keyin `toolkit.py timing` bilan yangi vaqtlarni hisoblang. Eski vaqtlarni yangi tartibga ko'chirib qo'ymang.
8. `edit.json` yoki `hf_plan.json`ni yozing. Preview/check kadrlarni ochib tekshiring: bosh kesilmasin, caption og'izni yopmasin, rasmlar gapga mos bo'lsin.
9. To'liq renderdan keyin `toolkit.py finalize` bilan umumiy ovozni tekshiring. Faqat o'tgan video `final/`ga tushadi.

Hamma aniq buyruq va sozlamalar `README.md`da. AI montajni rejalashtiradi; bu papka o'zi mustaqil ravishda yaxshi b-roll tanlab yoki ssenariy yozib bermaydi.

Do'stingizga yana yuborayotganda asl toza ZIPni yuboring. Ishlatilgan papkangiz ichida video, yuz va `.env` bo'lishi mumkin.
