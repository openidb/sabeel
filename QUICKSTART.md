# Quick Start Guide - OpenITI to Kavita

## What We've Set Up

1. **Kavita** - Running on http://localhost:5001
   - Library volume mounted at `kavita/library/`
   - Timezone set to Asia/Riyadh

2. **OpenITI Pipeline** - Converts Arabic texts to EPUB
   - Located in `openiti-pipeline/`
   - Successfully tested on 3 sample books
   - Ready for full-scale conversion

## Test the Sample Books

### Step 1: Access Kavita
Open http://localhost:5001 in your browser

### Step 2: Add Library
1. Go to Settings → Libraries
2. Click "Add Library"
3. Set the path to: `/library`
4. Choose type: "Book" or "Mixed"
5. Click "Scan Library"

### Step 3: View the Books
You should see 3 test books:
- Ghurar Khasais (Abu Ishaq Watwat, 718 AH)
- Ajrumiyya (Ibn Ajrum, 723 AH)
- Lisan al-Arab (Ibn Manzur, 711 AH)

### Step 4: Test Reading
1. Click on a book to open it
2. Verify RTL (right-to-left) text display
3. Check Arabic characters render correctly
4. Test navigation and reading experience

## If Quality Looks Good - Scale Up!

### Full Conversion Pipeline

```bash
cd openiti-pipeline

# Clone the full RELEASE repository (warning: multi-GB download)
git clone https://github.com/OpenITI/RELEASE.git workspace/RELEASE

# Run the full conversion (this will take several hours)
source env/bin/activate
python scripts/batch_convert_all.py workspace/RELEASE output ../kavita/library/openiti
```

This will:
1. Scan RELEASE for all Shamela texts from 0025-1450 AH
2. Convert each to EPUB format
3. Organize by century and author in `kavita/library/openiti/`

### Expected Scale
- Estimated: ~3,760 Shamela texts total
- Unknown how many fall in 0025-1450 AH range
- Conversion time: ~30-120 seconds per book
- Total time: Several hours (mostly automated)

## Directory Structure After Full Conversion

```
kavita/library/openiti/
├── 0001-0100AH/
│   ├── AuthorName1/
│   │   └── book1.epub
│   └── AuthorName2/
│       └── book2.epub
├── 0101-0200AH/
│   └── ...
├── 0701-0800AH/
│   ├── IbnManzurIfriqi/
│   │   └── 0711IbnManzurIfriqi.LisanCarab.Shamela0001687-ara1.epub
│   ├── AbuIshaqWatwat/
│   │   └── 0718AbuIshaqWatwat.GhurarKhasais.Shamela0001349-ara1.epub
│   └── IbnAjrum/
│       └── 0723IbnAjrum.Ajrumiyya.Shamela0011371-ara1.epub
└── ...
```

## Troubleshooting

### Books Not Showing in Kavita
- Rescan the library: Settings → Libraries → Scan
- Check logs: `docker logs kavita`

### RTL Text Not Displaying Correctly
- CSS stylesheet issue - check `openiti-pipeline/scripts/arabic-rtl.css`
- Try different ebook reader in Kavita settings

### Conversion Errors
- Check Python environment: `source openiti-pipeline/env/bin/activate`
- Verify Pandoc: `pandoc --version`
- Check logs in conversion output

## Useful Commands

```bash
# Restart Kavita
docker compose restart

# View Kavita logs
docker logs kavita -f

# Test single book conversion
cd openiti-pipeline
source env/bin/activate
python scripts/convert_to_epub.py path/to/book.mARkdown output/

# Check conversion progress
ls -lh openiti-pipeline/output/*.epub | wc -l
```

## Current Status

✅ Kavita running and accessible
✅ 3 test books converted successfully
✅ Books ready to test in Kavita
⏳ Waiting for quality verification
⏳ Full repository download pending
⏳ Full conversion pending

## Next Steps

1. Test the 3 sample books in Kavita
2. Verify quality (RTL, fonts, readability)
3. If good → proceed with full conversion
4. If issues → adjust conversion script and re-test
