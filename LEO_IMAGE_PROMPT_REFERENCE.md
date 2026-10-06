# Leo — Image Prompt Slash-Command Reference

**Purpose:** Panduan internal untuk memahami modifier visual bertanda `/` saat menyusun prompt gambar.  
**Project:** Alpha  
**Owner:** Leo — image generation via ImageFlow  
**Status:** Reference guide; slash modifiers di bawah ini adalah notasi prompt, bukan slash command Telegram atau setting teknis yang otomatis dijalankan.

**Wajib baca:** Sebelum Leo bertanya tentang brief, memberi saran gaya, atau menulis prompt untuk setiap permintaan gambar, buka dan baca file ini terlebih dahulu. Jangan mengandalkan ingatan atau menebak isi panduan. Jika file tidak bisa diakses, beri tahu pengguna sebelum melanjutkan.

---

## 1. Cara membaca notasi `/`

Pengguna dapat menulis prompt biasa lalu menambahkan modifier, misalnya:

> Buat poster kopi untuk Instagram, suasana pagi di rumah kayu, `/cinematic /realistic /blur /warm`.

Leo mengartikan setiap `/modifier` sebagai arahan visual. Prompt final yang dikirim ke ImageFlow **harus mempertahankan secara literal setidaknya satu token slash yang relevan**, lalu menjelaskan artinya dengan bahasa alami. Jangan menghapus semua token slash saat merapikan prompt. Jika pengguna belum memberi modifier, pilih satu atau beberapa yang cocok dari panduan ini setelah brief dipahami; jangan memilih modifier yang bertentangan dengan permintaan.

Contoh bentuk prompt yang dikirim:

> Modifiers: `/cinematic /realistic /blur:background`. Foto sinematik realistis dengan subjek utama tajam dan latar belakang lembut blur ...

Jika modifier punya nilai, formatnya boleh seperti:

- `/blur:background`
- `/ratio:4:5`
- `/palette:teal-orange`
- `/lens:85mm`

Modifier boleh ditulis dalam urutan apa pun. Teks brief pengguna tetap menjadi sumber utama. Jangan biarkan modifier mengubah subjek, merek, identitas, teks, atau tujuan gambar yang sudah ditentukan.

### Aturan parse

1. Kenali token yang dimulai dengan `/`; jangan menganggap seluruh pesan sebagai command.
2. Gabungkan modifier yang saling melengkapi ke dalam satu arahan visual ringkas.
3. Jika dua modifier bertentangan, pertahankan pilihan yang disebut paling eksplisit/terakhir dan tanyakan hanya bila hasilnya benar-benar mengubah brief.
4. Jika satu modifier punya beberapa makna umum, gunakan arti default pada daftar di bawah. Contoh: `/blur` berarti latar belakang blur, subjek utama tetap tajam.
5. Jangan memasukkan semua modifier secara mekanis. Buang pengulangan dan istilah yang bertentangan agar prompt tetap fokus.
6. Kata yang belum ada di daftar tetap boleh dipahami sebagai arahan bahasa alami; jangan menolak permintaan hanya karena modifier baru.
7. Jelaskan interpretasi singkat jika modifier ambigu atau hasil yang diminta tidak didukung oleh mode/generator yang sedang dipakai.

---

## 2. Kerangka prompt dasar

Bangun prompt dari unsur yang relevan, tidak wajib semuanya:

`Modifier literal: /<gaya> /<fokus> ... + jenis gambar + subjek + pose/aksi + lokasi/latar + framing/sudut kamera + pencahayaan + warna + medium/gaya + mood + detail penting + batasan.`

Awali prompt yang dikirim dengan `Modifiers: /...` dan pertahankan token itu apa adanya, kemudian beri deskripsi natural yang menerangkan hasil visual yang dimaksud.

### Template internal

> **Modifiers: `/<modifier-1> /<modifier-2>`**. **[Jenis/tujuan gambar]** menampilkan **[subjek dan ciri penting]** yang **[aksi/pose/ekspresi]**, berada di **[lingkungan/latar]**. Dibingkai sebagai **[shot size/sudut/komposisi]**, dengan **[pencahayaan]**, **[palet warna]**, dan **[medium/gaya visual]**. Nuansa **[mood]**. Pertahankan **[detail wajib]**; hindari **[elemen yang tidak diinginkan]**. Rasio **[rasio]**.

Gunakan deskripsi yang dapat divisualisasikan, bukan tumpukan kata sifat. Pilih 1 gaya utama, 1 mood utama, dan hanya detail yang mendukung tujuan gambar.

### Checklist: prompt gambar yang kuat

Prompt yang baik bukan prompt terpanjang atau penuh kata keren. Prompt yang baik membuat jelas **apa fokusnya, apa yang terjadi, bagaimana gambar dibingkai, dan detail mana yang wajib dipertahankan**.

Gunakan frasa deskriptif yang langsung, bukan sekadar “buat/generate gambar keren”. Adobe Firefly menyarankan prompt spesifik dengan subjek dan descriptor yang jelas (setidaknya tiga kata di Firefly); itu panduan untuk Firefly, bukan syarat teknis ImageFlow.

1. **Tentukan satu fokus utama.** Sebutkan subjek inti lebih dulu; jangan minta lima hal menjadi pusat perhatian sekaligus.
2. **Jelaskan ciri pembeda.** Bentuk, bahan, warna, usia/jenis karakter, ekspresi, pakaian, props, atau detail produk yang memang penting.
3. **Sebutkan aksi/pose dan relasi objek.** Misalnya tangan memegang cangkir, bukan sekadar “barista dan cangkir”.
4. **Tentukan konteks.** Lokasi, latar, waktu, cuaca, dan detail yang mendukung cerita.
5. **Pilih framing dan komposisi.** Close-up/medium/wide, angle kamera, posisi subjek, arah pandang, ruang untuk teks, dan crop safety.
6. **Pilih satu medium/gaya utama.** Tambahkan satu atau dua pendukung bila perlu; hindari mencampur gaya yang bertentangan.
7. **Arahkan cahaya, palet, dan mood.** Gunakan deskripsi spesifik, misalnya soft window light, warm cream-and-terracotta palette, calm premium mood.
8. **Nyatakan batasan yang benar-benar penting.** Contoh: no text, no watermark, keep product label unchanged, background blur only.
9. **Sertakan rasio/penggunaan bila relevan.** Rasio juga harus dicek di setting UI Flow, bukan mengandalkan teks prompt saja.
10. **Pertahankan slash token literal.** Biasanya beberapa token yang saling mendukung sudah cukup; jangan menambahkan seluruh kamus ke satu prompt.

### Formula prompt yang disarankan

`Modifiers: /<jenis-output> /<gaya-utama> /<kamera-atau-efek> /<rasio-bila-perlu>. Subjek utama + ciri spesifik + aksi/pose. Lokasi dan latar. Framing/komposisi. Pencahayaan dan palet. Medium/gaya dan mood. Detail wajib. Hal yang harus dihindari. Penggunaan/rasio.`

### Contoh: prompt lemah → prompt kuat

- **Lemah:** `Buat gambar kopi yang keren, /cinematic /blur.`
- **Lebih kuat:** `Modifiers: /product-photo /cinematic /blur:background /warm. Foto editorial secangkir kopi susu dalam gelas bening di atas meja kayu, uap tipis terlihat, cahaya jendela pagi dari kiri. Gelas dan lapisan kopi tajam; kedai di belakang lembut blur. Palet cream dan cokelat hangat, komposisi vertikal dengan ruang kosong di atas untuk judul. Tanpa tulisan dan logo.`

Kenapa lebih kuat: subjek, bahan, aksi, waktu, sumber cahaya, titik fokus, palet, komposisi, penggunaan, dan batasan semuanya jelas; modifier `/blur` juga diperjelas agar tidak membuat subjek ikut kabur.

---

## 3. Modifier gaya dan medium

| Modifier | Interpretasi default |
|---|---|
| `/cinematic` | Komposisi seperti satu frame film; pencahayaan dan warna dramatis tetapi tetap mendukung cerita. Bukan otomatis gelap atau wide-screen. |
| `/realistic` | Tampilan fotorealistis; anatomi, material, skala, bayangan, dan cahaya alami yang meyakinkan. |
| `/photorealistic` | Mendorong tampilan seperti foto kamera nyata dengan detail optik/material yang jelas. Lebih spesifik daripada `/realistic`. |
| `/animated` | Gambar diam dengan tampilan animasi; bukan video bergerak. Tentukan 2D/3D bila penting. |
| `/2d` | Ilustrasi dua dimensi dengan bentuk dan bayangan grafis. |
| `/3d` | Objek atau karakter dengan volume tiga dimensi dan pencahayaan/render 3D. Tidak otomatis berarti fotorealistis. |
| `/anime` | Bahasa visual animasi Jepang secara umum; fokus pada ciri desain, bukan meniru kreator tertentu. |
| `/cartoon` | Bentuk kartun ekspresif, proporsi dan outline disesuaikan dengan brief. |
| `/clay` | Tampilan seperti model clay/plastisin, permukaan matte dan bentuk buatan tangan. |
| `/stop-motion` | Tampilan frame animasi stop-motion sebagai gambar diam, dengan material dan pose berkarakter. |
| `/vector` | Ilustrasi bersih berbasis bentuk, bidang warna, dan outline; cocok untuk ikon/logo sederhana. |
| `/watercolor` | Pigmen transparan, tepi lembut, dan tekstur kertas cat air. |
| `/oil-painting` | Sapuan cat tebal/berlapis dan tekstur kanvas. |
| `/pencil-sketch` | Garis pensil, arsiran, dan tekstur kertas. |
| `/pixel-art` | Gambar berbasis grid piksel; bentuk dan palet terbatas. |
| `/editorial` | Art direction majalah/iklan editorial yang rapi dan terkurasi. |
| `/product-photo` | Foto produk dengan bentuk, material, label, dan pencahayaan yang terbaca jelas. |
| `/documentary` | Rasa fotografi candid dan natural; hindari kesan terlalu staged. |
| `/surreal` | Perpaduan elemen tak biasa atau logika mimpi yang disengaja, namun tetap punya focal point. |
| `/minimal` | Elemen sedikit, hierarki jelas, ruang kosong terjaga. |

**Jangan gabungkan gaya yang berlawanan tanpa alasan:** misalnya `/photorealistic /flat-vector` atau `/watercolor /chrome-3d`. Jika pengguna memang menginginkan hybrid, jelaskan pembagian materialnya, seperti “subjek 3D, latar ilustrasi cat air.”

### Genre fotografi

| Modifier | Cocok untuk / interpretasi |
|---|---|
| `/photo` | Arah fotografi umum; tambahkan genre dan jenis cahaya. |
| `/portrait-photo` | Portrait manusia; tentukan ekspresi, crop, lensa-look, dan latar. |
| `/fashion-photo` | Editorial pakaian; pose, tekstur kain, styling, dan siluet harus terbaca. |
| `/beauty-photo` | Beauty/makeup; fokus pada kulit, makeup, detail wajah, dan lighting lembut/terarah. |
| `/product-photo` | Produk sebagai hero subject; bentuk, label, material, pantulan, dan shadow harus terkontrol. |
| `/food-photo` | Makanan menggugah selera; tekstur, steam, garnish, angle, dan styling meja. |
| `/lifestyle-photo` | Produk/orang dalam situasi penggunaan sehari-hari yang natural. |
| `/editorial-photo` | Art direction terkurasi seperti majalah atau kampanye. |
| `/documentary-photo` | Rasa candid, observasional, dan tidak terlalu staged. |
| `/street-photo` | Momen urban candid dengan lingkungan sebagai konteks. |
| `/travel-photo` | Lanskap/perjalanan dengan lokasi, kondisi cahaya, dan skala yang jelas. |
| `/landscape-photo` | Pemandangan alam; tentukan foreground, horizon, waktu, dan atmosfer. |
| `/architecture-photo` | Bangunan; perspektif, garis vertikal, material, dan skala. |
| `/interior-photo` | Interior; layout ruang, focal point, material, sumber cahaya, dan lensa-look. |
| `/wildlife-photo` | Satwa pada habitatnya; spesies/pose dan jarak kamera harus jelas. |
| `/sports-photo` | Aksi olahraga; momen puncak, arah gerak, ekspresi, dan freeze/motion blur. |
| `/automotive-photo` | Kendaraan; sudut 3/4, permukaan, pantulan, dan latar. |
| `/still-life-photo` | Objek diam yang ditata; props dan keseimbangan visual. |
| `/macro-photo` | Detail sangat dekat; sebut tekstur/fitur mikro yang menjadi fokus. |
| `/event-photo` | Suasana acara; siapa/momen utama, crowd, dan pencahayaan venue. |

### Library ilustrasi dan medium seni

| Modifier | Interpretasi default |
|---|---|
| `/flat-vector` | Bidang warna rata, siluet tegas, minim shading/tekstur. |
| `/line-art` | Bentuk dibangun terutama dari garis; tentukan tebal-tipis dan warna garis. |
| `/cel-shaded` | Bayangan grafis dengan bidang tegas seperti frame animasi. |
| `/storybook` | Ilustrasi naratif hangat; karakter dan latar terasa seperti halaman buku cerita. |
| `/comic-book` | Panel/ink outline, kontras dan gestur kuat; jangan menambahkan panel/teks kecuali diminta. |
| `/graphic-novel` | Ilustrasi naratif dengan tinta, tekstur, dan pencahayaan yang lebih atmosferik. |
| `/manga` | Bahasa visual manga; pilih B/W atau warna, ekspresi, dan tingkat detail. |
| `/watercolor` | Pigmen transparan, tepi lembut, tekstur kertas. |
| `/gouache` | Cat opak matte dengan bentuk warna solid dan tepi painterly. |
| `/acrylic` | Lapisan cat berwarna pekat; arahkan tekstur bila ingin terlihat. |
| `/ink-wash` | Sapuan tinta, gradasi air, ruang kosong, dan kontras organik. |
| `/charcoal` | Arsiran arang, smudge, dan kontras monokrom. |
| `/colored-pencil` | Jejak pensil warna dan tekstur garis yang terlihat. |
| `/pastel-drawing` | Pigmen pastel berdebu, blending lembut, dan warna powdery. |
| `/linocut` | Bentuk potongan cetak dengan kontras tinggi dan tekstur ukiran. |
| `/woodcut` | Ilustrasi cetak kayu dengan garis pahat dan bidang gelap-terang. |
| `/screenprint` | Bidang cetak rata, warna terbatas, sedikit tekstur registrasi. |
| `/risograph` | Lapisan warna seperti cetak risograph; gunakan palet terbatas dan grain halus. |
| `/paper-cut` | Layer bentuk kertas potong dengan bayangan antar-layer. |
| `/collage` | Potongan foto/kertas/tekstur dikomposisikan; jelaskan bahan dan susunan. |
| `/stained-glass` | Bidang kaca warna dengan garis sambungan/timbal. |
| `/embroidery` | Jahitan benang dan tekstur kain; bukan permukaan cetak datar. |
| `/mosaic` | Gambar tersusun dari potongan kecil seperti ubin/kaca. |
| `/low-poly` | Bentuk faceted geometris dengan jumlah bidang terbatas. |
| `/isometric` | Perspektif isometrik yang rapi, cocok untuk objek/scene diagramatik. |
| `/diorama` | Miniatur scene tiga dimensi; sebut bahan dan sudut pandang. |
| `/clay-render` | Objek/karakter tampak dibentuk dari clay, permukaan matte dan sedikit imperfections. |
| `/3d-toy` | Bentuk seperti figur mainan koleksi, material plastik/vinyl sesuai arahan. |
| `/technical-illustration` | Bentuk mekanis/produk dengan detail terstruktur dan keterbacaan fungsi. |
| `/scientific-illustration` | Penggambaran objek alam/sains yang jelas dan informatif, bukan dekoratif berlebihan. |

### Gerakan seni, era, dan graphic-design flavor

Gunakan ini sebagai **arahan visual umum**, bukan meniru satu karya tertentu. Pasangkan dengan medium, subjek, dan palet agar hasil tidak menjadi campuran era yang acak.

| Modifier | Arah visual |
|---|---|
| `/art-deco` | Geometri dekoratif, simetri, garis tegas, aksen metalik yang terukur. |
| `/art-nouveau` | Garis organik, bentuk flora, lengkung dekoratif, komposisi ornamental. |
| `/bauhaus` | Bentuk geometris dasar, grid, fungsi, warna primer yang terkendali. |
| `/swiss-style` | Grid, tipografi sans-serif, kontras, hierarki dan alignment kuat. |
| `/mid-century-modern` | Siluet sederhana, warna earthy/retro, bentuk organik-modern. |
| `/pop-art` | Warna berani, kontras tinggi, repetisi/halftone bila relevan. |
| `/brutalist-graphic` | Grid/bentuk keras, kontras, tipografi ekspresif; jangan mengorbankan keterbacaan. |
| `/retro-futurism` | Imajinasi masa depan dengan bahasa visual era lampau. |
| `/film-noir` | Monokrom, bayangan tajam, cahaya terarah, mood misteri. |
| `/cyberpunk` | Kota teknologi padat, neon, kontras, detail futuristik; hindari menambah neon tanpa permintaan. |
| `/solarpunk` | Teknologi dan lingkungan hijau yang hidup, cahaya alami, optimistis. |
| `/synthwave` | Neon retro, sunset gradien, grid/gelombang sebagai aksen. |
| `/vaporwave` | Palet pastel/neon, referensi digital-retro dan komposisi surealis. |
| `/steampunk` | Mesin/objek mekanis bernuansa era uap; kuningan dan gear hanya jika mendukung subjek. |
| `/fantasy` | Dunia magis/fantastis; tentukan aturan, makhluk, dan tingkat realisme. |
| `/dark-fantasy` | Fantasi dengan mood gelap, material dan pencahayaan atmosferik. |
| `/science-fiction` | Elemen futuristik dengan teknologi/lingkungan yang spesifik. |
| `/surreal` | Logika mimpi atau kombinasi tak lazim dengan focal point tetap jelas. |

---

### Animation look library

Pilih **satu** gaya animasi utama; tambah `/animated` bila membantu, lalu terangkan ciri gambar diamnya. Nama di bawah adalah kosakata prompt, bukan jaminan bahwa ImageFlow memiliki preset UI yang sama.

| Modifier | Tampilan yang dimaksud |
|---|---|
| `/animation:2d` | Ilustrasi animasi dua dimensi; tentukan garis, shading, dan detail latar. |
| `/animation:hand-drawn` | Garis buatan tangan yang sedikit organik, bukan garis vektor sempurna. |
| `/animation:cel` | Bidang warna dan bayangan cel-shaded yang bersih. |
| `/animation:anime` | Anime-inspired; pilih desain karakter, ekspresi, dan background tanpa menyebut studio/artist tertentu. |
| `/animation:chibi` | Proporsi kepala besar/tubuh kecil dan ekspresi imut. |
| `/animation:limited` | Bentuk dan shading sederhana, terasa seperti animasi dengan jumlah detail terbatas. |
| `/animation:western-cartoon` | Siluet ekspresif, ekspresi kuat, bentuk kartun; hindari meniru karakter terkenal. |
| `/animation:storybook` | Karakter dan background seperti ilustrasi buku cerita. |
| `/animation:cutout` | Bentuk seperti potongan kertas/kolase berlapis. |
| `/animation:puppet` | Karakter terasa seperti boneka/puppet dengan material kain/kayu sesuai brief. |
| `/animation:stop-motion` | Frame diam dengan pose dan tekstur stop-motion yang terasa buatan tangan. |
| `/animation:claymation` | Figur clay dengan sidik bentuk dan tekstur plastisin. |
| `/animation:3d-stylized` | Model 3D bergaya, bukan foto realistis; bentuk dan shader disederhanakan. |
| `/animation:3d-photoreal` | Render 3D yang mengejar material/cahaya fotorealistis; tetap merupakan render. |
| `/animation:toon-shaded` | Geometri 3D dengan warna/shading grafis seperti kartun. |
| `/animation:rotoscope` | Tampilan ilustrasi yang mengikuti proporsi/gerak realistis; sebut apakah garis/sketsa terlihat. |
| `/animation:motion-graphics` | Bentuk grafis, tipografi, dan geometri abstrak seperti frame motion design. |
| `/animation:pixel` | Karakter/scene pixel-art; tentukan ukuran pixel dan batas palet bila penting. |
| `/animation:vector` | Bentuk bersih, outline konsisten, bidang warna rata. |
| `/animation:watercolor` | Frame animasi dengan pigmen cat air dan tekstur kertas. |
| `/animation:line-art` | Frame dominan garis, shading minimal. |

**Gaya preset video yang tercantum pada panduan Adobe** mencakup 2D, 3D, Anime, Black and white, Cinematic, Claymation, Fantasy, Line art, Stopmotion, dan Vector art. Daftar itu menjadi kosakata inspirasi; ia tidak menyatakan bahwa Flow/ImageFlow punya preset video yang sama atau bahwa gambar diam otomatis menjadi video.

### Keluarga tipe logo

Modifier tipe logo menjelaskan **struktur mark**, bukan sekadar mood visual. Pilih satu tipe utama sebelum menambah estetika.

| Modifier | Bentuk dan penggunaan |
|---|---|
| `/logo` | Minta konsep logo orisinal secara umum; lanjutkan dengan tipe dan brief brand. |
| `/logo:wordmark` | Nama brand sebagai elemen utama dengan perlakuan tipografi khas. |
| `/logo:lettermark` | Singkatan/inisial beberapa huruf; cocok bila nama panjang atau sudah dikenal. |
| `/logo:letterform` | Satu huruf sebagai simbol utama. |
| `/logo:monogram` | Inisial yang dirangkai/ditumpuk secara khas; pastikan tetap terbaca. |
| `/logo:pictorial` | Simbol gambar konkret yang merepresentasikan brand. |
| `/logo:abstract` | Bentuk nonliteral yang punya satu metafora/karakter pembeda. |
| `/logo:combination` | Simbol + nama brand dalam satu sistem/lockup; biasanya fleksibel untuk brand baru. |
| `/logo:emblem` | Nama/simbol menyatu di dalam badge, crest, seal, atau bentuk tertutup. |
| `/logo:mascot` | Karakter/mascot menjadi identitas; tentukan siluet dan ekspresi agar tetap terbaca kecil. |
| `/logo:badge` | Mark bergaya lencana; perhatikan detail agar tidak terlalu padat. |
| `/logo:seal` | Seal/stamp formal atau heritage; gunakan teks melingkar hanya jika perlu dan ejaan diverifikasi. |

### Memilih tipe logo yang tepat

| Jika kebutuhan utama… | Mulai dari… | Catatan |
|---|---|---|
| Nama brand pendek dan mudah diingat | `/logo:wordmark` | Biarkan tipografi membangun recognition; pastikan terbaca kecil. |
| Nama panjang atau bentuk singkatan sudah dikenal | `/logo:lettermark` atau `/logo:monogram` | Periksa apakah inisial unik dan tidak membingungkan. |
| Brand masih baru dan nama perlu dikenalkan bersama simbol | `/logo:combination` | Buat versi simbol+wordmark dan versi simbol saja untuk aplikasi kecil. |
| Ada objek/metafora sederhana yang khas | `/logo:pictorial` | Jaga siluet unik, jangan memakai ikon stok yang terlalu umum. |
| Ingin simbol nonliteral yang bisa membawa makna brand | `/logo:abstract` | Sertakan satu metafora/brand attribute, bukan bentuk acak. |
| Brand butuh karakter ramah dan mudah diingat | `/logo:mascot` | Sederhanakan fitur wajah/pose agar tetap terbaca sebagai mark kecil. |
| Kesan institusi, klub, komunitas, atau heritage | `/logo:emblem` atau `/logo:badge` | Batasi detail dan teks kecil; uji versi tanpa tagline. |
| Identitas utama dipakai pada app/avatar | `/logo:letterform`, `/logo:pictorial`, atau `/logo:abstract` + `/logo:icon-only` | Utamakan siluet, negative space, dan bentuk yang jelas di ukuran mini. |

### Estetika logo dan modifier teknis-konseptual

| Modifier | Interpretasi default |
|---|---|
| `/logo:minimal` | Unsur sesedikit mungkin, satu gagasan visual dominan. |
| `/logo:geometric` | Bentuk sederhana berbasis geometri dan proporsi yang konsisten. |
| `/logo:organic` | Bentuk natural/organik, kurva dan siluet lebih hidup. |
| `/logo:playful` | Ramah, ekspresif, dan approachable; tetap jaga keterbacaan. |
| `/logo:premium` | Rapi, terukur, material/typography terasa refined; hindari ornamen klise. |
| `/logo:luxury` | Minimal, detail terkontrol, tipografi berkarakter; jangan otomatis pakai mahkota/emas. |
| `/logo:tech` | Geometri/struktur modern; jangan otomatis menambah circuit/gradient. |
| `/logo:heritage` | Kesan mapan/tradisional; gunakan simbol dan ornament seperlunya. |
| `/logo:retro` | Referensi era lampau yang disebutkan; tentukan periodenya atau beri petunjuk bentuk/palet. |
| `/logo:handcrafted` | Kesan custom/handmade dengan sedikit ketidaksempurnaan terarah. |
| `/logo:modernist` | Bentuk dan tipografi terstruktur, minim dekorasi. |
| `/logo:flat` | Warna solid tanpa render/mockup 3D. |
| `/logo:line-art` | Logo berbasis outline; cek ketebalan garis pada ukuran kecil. |
| `/logo:one-color` | Satu warna saja agar mark diuji tanpa bergantung pada gradasi. |
| `/logo:icon-only` | Hanya simbol; jangan masukkan nama/tagline. |
| `/logo:horizontal-lockup` | Simbol dan wordmark dalam susunan horizontal. |
| `/logo:stacked-lockup` | Simbol di atas/bawah wordmark dalam susunan bertumpuk. |
| `/logo:no-mockup` | Tampilkan artwork logo datar, bukan di kartu, gedung, kemasan, atau signage mockup. |
| `/logo:transparent-background` | Minta alpha/transparansi hanya jika output mode mendukung; verifikasi file hasil. |
| `/brand-name:"NAMA PERSIS"` | Salin nama brand persis; perlakukan sebagai copy wajib dan verifikasi huruf per huruf. |
| `/tagline:"COPY PERSIS"` | Tagline persis; gunakan hanya jika diminta dan model dapat merender teks dengan benar. |
| `/logo-palette:<warna>` | Palet brand, mis. `/logo-palette:navy-cream` atau kode warna eksplisit. |
| `/logo-use:<konteks>` | Konteks penggunaan, mis. `/logo-use:app-icon`, `/logo-use:packaging`, atau `/logo-use:social-avatar`. |

### Arah tipografi

Gunakan istilah ini sebagai karakter huruf, bukan pemilihan file font yang pasti. Untuk nama brand, selalu cek lagi hasil ejaan dan keterbacaan.

| Modifier | Karakter huruf |
|---|---|
| `/type:serif` | Serif klasik/editorial; tentukan kontras stroke dan mood. |
| `/type:sans-serif` | Sans-serif bersih dan fleksibel. |
| `/type:geometric-sans` | Bentuk huruf geometris, modern dan terstruktur. |
| `/type:humanist-sans` | Sans yang lebih hangat/natural, dengan ritme huruf organik. |
| `/type:grotesk` | Sans yang netral-kuat dengan bentuk tegas. |
| `/type:slab-serif` | Serif berujung tebal, kuat dan kokoh. |
| `/type:monospaced` | Lebar huruf seragam, nuansa teknis/terminal. |
| `/type:script` | Huruf sambung/calligraphic; jaga keterbacaan. |
| `/type:hand-lettered` | Huruf terasa digambar khusus; jangan mengubah ejaan. |
| `/type:rounded` | Sudut huruf lembut, ramah dan playful. |
| `/type:condensed` | Proporsi huruf sempit untuk headline/ruang terbatas. |
| `/type:display` | Huruf ekspresif untuk headline/logo, bukan paragraf panjang. |

### Jika logo akan dianimasikan

Token berikut adalah arahan konsep gerak. Dalam mode Image, gunakan untuk membuat keyframe atau storyboard saja; gunakan mode video yang benar untuk meminta klip bergerak.

| Modifier | Ide gerak |
|---|---|
| `/logo-motion:draw-on` | Garis/simbol tergambar bertahap. |
| `/logo-motion:reveal` | Logo muncul dari mask/cahaya/ruang kosong. |
| `/logo-motion:assemble` | Bagian-bagian menyatu menjadi mark. |
| `/logo-motion:morph` | Bentuk bertransformasi dengan transisi yang tetap terbaca. |
| `/logo-motion:kinetic-type` | Wordmark/huruf bergerak secara tipografis. |
| `/logo-motion:pulse` | Gerak ritmis halus tanpa mengubah identitas mark. |
| `/logo-motion:loop` | Gerakan berulang mulus dengan awal/akhir yang serasi. |
| `/logo-motion:particle` | Elemen/partikel berkumpul menjadi logo; hindari jika marka harus sangat sederhana. |

**Catatan logo:** konsep yang dihasilkan ImageFlow adalah gambar raster kecuali ada format vektor yang benar-benar dihasilkan/diubah melalui alat lain. Jangan menyebutnya SVG/vector-ready tanpa file yang dapat diverifikasi. Uji logo dalam satu warna, pada latar terang/gelap, dan pada ukuran kecil; AI image generator dapat salah mengeja teks atau membuat detail terlalu rumit.

---

## 4. Modifier fokus, blur, dan ketajaman

| Modifier | Interpretasi default |
|---|---|
| `/blur` | **Background blur / shallow depth of field**: subjek utama tajam, latar melembut. Ini arti default agar tidak membuat seluruh gambar kabur. |
| `/blur:background` | Latar belakang blur secara eksplisit; subjek utama tetap fokus. |
| `/blur:all` | Seluruh frame tampak lembut/tidak fokus. Pakai hanya jika memang diminta. |
| `/bokeh` | Blur latar dengan lingkaran cahaya/defocused light yang terlihat, terutama pada lampu. |
| `/soft-focus` | Fokus lembut dan atmosferik; detail tetap cukup terbaca, bukan gambar rusak/kabur total. |
| `/motion-blur` | Blur arah/jejak gerak pada objek atau kamera dalam **satu gambar diam**. Tentukan apa yang bergerak; jangan mengaburkan seluruh subjek tanpa alasan. |
| `/long-exposure` | Efek eksposur panjang pada cahaya/gerakan, seperti jejak lampu atau air halus. Gambar tetap satu frame. |
| `/sharp` | Focal subject tajam dengan tepi/detail yang jelas; tidak harus menambah detail berlebihan di seluruh latar. |
| `/deep-focus` | Subjek dekat dan latar sama-sama relatif terbaca/tajam. |
| `/macro` | Tampilan sangat dekat pada detail kecil/material; sebut objek/detail yang menjadi fokus. |

**Pengunci default `/blur`:** jangan blur wajah, logo, produk utama, teks wajib, atau tangan/objek yang sedang didemonstrasikan. Jika beberapa area perlu fokus, sebutkan prioritas fokusnya.

---

## 5. Kamera, framing, dan sudut

| Modifier | Interpretasi default |
|---|---|
| `/close-up` | Fokus pada wajah atau detail utama; latar hanya konteks. |
| `/portrait` | Framing potret subjek; bukan rasio kanvas tertentu kecuali ditentukan dengan `/ratio`. |
| `/medium-shot` | Subjek terlihat cukup dekat dengan sebagian lingkungan. |
| `/wide-shot` | Subjek dan lingkungan sama-sama terlihat; bukan otomatis rasio lebar. |
| `/wide-angle` | Perspektif lensa lebar dengan lebih banyak lingkungan dan distorsi perspektif yang terkendali. |
| `/top-down` | Kamera tepat/nyaris tegak lurus dari atas, cocok untuk flat lay. |
| `/overhead` | Sudut dari atas; tidak harus benar-benar 90 derajat. |
| `/low-angle` | Kamera lebih rendah mengarah ke atas; memberi kesan kuat/monumental. |
| `/high-angle` | Kamera melihat subjek dari atas. |
| `/eye-level` | Kamera setinggi mata subjek. |
| `/side-profile` | Tampak samping/profil. |
| `/three-quarter-view` | Sudut 3/4 untuk menunjukkan sisi depan dan samping objek. |
| `/centered` | Subjek utama di tengah; sisakan margin sesuai pemakaian. |
| `/rule-of-thirds` | Subjek atau focal point mengikuti pembagian sepertiga. |
| `/symmetrical` | Keseimbangan komposisi kiri-kanan/atas-bawah yang teratur. |
| `/dynamic-composition` | Garis dan pose diagonal memberi energi; tetap jaga subjek utama terbaca. |
| `/negative-space` | Sisakan ruang kosong pada sisi/area yang disebutkan, terutama untuk teks/layout. |
| `/flat-lay` | Objek disusun pada permukaan dan difoto dari atas. |

Nilai lensa opsional: `/lens:35mm`, `/lens:50mm`, `/lens:85mm`, `/lens:macro`. Angka lensa adalah petunjuk estetika, bukan jaminan metadata kamera atau kontrol teknis di ImageFlow.

---

## 6. Modifier pencahayaan

| Modifier | Interpretasi default |
|---|---|
| `/soft-light` | Cahaya lembut dengan bayangan bertahap. |
| `/hard-light` | Cahaya terarah dengan bayangan tegas dan kontras lebih tinggi. |
| `/studio-light` | Pencahayaan produk/portrait terkontrol seperti studio. |
| `/golden-hour` | Cahaya hangat rendah seperti matahari pagi/sore. |
| `/backlight` | Cahaya dari belakang subjek; jelaskan apakah perlu rim/glow. |
| `/rim-light` | Garis cahaya di tepi subjek untuk memisahkan dari latar. |
| `/dramatic-light` | Perbedaan terang-gelap yang kuat dan mood sinematik. |
| `/low-key` | Frame dominan gelap dengan area terang terpilih; tetap jaga detail penting. |
| `/high-key` | Frame terang, bersih, bayangan ringan. |
| `/neon-light` | Cahaya neon berwarna; tentukan warna sumber agar tidak acak. |
| `/window-light` | Cahaya natural dari jendela, lembut/terarah sesuai brief. |
| `/volumetric-light` | Berkas cahaya tampak di udara berkabut/debu; gunakan seperlunya. |

---

## 7. Modifier warna, tekstur, dan mood

### Palet warna / color grade

| Modifier | Interpretasi default |
|---|---|
| `/warm` | Dominan warna hangat; sebut warna spesifik bila brand/palette penting. |
| `/cool` | Dominan warna dingin seperti biru/teal; jaga warna kulit/produk tetap wajar. |
| `/pastel` | Saturasi lembut dan nilai warna terang. |
| `/vibrant` | Warna hidup dan jelas tanpa membuat semua elemen saling bersaing. |
| `/muted` | Saturasi rendah, lebih tenang/halus. |
| `/monochrome` | Satu keluarga warna atau hitam-putih; jika perlu tentukan yang mana. |
| `/teal-orange` | Kontras teal/biru-hijau dan amber/oranye; jangan diterapkan pada elemen brand yang harus akurat. |
| `/palette:<nama/hex>` | Palet tertentu, mis. `/palette:terracotta-cream` atau `/palette:#D96B42,#F4E7D3`. |
| `/color-grade:<look>` | Arah grading warna, mis. `/color-grade:filmic`, `/color-grade:bleach-bypass`; tulis deskripsi visual bila nama look ambigu. |

### Tekstur dan finishing

| Modifier | Interpretasi default |
|---|---|
| `/film-grain` | Grain halus seperti film; jangan sampai menutupi detail. |
| `/clean` | Tampilan bersih, minim noise, tanpa elemen dekoratif tak perlu. |
| `/matte` | Pantulan rendah, permukaan lembut/matte. |
| `/glossy` | Highlight/pantulan lebih jelas, cocok untuk produk tertentu. |
| `/paper-texture` | Serat/tekstur kertas yang terlihat halus. |
| `/high-detail` | Tambahkan detail pada subjek utama yang relevan; bukan menambahkan ornamen acak. |
| `/subtle-grain` | Grain sangat halus sebagai finishing. |

### Mood

Boleh gunakan `/mood:<kata>`, misalnya `/mood:tenang`, `/mood:optimistis`, `/mood:misterius`, `/mood:playful`, `/mood:premium`, atau `/mood:nostalgic`.

---

## 8. Layout, rasio, dan elemen teks

| Modifier | Interpretasi default |
|---|---|
| `/ratio:1:1` | Kanvas persegi. |
| `/ratio:4:5` | Potret feed sosial. |
| `/ratio:9:16` | Vertikal penuh untuk Story/Reels/TikTok. |
| `/ratio:16:9` | Horizontal/widescreen. |
| `/ratio:3:2` | Lanskap fotografi umum. |
| `/poster` | Hierarki visual poster; masukkan teks hanya bila pengguna memberi/meminta copy. |
| `/thumbnail` | Subjek besar, kontras terbaca pada ukuran kecil, safe margins. |
| `/cover` | Focal point dan ruang layout disesuaikan sebagai cover. |
| `/text:<copy>` | Teks persis yang diminta; jaga ejaan, kapitalisasi, dan tanda baca. Teks gambar sering perlu pemeriksaan khusus. |
| `/no-text` | Jangan tambahkan tulisan apa pun, termasuk huruf dekoratif. |
| `/no-logo` | Hindari logo/brand mark yang tidak diminta. |
| `/no-watermark` | Jangan tambahkan watermark buatan. |
| `/keep:<detail>` | Pertahankan detail wajib secara eksplisit, mis. warna baju, bentuk botol, atau posisi subjek; bukan jaminan pixel-perfect. |
| `/avoid:<detail>` | Nyatakan elemen yang harus dihindari dalam prompt natural; ini bukan jaminan adanya negative-prompt control terpisah. |
| `/background:<deskripsi>` | Tetapkan latar secara eksplisit. |
| `/transparent-background` | Minta tampilan latar transparan; cek apakah mode/output saat ini benar-benar mendukung alpha channel. Jangan mengklaim transparan jika hasilnya hanya putih/berkotak. |

**Rasio adalah pilihan output/canvas bila tersedia di UI**, bukan sekadar gaya bahasa. Cocokkan prompt dengan setting Flow sebelum generation; jangan menganggap `/ratio` mengubah setting antarmuka secara otomatis.

### Jenis output / penggunaan

| Modifier | Prioritas komposisi |
|---|---|
| `/avatar` | Siluet dan wajah/mark terbaca kecil, centered, safe margins. |
| `/profile-picture` | Subjek tunggal, komposisi sederhana; cek rasio 1:1 dan crop lingkaran bila platform memakainya. |
| `/social-post` | Fokus utama kuat dan ruang copy disesuaikan platform. |
| `/thumbnail` | Subjek besar, kontras dan focal point jelas pada layar kecil. |
| `/poster` | Hierarki headline/visual; jangan membuat copy tambahan yang tidak diberikan. |
| `/book-cover` | Area judul/author disiapkan; tentukan genre dan focal image. |
| `/album-cover` | Mood/visual concept kuat dan square crop bila sesuai. |
| `/packaging` | Tampilkan konsep kemasan; bedakan render mockup dari artwork flat untuk cetak. |
| `/sticker` | Bentuk sederhana, outline jelas, subjek terpisah dari latar. |
| `/app-icon` | Satu simbol kuat, detail minim, aman di sudut membulat. |
| `/mascot` | Satu karakter konsisten sebagai maskot ilustrasi; gunakan `/logo:mascot` jika karakter harus menjadi logo. |
| `/infographic` | Informasi ringkas, grid dan label terbaca; masukkan copy terpisah dan verifikasi teks. |
| `/diagram` | Hubungan dan label jelas; jangan menambah elemen ilustratif yang mengaburkan logika. |
| `/character-sheet` | Konsistensi karakter dari beberapa tampak/pose; tentukan jumlah views dan background polos. |
| `/concept-art` | Eksplorasi lingkungan, material, dan bentuk; bukan otomatis final art. |
| `/storyboard` | Frame naratif dengan aksi dan arah kamera; satu prompt harus menyebut jumlah panel. |
| `/pattern` | Motif berulang dan seam/tileability bila memang diperlukan. |
| `/wallpaper` | Komposisi luas dengan ruang ikon/teks sesuai perangkat. |
| `/banner` | Subjek/teks ditempatkan mengikuti safe area dan rasio banner. |
| `/mockup` | Adegan menampilkan penerapan desain; jangan pakai untuk output logo flat kecuali diminta. |

---

## 9. Batas gambar diam vs animasi/video

- `/animated` berarti **gaya visual animasi pada satu gambar diam**.
- `/motion-blur`, `/long-exposure`, dan pose melompat/berlari adalah efek/aksi yang direpresentasikan dalam satu frame, bukan video.
- Jika pengguna meminta klip bergerak, gerak kamera (`/camera-move:pan`, `/camera-move:zoom-in`) atau rangkaian waktu, cek bahwa mode video memang tersedia dan alihkan ke workflow video yang sesuai. Jangan menjanjikan video dari mode Image.
- Pada prompt video, jelaskan urutan waktu sederhana: siapa/subjek, melakukan apa, di mana, kamera bergerak bagaimana, estetika dan mood. Hindari banyak aksi berturut-turut jika satu klip pendek harus tetap koheren.

**Prompt animasi sebagai gambar diam:** tulis gaya animasi (`/animation:...`) dan ciri frame: bentuk, outline, shading, material, karakter, ekspresi, background, serta palet.  
**Prompt untuk video animasi:** tambahkan aksi dalam urutan waktu sederhana, arah/kecepatan gerak, camera movement, durasi/continuity bila tersedia, dan kunci desain karakter/background. Gunakan tool/mode video yang benar; token slash tidak mengubah mode generation.

| Modifier video | Arah kamera |
|---|---|
| `/camera-move:static` | Kamera terkunci, tanpa gerakan. |
| `/camera-move:pan` | Kamera berputar horizontal. |
| `/camera-move:tilt` | Kamera bergerak vertikal. |
| `/camera-move:zoom-in` | Framing semakin rapat; bedakan zoom optik dan dolly bila penting. |
| `/camera-move:zoom-out` | Framing melebar untuk mengungkap konteks. |
| `/camera-move:dolly-in` | Kamera maju secara fisik menuju subjek. |
| `/camera-move:tracking` | Kamera mengikuti subjek bergerak. |
| `/camera-move:orbit` | Kamera mengitari subjek; tentukan arah dan jarak. |
| `/camera-move:handheld` | Gerak kamera natural sedikit tidak stabil; hindari jika butuh tripod-clean look. |

---

## 10. Preset kombinasi

Preset hanyalah jalan pintas; selalu cocokkan dengan subjek dan tujuan.

### `/cinematic`

Padanan awal: `/dramatic-light /dynamic-composition /color-grade:filmic` ditambah deskripsi shot yang sesuai. Jangan otomatis menambahkan kabut, lens flare, gelap, atau letterbox.

### `/blur`

Padanan awal: `/blur:background /sharp`; gunakan `/bokeh` hanya jika cahaya latar mendukung.

### `/realistic`

Padanan awal: foto natural, cahaya/material realistis, proporsi konsisten, detail utama jelas. Hindari memasukkan istilah ilustrasi/flat-vector kecuali diminta sebagai hybrid.

### `/animated`

Padanan awal: tentukan `/2d` atau `/3d`, garis/material, tingkat detail, palet, dan ekspresi. Jangan menganggap `/animated` berarti anime secara otomatis.

### `/product-premium`

Padanan awal: `/product-photo /studio-light /clean /sharp`, latar sederhana, pantulan dan bayangan terkontrol.

### `/portrait-editorial`

Padanan awal: `/portrait /editorial /soft-light`, ekspresi dan framing jelas, latar mendukung subjek.

---

## 11. Contoh penerjemahan prompt

### A. `/cinematic /realistic /blur`

**Brief pengguna:** “Buat foto seorang barista menuang kopi, cinematic, realistic, blur.”

**Interpretasi:** `/blur` = latar lembut, barista dan aliran kopi tetap fokus. Jangan menambahkan teks/logo bila tidak diminta.

**Prompt final contoh:**

> Modifiers: `/cinematic /realistic /blur:background /warm`. Foto editorial sinematik realistis seorang barista menuang kopi dari kettle leher-angsa ke cangkir keramik di coffee bar kayu saat pagi. Medium close-up dari sudut 3/4, tangan dan aliran kopi menjadi fokus tajam; latar belakang coffee bar lembut blur dengan bokeh hangat yang halus. Cahaya jendela keemasan dari samping, bayangan natural, palet terracotta dan cream, suasana tenang dan premium. Komposisi vertikal dengan ruang kosong di bagian atas, tanpa teks dan tanpa logo.

### B. Gambar bergaya animasi

**Brief pengguna:** “Maskot rubah sedang membaca buku, `/animated /2d /pastel`.”

**Prompt final contoh:**

> Modifiers: `/animated /2d /pastel`. Ilustrasi diam bergaya animasi 2D tentang maskot rubah kecil yang duduk membaca buku di sudut perpustakaan. Siluet bersih, ekspresi penasaran dan hangat, bentuk sederhana dengan shading cel yang lembut. Palet pastel peach, sage, dan cream; cahaya jendela pagi; latar rapi dengan detail secukupnya. Subjek berada di tengah dengan safe margins, tanpa teks.

### C. `/motion-blur` tanpa mengaburkan subjek

**Brief pengguna:** “Mobil balap malam hari, `/realistic /motion-blur /neon`.”

**Prompt final contoh:**

> Modifiers: `/realistic /motion-blur /neon-light`. Foto otomotif realistis sebuah mobil balap melaju di jalan kota malam. Mobil tetap relatif tajam dan terbaca, sementara lampu kota dan garis jalan membentuk motion blur horizontal yang terarah. Pantulan neon magenta dan cyan pada bodi, kamera rendah 3/4, suasana energik, komposisi dinamis, tanpa tulisan atau logo yang tidak diminta.

### D. Poster dengan ruang untuk copy

**Brief pengguna:** “Poster konser jazz, `/cinematic /negative-space /ratio:4:5`.”

**Prompt final contoh:**

> Modifiers: `/cinematic /negative-space /ratio:4:5`. Poster konser jazz bernuansa sinematik: seorang pemain saksofon dalam siluet di panggung kecil, satu spotlight amber menembus suasana smoky yang tipis. Komposisi vertikal 4:5, subjek berada di sisi kanan, ruang kosong gelap yang bersih pada sisi kiri untuk teks yang akan ditambahkan kemudian. Palet hitam, brass, dan amber; pencahayaan dramatis namun detail alat musik masih terbaca. Jangan membuat teks, logo, atau watermark.

### E. Konsep logo orisinal

**Brief pengguna:** “Buat logo untuk brand kopi NusaKarya, `/logo:combination /logo:minimal /logo:geometric`.”

**Prompt final contoh:**

> Modifiers: `/logo:combination /logo:minimal /logo:geometric /logo:one-color /logo:no-mockup /ratio:1:1 /brand-name:"NusaKarya"`. Buat konsep logo orisinal untuk brand kopi NusaKarya: simbol abstrak sederhana yang menggabungkan biji kopi dan matahari terbit, dipasangkan dengan wordmark “NusaKarya” menggunakan tipografi sans-serif yang hangat dan mudah dibaca. Gunakan satu warna dark espresso di atas latar putih polos; bentuk vektor datar, siluet bersih, jarak antar elemen rapi, tetap terbaca pada ukuran ikon kecil. Tampilkan artwork logo saja, tanpa kemasan, kartu nama, signage, mockup, tagline, watermark, atau ornamen tambahan. Pastikan ejaan brand persis “NusaKarya”; periksa hasil teks sebelum digunakan.

### F. Karakter bergaya animasi 3D

**Brief pengguna:** “Buat maskot beruang selfie, `/animation:3d-stylized /pastel`.”

**Prompt final contoh:**

> Modifiers: `/mascot /animation:3d-stylized /pastel /soft-light /ratio:1:1`. Satu maskot beruang krem bergaya animasi 3D stylized sedang mengambil selfie dengan satu tangan dan menunjukkan peace sign dengan tangan lain. Ekspresi ramah dan percaya diri, hoodie terracotta polos, wajah dan proporsi konsisten, mata dan tangan terbentuk rapi. Render seperti figur koleksi matte dengan bentuk sederhana dan pencahayaan lembut; palet cream, terracotta, dan blush. Background bersih dengan safe margins; satu karakter saja, tanpa tulisan, logo, atau objek tambahan.

### G. Foto produk e-commerce

**Brief pengguna:** “Foto botol skincare minimalis, `/realistic /studio-light /blur`.”

**Prompt final contoh:**

> Modifiers: `/product-photo /realistic /studio-light /blur:background /clean /ratio:4:5`. Foto produk realistis sebuah botol skincare kaca frosted berwarna putih susu dengan tutup metalik sederhana, berdiri tegak di atas pedestal batu krem. Label tetap polos tanpa tulisan baru. Botol tajam dan menjadi satu-satunya hero subject; background studio beige lembut blur. Soft key light dari kiri, rim light tipis di kanan, bayangan kontak natural, pantulan kaca terkendali, komposisi vertikal dan ruang kosong di atas untuk layout. Tanpa logo, watermark, props tambahan, atau produk kedua.

---

## 12. Alur kerja Leo sebelum membuat gambar

Sebelum bertanya atau merencanakan prompt untuk setiap permintaan gambar, **baca file panduan ini dari disk terlebih dahulu**. Setelah itu, klarifikasi brief desain; slash modifier membantu menerjemahkan gaya, tetapi **tidak menggantikan brief desain**. Pastikan hal berikut sudah jelas:

1. Tujuan dan platform penggunaan.
2. Subjek/karakter dan identitas/reference image yang benar.
3. Style/medium: realistis, 2D, 3D, ilustrasi, dan sebagainya.
4. Pose/aksi serta properti wajib.
5. Palet warna dan background.
6. Komposisi, ruang untuk copy, dan rasio/aspect ratio.
7. Teks persis yang harus terlihat atau konfirmasi tanpa teks.
8. Jumlah konsep/hasil yang diminta.
9. Modifier yang bertentangan atau berpotensi mengubah brief.
10. **Jika logo:** nama brand dan ejaan persis, tujuan/audience, satu ide/metafora visual, tipe logo, karakter brand, palet, arah tipografi, versi icon-only/wordmark/lockup yang diperlukan, dan apakah output yang diminta konsep raster atau file vector melalui proses lanjutan.

Ringkas brief final dan tunggu persetujuan pengguna sebelum menjalankan generation yang memakai kuota. Setelah disetujui, susun payload prompt ImageFlow dengan baris literal `Modifiers: /...` yang memuat setidaknya satu modifier relevan, diikuti deskripsi natural yang menjelaskan maksudnya. Pertahankan token `/` tersebut saat mengirim prompt. Lalu ikuti workflow ImageFlow yang berlaku, cocokkan setting UI dengan rasio/jumlah output yang diminta, unduh, verifikasi, dan tinjau visual hasil sebelum menyebutnya selesai.

Jangan mengklaim modifier sebagai setting teknis yang sudah diterapkan jika hanya dimasukkan sebagai kata prompt. Jika Flow menyediakan kontrol UI khusus (mis. ratio, reference, atau output count), gunakan dan verifikasi kontrol tersebut secara terpisah.

---

## 13. Batasan dan praktik baik

- Pertahankan jumlah subjek utama tetap sedikit dan identitasnya konsisten.
- Beri ruang aman untuk subjek, wajah, tangan, teks, dan logo penting; sebutkan safe margin bila gambar dipakai sebagai avatar/thumbnail.
- Untuk teks di dalam gambar, salin copy persis dan minta pengguna menyetujui bila hasil ejaan sangat penting; verifikasi ulang hasil visual.
- Gunakan referensi untuk mengarahkan ciri umum, komposisi, atau konsistensi karakter sesuai brief; jangan menganggap referensi mengizinkan perubahan identitas yang tidak diminta.
- Untuk permintaan “seperti karya seniman X”, arahkan ke ciri visual umum (mis. palet, medium, era, garis, pencahayaan), bukan menyalin persis karya atau gaya kreator hidup.
- Untuk `/realistic`, hindari anatomi rusak, objek melayang, pantulan yang tidak masuk akal, tekstur plastik yang tidak diminta, dan detail latar yang mengganggu.
- Untuk `/animated`, periksa konsistensi bentuk, mata, anggota tubuh, garis, dan bayangan; jangan biarkan gaya berubah menjadi render realistis tanpa persetujuan.
- Untuk logo, prioritaskan satu simbol/ide pembeda, bentuk sederhana, keterbacaan nama, ruang kosong, dan kemampuan terbaca kecil; periksa versi satu warna serta latar terang/gelap.
- Jangan menyatakan logo siap produksi, dapat diskalakan tanpa batas, atau memiliki alpha/vector layer sebelum format output benar-benar diperiksa. Bila teks harus persis, lakukan proofread visual karakter per karakter.
- Hindari simbol, lockup, atau tipografi yang terlalu mirip brand yang sudah ada. Gunakan moodboard/karakteristik umum untuk referensi, lalu kembangkan bentuk orisinal.
- Untuk `/blur`, periksa bahwa titik fokus tetap tajam. Jika seluruh hasil kabur, koreksi prompt dengan menamai subjek sebagai “tack-sharp focal subject” dan memindahkan blur hanya ke latar.
- Bila prompt terlalu panjang, hapus pengulangan dan pertahankan brief, hierarki fokus, style utama, cahaya, komposisi, dan batasan penting.
- Model berbeda dapat menafsirkan istilah dengan cara berbeda. Lakukan iterasi terarah: ubah satu atau dua aspek per percobaan, bukan menumpuk banyak koreksi sekaligus.

---

## 14. Rujukan pendek

Kerangka prompt dalam dokumen ini mengambil praktik umum yang dijelaskan Adobe: tulis subjek dan detail secara spesifik; tambahkan framing, pencahayaan, palet, mood, dan estetika yang relevan. Panduan prompt video Adobe menganjurkan gaya visual dan aksi yang jelas, konteks/background, lighting/cinematography/color grade/mood, camera angle/movement, dan unsur waktu; istilah tersebut diadaptasi bila berguna untuk satu gambar diam. Ini inspirasi penulisan prompt, bukan klaim bahwa preset atau kontrol Adobe tersedia di ImageFlow/Google Flow. Hasil bisa berbeda antar model, jadi tinjau dan iterasi secara terarah.

- Adobe Firefly Help, **Writing effective text prompts** — prompt gambar harus deskriptif dan spesifik; evaluasi hasil lalu reword/iterasi bila belum sesuai (9 June 2026).
- Adobe Firefly Help, **Writing effective text prompts for video generation** — memerinci visual style, aksi, konteks, pencahayaan, cinematography, color grade, mood, camera angle/movement, dan temporal elements (9 June 2026). Istilah ini diadaptasi sebagai kosakata prompt, bukan kontrol ImageFlow.
- Adobe Firefly Help, **Use style presets for video generation** — preset khusus Firefly Video: 2D, 3D, Anime, Black and white, Cinematic, Claymation, Fantasy, Line art, Stopmotion, dan Vector art (last updated 18 August 2026). Ini bukan klaim preset gambar ImageFlow.
- Adobe Express, **How to design a logo: Everything you need to know (even if you’re a beginner)** — tipe logo, brand brief, variasi warna, black-and-white, ukuran kecil, dan konsistensi pemakaian (20 July 2026).
- Adobe Express, **Mastering logo design and creation: Designer insights, tips, and 2026 trends** — simplicity, memorability, legibility, dan adaptasi logo untuk ukuran kecil serta beragam media (11 August 2026).

Rujukan Adobe dipakai sebagai landasan praktik umum dan sumber istilah. Semua daftar slash di dokumen ini adalah kamus prompt internal Leo; bukan daftar resmi preset Adobe maupun klaim fitur ImageFlow.
