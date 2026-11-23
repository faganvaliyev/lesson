# Rəqəmsal uçurum və əmək bazarı

Kollokvium layihəsi (Format A: açıq data ilə alət) üçün Streamlit dashboard.

**Sual:** Azərbaycanda internet istifadəsində cins və bölgə fərqləri necə dəyişib və onlar əmək bazarındakı fərqlərlə üst-üstə düşürmü?

## Data
- `World Bank WDI API` — internet istifadəsi, sabit genişzolaqlı abunə, işçi qüvvəsində iştirak və məşğulluq (cins üzrə). Tətbiq datanı canlı oxuyur; API əlçatan olmasa `data/wdi_snapshot.csv` istifadə olunur.
- `data/manual.csv` — WDI-də olmayan göstəricilər (ITU, DSK, Dünya Bankı hesabatları), hər sətirdə mənbə ilə.

## İşə salmaq
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
[share.streamlit.io](https://share.streamlit.io) → New app → bu repo, branch `main`, fayl `app.py`.
