# xct-xteam-icon

API وسيط للأيقونات ديال Free Fire — الرابط العمومي نضيف، ورابط المصدر الأصلي مخفي.

## الاستعمال

```
GET https://xct-xteam-icon.vercel.app/<icon_name>.png
```

مثال:

```
https://xct-xteam-icon.vercel.app/Icon_Pet_Golden_Panther.png
```

- `200` → صورة PNG ديال الأيقونة
- `404` → الأيقونة ما كايناش
- `400` → اسم الأيقونة غير صالح
- `502` → المصدر ما جاوبش

## كيفاش خدام

الأيقونة كتجي من مصدر خارجي، والرابط ديالو **ما كاينش في الكود** — كاين غير في متغير البيئة `ICON_BASE_URL` (في إعدادات مشروع Vercel). هكذا الرابط العمومي كيبان نضيف:

```
xct-xteam-icon.vercel.app/<icon_name>.png
```

بلا ما يبان المصدر الأصلي.

## الإعداد

متغير بيئة واحد (Vercel → Settings → Environment Variables):

| المتغير | القيمة |
| --- | --- |
| `ICON_BASE_URL` | رابط المصدر ديال الأيقونات (بلا `/` في الآخر) |

## التقنية

- FastAPI + httpx
- Vercel (Python runtime)
- أسماء الأيقونات المسموحة: حروف، أرقام، `_` و `-` فقط
- الصور الناجحة كتتكاشا 24 ساعة (`Cache-Control: public, max-age=86400`)؛ الأخطاء ما كتتكاشاش
